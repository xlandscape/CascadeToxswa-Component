# -*- coding: utf-8 -*-
import os, io, subprocess, pandas, re, shutil, datetime, numpy as np, util, time, datetime as dt
from Catchment import Reach
from functools import partial
import cython_util as cu


class Toxswa(object):
    """
    Class for TOXSWA model.
    Contains attributes and methods for running TOXSWA, preparing input and reading output.
    """

    # Name of TXW template file
    txwTemplateFile = "txw_template.txw"
    # Name of MFU template file
    mfuTemplateFile = "mfu_template.mfu"

    # Name of MFU template file
    mfsTemplateFile = "mfs_template.mfs"

    # Name of MFL template file
    mflTemplateFile = "mfl_template.mfl"
    
    allowedOutputVars = [
        "MasWatLay",
        "MasDwnWatLay",
        "MasDrfWatLay",
        "MasSedInWatLay",
        "MasSedOutWatLay",
        "MasTraWatLay",
        "MasVolWatLay",
        "MasSed",
        "MasTraSed",
        "ConLiqWatTgtAvg",
        "ConLiqWatTgtAvgHrAvg",
        "ConLiqWatTgtAvgHrMax",
        "CntSorSedTgt",
        "DepWat",
        "VelWatFlw",
        "QBou",
        "CntSorSedTgt",
        "VelWatFlw",
        "QBou",
        "CntSedTgt1",
        "MasDraWatLay",
        "MasRnfWatLay",
        "MasDwnWatLay",
        "MasUpsWatLay",
        "MasForWatLay",
        "MasVolWatLay",
    ]

    # Command to run TOXSWA
    runCommand = "run_TOXSWA.BAT"
    # Name of working directory
    workDirName = "work"

    # format string for parsing and printing TOXSWA time stamps
    dateTimeFormat = "%d-%b-%Y-%Hh%M"
    dateTimeFormatMfu = "%d-%b-%Y-%Hh%M-%S:%f"
    datTimeParseFcn = lambda x: datetime.datetime.strptime(x, Toxswa.dateTimeFormat)

    flagOk = 0
    flagError = 1
    flagSkipExist = 2
    flagSkipReach = 3
    flagMessage = {
        flagOk: "success",
        flagError: "error",
        flagSkipExist: "skipped: existing results found",
        flagSkipReach: "skipped: run not required",
    }

    hydrologyTimeStep = 3600

    def __init__(self, experimentDir, toxswaConfig, generalConfig, outputDir):
        """
        Creates toxswa object
        """
        self.inputDir = generalConfig["inputDir"]
        self.outputDir = outputDir
        self.workDir = os.path.join(experimentDir, self.workDirName)
        self.runToxswaCommand = os.path.join(toxswaConfig["toxswaDir"], self.runCommand)
        self.toxswaConfig = toxswaConfig
        self.generalConfig = generalConfig
        self.substanceNames = toxswaConfig["substanceNames"].replace(" ", "").split(",")
        self.defaultTimeStep = toxswaConfig.getfloat("timeStepDefault")
        self.outputVars = toxswaConfig["outputVars"].replace(" ", "").split(",")
        self.startTime = dt.datetime.strptime(
            self.generalConfig["startDateSim"], "%d-%b-%Y"
        )
        self.endTime = dt.datetime.strptime(
            self.generalConfig["endDateSim"], "%d-%b-%Y"
        ) + dt.timedelta(hours=23)
        self.scaleFacDrift = toxswaConfig.getfloat("scaleFacDrift", 1)
        self.HML_firstRow = None
        self.HML_nRow = None
        self.HML_skipRows = [1]
        self.keepOrigOutFiles = toxswaConfig["keepOrigOutFiles"].lower() == "true"
        self.deleteMfuFiles = toxswaConfig.getboolean("deleteMfuFiles", False)
        self.dummyOutTable = None
        if not "MasDwnWatLay" in self.outputVars:
            self.outputVars.append("MasDwnWatLay")
        if not os.path.exists(self.workDir):
            os.makedirs(self.workDir)

        # write meteorology file
        tempData = pandas.read_csv(
            os.path.join(self.inputDir, toxswaConfig["temperatureFile"]),
            header=[0, 1],
            parse_dates=[0],
            infer_datetime_format=True,
        )
        filter = (
            (tempData.Time >= self.startTime) & (tempData.Time <= self.endTime)
        ).iloc[:, 0]
        tempData = tempData.loc[filter, :]
        fmt = [lambda x: x.strftime("%d/%m/%Y"), lambda x: str(x)]
        util.writeOutputTable(
            os.path.join(self.workDir, "temperature.met"),
            tempData,
            fmt,
            inclColNames=False,
            headerLines=[
                "* Daily air temperature:",
                "*" + ",".join(tempData.columns.get_level_values(0)),
            ],
        )

    def init_reach(self, reach):
        """
        Initializes TOXSWA simulation for given reach.
        Writes input files that do not depend on upstream runs (TXW and HYD)
        TODO: precision for string conversion mass loading and waterbody properties should probably be explicitly specified
        """

        if reach.skip or (
            self.txw_exists(reach)
            and self.hyd_exists(reach)
            and self.mfs_exists(reach)
            and self.mfl_exists(reach)
        ):
            return

        hydrologyMassLoadingsTable = pandas.read_csv(
            os.path.join(
                self.generalConfig["inputDir"], reach.hydrologyMassLoadingsFile
            ),
            header=[0],
            parse_dates=[0],
            infer_datetime_format=True,
            skiprows=self.HML_skipRows,
        )
        if self.HML_nRow is None:
            filter = (hydrologyMassLoadingsTable.Time >= self.startTime) & (
                hydrologyMassLoadingsTable.Time <= self.endTime + dt.timedelta(hours=1)
            )
            hydrologyMassLoadingsTable = hydrologyMassLoadingsTable.loc[filter,]
            hydrologyMassLoadingsTable.reset_index(drop=True, inplace=True)
            self.HML_firstRow = filter.idxmax() + 2
            self.HML_nRow = filter.sum()
            self.HML_skipRows = lambda x: not (
                x == 0
                or (x >= self.HML_firstRow and (x <= self.HML_firstRow + self.HML_nRow))
            )

        lastRow = hydrologyMassLoadingsTable.iloc[-1,]
        if lastRow.Time.hour == 0:
            hydrologyMassLoadingsTable = hydrologyMassLoadingsTable.append(lastRow)
            hydrologyMassLoadingsTable.iloc[-1, 0] += dt.timedelta(hours=1)

        firstRow = hydrologyMassLoadingsTable.iloc[0,]
        if firstRow.Time.hour == 1:
            hydrologyMassLoadingsTable = pandas.concat(
                [
                    hydrologyMassLoadingsTable.loc[
                        [
                            0,
                        ]
                    ],
                    hydrologyMassLoadingsTable,
                ],
                ignore_index=True,
            )
            hydrologyMassLoadingsTable.iloc[0, 0] -= dt.timedelta(hours=1)

        if not self.txw_exists(reach):
            self.write_txwFile(reach, hydrologyMassLoadingsTable)

        if not self.hyd_exists(reach):
            self.write_hydFile(reach, hydrologyMassLoadingsTable)

        if not self.mfs_exists(reach):
            self.write_mfsFile(reach, hydrologyMassLoadingsTable)
       if not self.mfl_exists(reach):
            self.write_mflFile(reach, hydrologyMassLoadingsTable)

    # def read_mflfile()
    def write_mflFile(self, reach, hydrologyMassLoadingsTable):
        massFlowTimestepFcn = lambda row: self.reach_massFlowTimestep(
            reach, row["DepWat"], row["QBou"]
        )

        massFlowTimestepLength = hydrologyMassLoadingsTable.apply(
            massFlowTimestepFcn, axis=1
        )
        mflDateTimeColumn = hydrologyMassLoadingsTable.Time.apply(
            lambda x: x + datetime.timedelta(minutes=30)
        )

        mflTimestepColumnFcn = lambda x: (
            x - (mflDateTimeColumn.iloc[0] - dt.timedelta(hours=1))
        ).total_seconds() / (3600 * 24)
        mflTimestepColumn = mflDateTimeColumn.apply(mflTimestepColumnFcn)
        mflTable = pandas.concat(
            [mflTimestepColumn, mflDateTimeColumn, hydrologyMassLoadingsTable.LoaDra],
            axis=1,
        )
        mflTable.columns = ["timeStep", "dateTime", "LoaDra"]

        # Read MFL template file
        with open(
            os.path.join(self.toxswaConfig["toxswaDir"], self.mflTemplateFile), "r"
        ) as f:
            mflTempl = f.read()

        # Formatter to convert table to string to write to MFS file
        datePrintFcn = lambda x: (x - datetime.timedelta(minutes=30)).strftime(
            Toxswa.dateTimeFormat
        )
        fmt = [lambda x: "%5.3f" % x, datePrintFcn, lambda x: "%.9f" % x]
        mflStr = mflTable.to_string(header=False, index=False, formatters=fmt)

        with open(
            os.path.join(self.workDir, "Reach" + str(reach.ID) + ".mfl"), "w"
        ) as mflFile:
            mflFile.write(mflTempl + "\n")
            mflFile.write(mflStr)

    def write_mfsFile(self, reach, hydrologyMassLoadingsTable):
        massFlowTimestepFcn = lambda row: self.reach_massFlowTimestep(
            reach, row["DepWat"], row["QBou"]
        )

        massFlowTimestepLength = hydrologyMassLoadingsTable.apply(
            massFlowTimestepFcn, axis=1
        )
        mfsDateTimeColumn = hydrologyMassLoadingsTable.Time.apply(
            lambda x: x + datetime.timedelta(minutes=30)
        )

        mfsTimestepColumnFcn = lambda x: (
            x - (mfsDateTimeColumn.iloc[0] - dt.timedelta(hours=1))
        ).total_seconds() / (3600 * 24)
        mfsTimestepColumn = mfsDateTimeColumn.apply(mfsTimestepColumnFcn)
        mfsTable = pandas.concat(
            [mfsTimestepColumn, mfsDateTimeColumn, massFlowTimestepLength], axis=1
        )
        mfsTable.columns = ["timeStep", "dateTime", "timestepLength"]

        # Read MFS template file
        with open(
            os.path.join(self.toxswaConfig["toxswaDir"], self.mfsTemplateFile), "r"
        ) as f:
            mfsTempl = f.read()

        # Fill in no of upstream reaches and their IDs
        mfsTempl = re.sub(
            "<upstreamReachIdList>", ", ".join(reach.upstreamIDs), mfsTempl
        )
        # Formatter to convert table to string to write to MFS file
        datePrintFcn = lambda x: (x - datetime.timedelta(minutes=30)).strftime(
            Toxswa.dateTimeFormat
        )
        fmt = [lambda x: "%5.3f" % x, datePrintFcn, lambda x: "%.6g" % x]
        mfsStr = mfsTable.to_string(header=False, index=False, formatters=fmt)

        with open(
            os.path.join(self.workDir, "Reach" + str(reach.ID) + ".mfs"), "w"
        ) as mfsFile:
            mfsFile.write(mfsTempl + "\n")
            mfsFile.write(mfsStr)

    def read_mfsfile(self, reachID):
        mfsFilePath = os.path.join(self.workDir, "Reach" + str(reachID) + ".mfs")
        mfsTable = pandas.read_csv(
            mfsFilePath,
            delim_whitespace=True,
            skiprows=7,
            parse_dates=[1],
            header=None,
            date_parser=cu.mfs_dateparser,
            names=["Time", "DateTime", "MassFluxTimeStep"],
        )
        mfsTable.loc[:, "MassFluxTimeStep"] = pandas.to_timedelta(
            mfsTable.MassFluxTimeStep, unit="S"
        )
        return mfsTable

    def reach_massFlowTimestep(self, reach, waterDepth, flowRate):
        residenceTime = reach.waterResidenceTime(waterDepth, flowRate)

        massFlowTimestep = max(
            self.toxswaConfig.getfloat("minMassFlowTimestep"),
            min(
                Toxswa.hydrologyTimeStep,
                residenceTime * self.toxswaConfig.getfloat("massFlowTimestepParam"),
            ),
        )
        return Toxswa.hydrologyTimeStep / np.floor_divide(
            Toxswa.hydrologyTimeStep, massFlowTimestep
        )

    def write_txwFile(self, reach, hydrologyMassLoadingsTable):
        """
        Creates the TXW file for given reach.
        """

        # variable names, units and widths for waterbody table
        varNameWaterBody = [
            "Len",
            "NumSeg",
            "WidWatSys",
            "SloSidWatSys",
            "DepWatDefPer",
        ]
        varUnitsWaterBody = ["m", "-", "m", "-", "m"]
        varWidthWaterBody = [4, 8, 11, 13, 13]

        # Read contents of TXW template file
        txwTemplate_file = open(
            os.path.join(self.toxswaConfig["toxswaDir"], self.txwTemplateFile), "r"
        )
        txwContent = txwTemplate_file.readlines()
        txwTemplate_file.close()

        # insert start and end date in TXW file
        lineIdx = get_lineIndex(txwContent, "<startDateSim>") - 1
        txwContent[lineIdx] = re.sub(
            "<startDateSim>",
            dt.datetime.strftime(self.startTime, "%d-%b-%Y"),
            txwContent[lineIdx],
        )
        lineIdx = get_lineIndex(txwContent, "<endDateSim>") - 1
        txwContent[lineIdx] = re.sub(
            "<endDateSim>",
            dt.datetime.strftime(self.endTime, "%d-%b-%Y"),
            txwContent[lineIdx],
        )

        # Insert spraydrift information in TXW file
        lineIdx = get_lineIndex(txwContent, "table Loadings")
        for evt in (
            hydrologyMassLoadingsTable.loc[hydrologyMassLoadingsTable.LoaDrf > 0]
        ).iterrows():
            spraydriftStr = " ".join(
                [
                    evt[1].Time.strftime("%d-%b-%Y-%Hh%M"),
                    "Drift",
                    str(0.0),
                    str(0.0),
                    str(evt[1].LoaDrf * self.scaleFacDrift),
                ]
            )
            txwContent.insert(lineIdx, spraydriftStr + "\n")

        # Insert up- and downstream reach IDs
        lineIdx = get_lineIndex(txwContent, "table ReachUp")
        for upstreamID in reach.upstreamIDs:
            txwContent.insert(lineIdx, "Reach" + upstreamID + "\n")

        lineIdx = get_lineIndex(txwContent, "<downstreamReach>") - 1
        if reach.downstreamIDs:
            downstreamIdStr = "Reach" + reach.downstreamIDs[0]
        else:
            downstreamIdStr = "Outlet"
        txwContent[lineIdx] = re.sub(
            "<downstreamReach>", downstreamIdStr, txwContent[lineIdx]
        )

        # Insert waterbody information in TXW file
        # set the Water depth defining perimeter for exchange between water layer and sediment to lowest water depth
        DepWatDefPer = min(hydrologyMassLoadingsTable.DepWat)
        waterBodyVals = [
            reach.length,
            reach.nSegments,
            reach.width,
            reach.slope,
            DepWatDefPer,
        ]
        waterBodyStr = ""
        for i in range(len(varNameWaterBody)):
            varNameWaterBody[i] = varNameWaterBody[i].center(varWidthWaterBody[i])
            varUnitsWaterBody[i] = ("(" + varUnitsWaterBody[i] + ")").center(
                varWidthWaterBody[i]
            )
            waterBodyStr = waterBodyStr + str(waterBodyVals[i]).center(
                varWidthWaterBody[i]
            )
        lineIdx = get_lineIndex(txwContent, "table WaterBody")
        txwContent.insert(lineIdx, " ".join(varNameWaterBody) + "\n")
        txwContent.insert(lineIdx + 1, " ".join(varUnitsWaterBody) + "\n")
        txwContent.insert(lineIdx + 2, waterBodyStr + "\n")

        lineIdx = get_lineIndex(txwContent, "table compounds")
        for substance in self.substanceNames:
            txwContent.insert(lineIdx, substance + "\n")

        lineIdx = get_lineIndex(txwContent, "<substanceName>")
        txwContent[lineIdx - 1] = txwContent[lineIdx - 1].replace(
            "<substanceName>", self.substanceNames[0]
        )
        propSkip = [
            "NumDauWat",
            "FraPrtDauWat",
            "NumDauSed",
            "FraPrtDauSed",
            "SubName.1",
            "SubName.2",
        ]
        substanceTable = pandas.read_csv(
            os.path.join(self.inputDir, self.toxswaConfig["substanceFile"]),
            skiprows=[1],
            index_col=0,
        )
        propUnits = pandas.read_csv(
            os.path.join(self.inputDir, self.toxswaConfig["substanceFile"]), nrows=1
        )
        lineIdx = get_lineIndex(txwContent, "<substanceProperties>")
        del txwContent[lineIdx - 1]
        if len(self.substanceNames) > 1:
            Raise(
                NotImplementedError(
                    "Metabolites not yet implemented, i.e. only one substance allowed"
                )
            )
        for substance in self.substanceNames:
            for prop in list(substanceTable.columns):
                if prop in propSkip:
                    continue
                line = "{:<15g}{}_{} ({})\n".format(
                    substanceTable.loc[substance, prop],
                    prop,
                    substance,
                    propUnits[prop][0],
                )
                txwContent.insert(lineIdx, line)
                lineIdx += 1

        lineIdx = get_lineIndex(txwContent, "<outputVariables>")
        del txwContent[lineIdx - 1]
        for outputVar in self.outputVars:
            if not outputVar in Toxswa.allowedOutputVars:
                raise Exception("Output variable " + outputVar + " not recognized")
            line = "{:<11s}{}\n".format("Yes", "print_" + outputVar)
            txwContent.insert(lineIdx, line)
            lineIdx += 1

        txw_file = open(
            os.path.join(self.workDir, "Reach" + str(reach.ID) + "_tmp.txw"), "w"
        )
        txw_file.write("".join(txwContent))
        txw_file.close()

    def write_hydFile(self, reach, hydrologyMassLoadingsTable):
        """
        Creates the HYD file for given reach.
        """

        # variable names, units and widths for hyd file
        varNameHyd = ["Time", "Date", "QBou", "DepWat"]
        varUnitsHyd = ["-", "-", "m3.s-1", "m"]
        varWidthHyd = [8, 17, 11, 12]
        secondsPerDay = 24 * 60 * 60

        timeStart = hydrologyMassLoadingsTable.Time[0]
        timeStep = [
            (time - timeStart).total_seconds() / secondsPerDay
            for i, time in hydrologyMassLoadingsTable.Time.items()
        ]
        outputTable = pandas.DataFrame(columns=["Time", "Date", "QBou", "DepWat"])
        outputTable.Time = timeStep
        outputTable.Date = hydrologyMassLoadingsTable.Time.values
        outputTable.QBou = hydrologyMassLoadingsTable.QBou.values
        outputTable.DepWat = hydrologyMassLoadingsTable.DepWat.values
        fmt = [
            lambda x: "% 7.3f" % x,
            lambda x: x.strftime("%d-%b-%y-%Hh%M"),
            lambda x: "% 11.3e" % x,
            lambda x: "% 12.3e" % x,
        ]

        for i in range(len(varNameHyd)):
            varNameHyd[i] = varNameHyd[i].center(varWidthHyd[i])
            varUnitsHyd[i] = ("(" + varUnitsHyd[i] + ")").center(varWidthHyd[i])

        outString = outputTable.to_string(index=False, formatters=fmt, header=False)
        outFile = open(
            os.path.join(self.workDir, "Reach" + str(reach.ID) + ".hyd"), "w"
        )
        outFile.write("*" + "".join(varNameHyd) + "\n")
        outFile.write("*" + "".join(varUnitsHyd) + "\n")
        outFile.write(outString)
        outFile.close()

    def update_txwFile(self, reach, timeStepWater, timeStepSediment):
        txw_file = open(
            os.path.join(self.workDir, "Reach" + str(reach.ID) + "_tmp.txw"), "rt"
        )
        txwContent = txw_file.read()
        txw_file.close()
        txwContent = re.sub("<MaxTimStpWat>", str(timeStepWater), txwContent)
        txwContent = re.sub("<MaxTimStpSed>", str(timeStepSediment), txwContent)
        txw_file = open(
            os.path.join(self.workDir, "Reach" + str(reach.ID) + ".txw"), "wt"
        )
        txw_file.write("".join(txwContent))
        txw_file.close()

    def hyd_exists(self, reach):
        return os.path.isfile(
            os.path.join(self.workDir, "Reach" + str(reach.ID) + ".hyd")
        )

    def txw_exists(self, reach):
        return os.path.isfile(
            os.path.join(self.workDir, "Reach" + str(reach.ID) + "_tmp.txw")
        )

    def mfs_exists(self, reach):
        reachID = reach.ID if type(reach) is Reach else reach
        return os.path.isfile(os.path.join(self.workDir, "Reach" + reachID + ".mfs"))

    def mfu_exists(self, reach):
        return os.path.isfile(
            os.path.join(self.workDir, "Reach" + str(reach.ID) + ".mfu")
        )
    def mfl_exists(self, reach):
        return os.path.isfile(
            os.path.join(self.workDir, "Reach" + str(reach.ID) + ".mfl")
        )
    def init(self, reach):
        report = {"reachID": reach.ID, "status": None}
        if reach.skip:
            report["status"] = Toxswa.flagSkipReach
        elif self.checkRun(reach):
            report["status"] = Toxswa.flagSkipExist
        else:
            self.init_reach(reach)
            report["status"] = Toxswa.flagOk
        return report

    def run(self, reach):
        """
        Runs TOXSWA for given reach
        """
        report = {
            "reachID": reach.ID,
            "status": Toxswa.flagOk,
            "runTimeToxswa": None,
            "runTimeTotal": None,
            "timeStepSediment": None,
        }

        if reach.skip:
            self.processOutputFiles(reach, keepOrig=self.keepOrigOutFiles)
            report["status"] = Toxswa.flagSkipReach
        elif self.checkRun(reach):
            report["status"] = Toxswa.flagSkipExist

        if report["status"] in [Toxswa.flagSkipReach, Toxswa.flagSkipExist]:
            if not self.mfu_exists(reach) and reach.massOutflowFileNeeded:
                self.write_dummy_mfu(reach)
            return report

        tStartTotal = time.perf_counter()

        timeStepSediment = self.defaultTimeStep

        try:
            while timeStepSediment >= self.toxswaConfig.getfloat("timeStepMin"):
                # write the txw file
                self.update_txwFile(reach, self.defaultTimeStep, timeStepSediment)
                tStartToxswa = time.perf_counter()

                result = subprocess.run(
                    '"' + self.runToxswaCommand + '"' + " Reach" + str(reach.ID),
                    shell=True,
                    cwd=self.workDir,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                tStop = time.perf_counter()
                dTimeToxswa = tStop - tStartToxswa
                dTimeTotal = tStop - tStartTotal

                # check for errors
                if os.path.isfile(
                    os.path.join(self.workDir, "Reach" + str(reach.ID) + ".ERR")
                ):
                    # reduce timestep length by half if it would not reduce it below the minimum
                    if timeStepSediment / 2 < self.toxswaConfig.getfloat("timeStepMin"):
                        raise Exception("TOXSWA crashed!")
                    else:
                        timeStepSediment = timeStepSediment / 2
                        continue
                else:
                    self.processOutputFiles(reach, keepOrig=self.keepOrigOutFiles)
                    report["status"] = Toxswa.flagOk
                    report["runTimeToxswa"] = dTimeToxswa
                    report["runTimeTotal"] = dTimeTotal
                    report["timeStepSediment"] = timeStepSediment
                    return report

        except:
            report["status"] = Toxswa.flagError
            return report

    def cleanup(self, reach):
        report = {"reachID": reach.ID, "status": None}
        if self.deleteMfuFiles:
            mfuFileName = os.path.join(self.workDir, "Reach" + str(reach.ID) + ".mfu")
            if os.path.exists(mfuFileName):
                os.remove(mfuFileName)
        report["status"] = Toxswa.flagOk
        return report

    def get_all_output(self, reach, substNames=None):
        if substNames is None:
            substNames = self.substanceNames
        elif not type(substNames) is list:
            substNames = [substNames]

        table = None
        for subst in substNames:
            for outputVar in self.outputVars:
                if table is None:
                    table = self.get_output(reach, outputVar, subst)
                else:
                    table[outputVar + "_" + subst] = self.get_output(
                        reach, outputVar, subst
                    )[outputVar + "_" + subst]
        if reach.skip and self.dummyOutTable is None:
            self.dummyOutTable = table
        return table

    def get_output(self, reach, varName, substName):
        """
        Reads and returns variable varName from TOXSWA output file for given reach
        """
        if reach.skip:
            return self.get_output_dummy(reach, varName, substName)
        f = open(os.path.join(self.workDir, "Reach" + str(reach.ID) + ".out"), "r")

        # create a generator to loop over lines in output file that contain varName
        lines = varfilter(f, varName + "_" + substName)

        # write the lines in a memory buffer
        tmp = io.StringIO()
        for line in lines:
            tmp.write(line)
        f.close()
        tmp.flush()
        tmp.seek(0)

        # read from the memory buffer and convert to a table (DataFrame)
        toxswa_output = pandas.read_csv(
            tmp,
            delim_whitespace=True,
            header=None,
            names=["timestep", "date_time", varName + "_" + substName],
            parse_dates=["date_time"],
            infer_datetime_format=True,
            usecols=[0, 1, 3],
        )
        tmp.close()
        return toxswa_output

    def get_output_dummy(self, reach, varName, substName):
        dateTimes = pandas.date_range(
            self.startTime, self.endTime + datetime.timedelta(hours=1), freq="H"
        )
        timeStep = list((dateTimes - self.startTime) / pandas.Timedelta(1.0, unit="D"))
        timeStep = list(map(partial(truncate, decimals=3), timeStep))
        dummyOutTable = pandas.DataFrame()
        dummyOutTable["timestep"] = timeStep
        dummyOutTable["date_time"] = dateTimes
        dummyOutTable["_".join([varName, substName])] = [0] * len(dateTimes)
        return dummyOutTable

    def write_dummy_mfu(self, reach):
        """
        Write a dummy MFU file for given reach with zero mass flux for all steps.
        """
        if not reach.downstreamIDs:
            return

        downstrReachId = reach.downstreamIDs[0]

        # if mfs file for downstream reach does not exist, assume that this reach is skipped, so no mfu file is needed
        if not self.mfs_exists(downstrReachId):
            return

        mfsTable = self.read_mfsfile(downstrReachId)
        nStepFcn = lambda x: int(np.round(dt.timedelta(hours=1) / x))
        mfsTable.loc[:, "nStep"] = mfsTable.MassFluxTimeStep.apply(nStepFcn)

        # Read MFU template file
        file_mfuTempl = open(
            os.path.join(self.toxswaConfig["toxswaDir"], self.mfuTemplateFile), "r"
        )
        mfuTempl = file_mfuTempl.read()
        file_mfuTempl.close()

        # Fill in no of upstream reaches and their IDs
        mfuOut = re.sub("<ReachID>", "Reach" + reach.ID, mfuTempl)
        mfuOut = re.sub("<substanceName>", self.substanceNames[0], mfuOut)

        with open(
            os.path.join(self.workDir, "Reach" + str(reach.ID) + ".mfu"), "w"
        ) as mfuFile:
            mfuFile.write(mfuOut + "\n")
            mfuFile.write("NO_MASS_FLUX" + "\n")

    def processOutputFiles(self, reach, keepOrig=True):
        toxswa_output = self.get_all_output(reach)
        toxswa_output.to_csv(
            os.path.join(self.outputDir, reach.ID + ".csv"), index=False
        )
        if not keepOrig and not reach.skip:
            os.remove(os.path.join(self.workDir, "Reach" + str(reach.ID) + ".out"))

    def checkRun(self, reach):
        """
        Checks if a run finished succesfully
        """
        regexPattern = "\*\s+The run time was\s+\d+ minutes and\s+\d+ seconds*"
        ret = False
        logFileName = os.path.join(self.workDir, "Reach" + reach.ID + ".log")
        if os.path.isfile(logFileName):
            with open(logFileName, "rt") as logFile:
                logFileContents = logFile.readlines()
                if not re.search(regexPattern, logFileContents[-1]) is None:
                    ret = True
        return ret


def varfilter(file, varName):
    """
    Creates a generator that allows us to loop over lines in TOXSWA output file containing varName
    """
    for line in file:
        if varName in line and line.lstrip()[0] != "*":
            yield (line)


def get_lineIndex(fileContents, string):
    """
    Searches for string in text file contents and returns line number
    """
    for num, line in enumerate(fileContents, 1):
        if string in line:
            return num


def truncate(n, decimals=0):
    multiplier = 10**decimals
    return int(n * multiplier) / multiplier
