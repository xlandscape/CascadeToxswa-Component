"""
Component that encapsulates the CascadeToxswa module.
"""
import datetime
import numpy as np
import os
import base
from osgeo import ogr
import attrib


class CascadeToxswa(base.Component):
    """
    A component that encapsulates the CascadeToxswa module for usage within the Landscape Model.
    """
    # RELEASES
    VERSION = base.VersionCollection(
        base.VersionInfo("2.0.5", "2021-08-13"),
        base.VersionInfo("2.0.4", "2021-07-16"),
        base.VersionInfo("2.0.3", "2021-02-19"),
        base.VersionInfo("2.0.2", "2021-01-28"),
        base.VersionInfo("2.0.1", "2020-12-03"),
        base.VersionInfo("2.0.0", "2020-10-22"),
        base.VersionInfo("1.3.35", "2020-08-12"),
        base.VersionInfo("1.3.33", "2020-07-30"),
        base.VersionInfo("1.3.29", "2020-06-15"),
        base.VersionInfo("1.3.27", "2020-05-20"),
        base.VersionInfo("1.3.24", "2020-04-02"),
        base.VersionInfo("1.3.17", "2020-02-25"),
        base.VersionInfo("1.3.15", "2020-02-10"),
        base.VersionInfo("1.3.13", "2020-02-07"),
        base.VersionInfo("1.3.12", "2020-01-29"),
        base.VersionInfo("1.2.40", "2019-11-21"),
        base.VersionInfo("1.2.39", None),
        base.VersionInfo("1.2.33", None),
        base.VersionInfo("1.2.30", None),
        base.VersionInfo("1.2.29", None),
        base.VersionInfo("1.2.28", None),
        base.VersionInfo("1.2.25", None),
        base.VersionInfo("1.2.20", None)
    )

    # AUTHORS
    VERSION.authors.extend((
        "Sascha Bub (component) - sascha.bub@gmx.de",
        "Thorsten Schad (component) - thorsten.schad@bayer.com",
        "Wim Beltman (module) - wim.beltman@wur.nl",
        "Maarten Braakhekke (module) - maarten.braakhekke@wur.nl",
        "Louise Wipfler (module) - louise.wipfler@wur.nl"
    ))

    # ACKNOWLEDGEMENTS
    VERSION.acknowledgements.extend((
        "[TOXSWA](https://www.pesticidemodels.eu/toxswa)",
    ))

    # ROADMAP
    VERSION.roadmap.extend((
        """Replace shapefile input
        ([#1](https://gitlab.bayer.com/aqrisk-landscape/cascadetoxswa-component/-/issues/1))""",
        """Rename Reaches input or output 
        ([#3](https://gitlab.bayer.com/aqrisk-landscape/cascadetoxswa-component/-/issues/3))""",
    ))

    # CHANGELOG
    VERSION.added("1.2.20", "components.CascadeToxswa component")
    VERSION.changed("1.2.25", "Convert discharge to m3/s in components.CascadeToxswa")
    VERSION.changed("1.2.28", "major update of component.CascadeToxswa")
    VERSION.changed("1.2.29", "component.CascadeToxswa updated")
    VERSION.changed("1.2.30", "component.CascadeToxswa updated")
    VERSION.fixed("1.2.33", "Removed quotation mark from components.CascadeToxswa output")
    VERSION.changed("1.2.39", "Integration of CascadeToxswa module in components.CascadeToxswa")
    VERSION.changed("1.2.40", "components.CascadeToxswa updated to module version 0.3")
    VERSION.changed("1.3.12", "components.CascadeToxswa updated to module version 0.4")
    VERSION.changed("1.3.15", "Number of workers parameterizable in components.CascadeToxswa")
    VERSION.changed("1.3.17", "Additional soil bottom width parameter in components.CascadeToxswa")
    VERSION.changed("1.3.24", "components.CascadeToxswa uses base function to call module")
    VERSION.fixed("1.3.27", "Scale of spray-deposition input in components.CascadeToxswa")
    VERSION.changed("1.3.27", "components.CascadeToxswa specifies scales")
    VERSION.fixed("1.3.29", "Input slicing in components.CascadeToxswa")
    VERSION.changed("1.3.33", "components.CascadeToxswa checks input types strictly")
    VERSION.changed("1.3.33", "components.CascadeToxswa checks for physical units")
    VERSION.changed("1.3.33", "components.CascadeToxswa reports physical units to the data store")
    VERSION.changed("1.3.33", "components.CascadeToxswa checks for scales")
    VERSION.changed("1.3.35", "components.CascadeToxswa receives empty path environment variable")
    VERSION.changed("2.0.0", "First independent release")
    VERSION.added("2.0.1", "Changelog and release history")
    VERSION.added("2.0.2", "Module updated to version 0.5")
    VERSION.changed("2.0.3", "Removed soil bottom width parameter")
    VERSION.added("2.0.4", ".gitignore")
    VERSION.fixed("2.0.4", "Retrieval of output data type")
    VERSION.changed("2.0.4", "Spelling of input names")
    VERSION.added("2.0.5", "Base documentation")

    def __init__(self, name, observer, store):
        super(CascadeToxswa, self).__init__(name, observer, store)
        self._module = base.Module("CMF-TOXWA_coupling", "0.5", "https://doi.org/10.18174/547183")
        self._inputs = base.InputContainer(self, [
            base.Input(
                "ProcessingPath",
                (attrib.Class(str, 1), attrib.Unit(None, 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="""The working directory for the module. It is used for all files prepared as module inputs
                or generated as module outputs."""
            ),
            base.Input(
                "Hydrography",
                (attrib.Class(str, 1), attrib.Unit(None, 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="""The spatial delineation of the hydrographic features in the simulated landscape. This
                input basically represents the flow-lines used during preparation of the hydrology. The hydrography is
                consistently for all components of the Landscape Model subdivided into individual segments (*reaches*).
                """
            ),
            base.Input(
                "SuspendedSolids",
                (attrib.Class(float, 1), attrib.Unit("g/m³", 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="The density of suspended solids that applies to all reaches."
            ),
            base.Input(
                "Reaches",
                (attrib.Class(np.ndarray, 1), attrib.Unit(None, 1), attrib.Scales("space/reach", 1)),
                self.default_observer,
                description="""The numeric identifiers for individual reaches (in the order of the `Hydrography` input)
                that apply scenario-wide."""
            ),
            base.Input(
                "TimeSeriesStart",
                (attrib.Class(datetime.date, 1), attrib.Unit(None, 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="""The first time step for which input data is provided. This is also the time step of where
                the CascadeToxswa simulation starts."""
            ),
            base.Input(
                "WaterDischarge",
                (
                    attrib.Class(np.ndarray, 1),
                    attrib.Unit("m³/s", 1),
                    attrib.Scales("time/hour, space/reach", 1)
                ),
                self.default_observer,
                description="The amount of water that leaves a reach within a time step."
            ),
            base.Input(
                "WaterDepth",
                (attrib.Class(np.ndarray, 1), attrib.Unit("m", 1), attrib.Scales("time/hour, space/reach", 1)),
                self.default_observer,
                description="""The depth of the water body measured from the surface to the lowest point of the 
                cross-section profile."""
            ),
            base.Input(
                "Temperature",
                (attrib.Class(np.ndarray, 1), attrib.Unit("°C", 1), attrib.Scales("time/day", 1)),
                self.default_observer,
                description="""The average daily air temperature. If hourly data are available, then the daily average
                temperature should be calculated from these hourly values. However, if only maximum and minimum daily
                temperature are available, these two values can be averaged."""
            ),
            base.Input(
                "MassLoadingSprayDrift",
                (
                    attrib.Class(np.ndarray, 1),
                    attrib.Unit("mg/m²", 1),
                    attrib.Scales("time/day, space/reach", 1)
                ),
                self.default_observer,
                description="The average drift deposition onto the surface of a water body."
            ),
            base.Input(
                "MolarMass",
                (attrib.Class(float, 1), attrib.Unit("g/mol", 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="The molar mass of the substance depositing at the water body surface."
            ),
            base.Input(
                "SaturatedVapourPressure",
                (attrib.Class(float, 1), attrib.Unit("Pa", 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="The saturated vapor pressure of the substance depositing at the water body surface."
            ),
            base.Input(
                "ReferenceTemperatureForSaturatedVapourPressure",
                (attrib.Class(float, 1), attrib.Unit("°C", 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="The temperature to which the value of the `SaturatedVaporPressure` applies."
            ),
            base.Input(
                "MolarEnthalpyOfVaporization",
                (attrib.Class(float, 1), attrib.Unit("kJ/mol", 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="The molar vaporization enthalpy of the substance depositing at the water body surface."
            ),
            base.Input(
                "SolubilityInWater",
                (attrib.Class(float, 1), attrib.Unit("mg/l", 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="The water solubility of the substance depositing at the water body surface."
            ),
            base.Input(
                "ReferenceTemperatureForWaterSolubility",
                (attrib.Class(float, 1), attrib.Unit("°C", 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="The temperature to which the value of the `SolubilityInWater` applies."
            ),
            base.Input(
                "MolarEnthalpyOfDissolution",
                (attrib.Class(float, 1), attrib.Unit("kJ/mol", 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="The molar dissolution enthalpy of the substance depositing at the water body surface."
            ),
            base.Input(
                "DiffusionCoefficient",
                (attrib.Class(float, 1), attrib.Unit("m²/d", 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="The diffusion coefficient of the substance depositing at the water body surface."
            ),
            base.Input(
                "ReferenceTemperatureForDiffusion",
                (attrib.Class(float, 1), attrib.Unit("°C", 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="The temperature to which the value of the `DiffusionCoefficient` applies."
            ),
            base.Input(
                "HalfLifeTransformationInWater",
                (attrib.Class(float, 1), attrib.Unit("d", 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="""The half-life transformation time in water of the substance depositing at the water body 
                surface."""
            ),
            base.Input(
                "TemperatureAtWhichHalfLifeInWaterWasMeasured",
                (attrib.Class(float, 1), attrib.Unit("°C", 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="The temperature to which the value of the `HalfLifeTransformationInWater` applies."
            ),
            base.Input(
                "MolarActivationEnthalpyOfTransformationInWater",
                (attrib.Class(float, 1), attrib.Unit("kJ/mol", 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="The molar activation enthalpy relating to the transformation in water."
            ),
            base.Input(
                "HalfLifeTransformationInSediment",
                (attrib.Class(float, 1),  attrib.Unit("d", 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="""The half-life transformation time in sediment of the substance depositing at the water 
                body surface."""
            ),
            base.Input(
                "TemperatureAtWhichHalfLifeInSedimentWasMeasured",
                (attrib.Class(float, 1), attrib.Unit("°C", 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="The temperature to which the value of the `HalfLifeTransformationInSediment` applies."
            ),
            base.Input(
                "MolarActivationEnthalpyOfTransformationInSediment",
                (attrib.Class(float, 1), attrib.Unit("kJ/mol", 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="The molar activation enthalpy relating to the transformation in sediment."
            ),
            base.Input(
                "CoefficientForEquilibriumAdsorptionInSediment",
                (attrib.Class(float, 1), attrib.Unit("l/kg", 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="""The coefficient for equilibrium adsorption in sediment of the substance depositing at 
                the water body surface."""
            ),
            base.Input(
                "ReferenceConcentrationInLiquidPhaseInSediment",
                (attrib.Class(float, 1), attrib.Unit("mg/l", 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="""The reference concentration in liquid phase in sediment of the substance depositing at 
                the water body surface."""
            ),
            base.Input(
                "FreundlichExponentInSediment",
                (attrib.Class(float, 1), attrib.Unit("1", 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="""The Freundlich exponent in sediment of the substance depositing at the water body 
                surface."""
            ),
            base.Input(
                "CoefficientForEquilibriumAdsorptionOfSuspendedSoils",
                (attrib.Class(float, 1), attrib.Unit("l/kg", 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="The coefficient for equilibrium adsorption of suspended soils."
            ),
            base.Input(
                "ReferenceConcentrationForSuspendedSoils",
                (attrib.Class(float, 1), attrib.Unit("mg/l", 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="The reference concentration for suspended soils."
            ),
            base.Input(
                "FreundlichExponentForSuspendedSoils",
                (attrib.Class(float, 1), attrib.Unit("1", 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="The Freundlich exponent for suspended particles."
            ),
            base.Input(
                "CoefficientForLinearAdsorptionOnMacrophytes",
                (attrib.Class(float, 1), attrib.Unit("l/kg", 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="""The coefficient for the linear adsorption of the substance on macrophytes."""
            ),
            base.Input(
                "NumberWorkers",
                (attrib.Class(int, 1), attrib.Unit(None, 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="""The number of individual worker processes for the CascadeToxswa simulation. Higher values
                usually result in a faster processing, but performance will drop if the available processors are 
                overloaded with workers. Consider for an optimal value also other processes running on the same 
                machine, especially other Monte Carlo runs of the Landscape Model."""
            )
        ])
        self._outputs = base.OutputContainer(self, [
            base.Output(
                "Reaches",
                store,
                self,
                {"scales": "space/reach", "unit": None},
                """The numerical identifiers of the reaches in the order presented by the other outputs. See the 
                `Reaches` input for further details on identifiers.""",
                {"type": "list[int]"}
            ),
            base.Output(
                "ConLiqWatTgtAvg",
                store,
                self,
                {"data_type": np.float, "scales": "time/hour, space/base_geometry", "unit": "g/m³"},
                "The average concentration along the reach at the specified moment in time in the water phase.",
                {
                    "type": np.ndarray,
                    "shape": (
                        "the number of time steps as given by the [WaterDischarge](#WaterDischarge) input",
                        "the number of reaches as given by the `Reaches` input"
                    ),
                    "chunks": "for fast retrieval of time series"
                }
            ),
            base.Output(
                "ConLiqWatTgtAvgHrAvg",
                store,
                self,
                {"data_type": np.float, "scales": "time/hour, space/base_geometry", "unit": "g/m³"},
                "The time weighted average of concentration in the water phase averaged for a reach.",
                {
                    "type": np.ndarray,
                    "shape": (
                        "the number of time steps as given by the [WaterDischarge](#WaterDischarge) input",
                        "the number of reaches as given by the `Reaches` input"
                    ),
                    "chunks": "for fast retrieval of time series"
                }
            ),
            base.Output(
                "CntSedTgt1",
                store,
                self,
                {"data_type": np.float, "scales": "time/hour, space/base_geometry", "unit": "g/kg"},
                "The total content in target layer 1 of sediment atb the specified time.",
                {
                    "type": np.ndarray,
                    "shape": (
                        "the number of time steps as given by the [WaterDischarge](#WaterDischarge) input",
                        "the number of reaches as given by the `Reaches` input"
                    ),
                    "chunks": "for fast retrieval of time series"
                }
            )
        ])
        return

    def run(self):
        """
        Runs the component.
        :return: Nothing.
        """
        processing_path = self.inputs["ProcessingPath"].read().values
        if " " in processing_path or " " in __file__:
            raise RuntimeError("CascadeToxswa cannot run with spaces in path")
        parameterization_file = os.path.join(processing_path, "IFEM_config.ini")
        reach_file = "reaches.csv"
        temperature_file = "temperature.csv"
        substance_file = "substances.csv"
        os.makedirs(processing_path)
        self.prepare_hydrological_data(processing_path, os.path.join(processing_path, reach_file))
        self.prepare_temperature(os.path.join(processing_path, temperature_file))
        self.prepare_substance(os.path.join(processing_path, substance_file))
        self.prepare_parameterization(parameterization_file, processing_path, reach_file, temperature_file,
                                      substance_file)
        self.run_cascade_toxswa(parameterization_file, processing_path)
        self.read_outputs(os.path.join(processing_path, "experiments", "e1"))
        return

    def prepare_hydrological_data(self, output_path, reaches_file):
        """
        Prepares the hydrological input data for the module.
        :param output_path: The path for the hydrological input data.
        :param reaches_file: The path for the reaches input file.
        :return: Nothing.
        """
        hydrography = self.inputs["Hydrography"].read().values
        suspended_solids = self.inputs["SuspendedSolids"].read().values
        reaches = self.inputs["Reaches"].read().values
        time_series_start = self.inputs["TimeSeriesStart"].read().values
        number_time_steps = self.inputs["WaterDischarge"].describe()["shape"][0]
        driver = ogr.GetDriverByName("ESRI Shapefile")
        data_source = driver.Open(hydrography, 0)
        layer = data_source.GetLayer()
        with open(reaches_file, "w") as f:
            # noinspection SpellCheckingInspection
            f.write(
                "RchID,RchIDDwn,Len,WidWatSys,SloSidWatSys,ConSus,CntOmSusSol,Rho,ThetaSat,CntOM,X,Y,Expsd\n" +
                "-,-,m,m,-,g/m3,g/g,kg/m3,m3/m3,g/g,-,-,-\n")
            for feature in layer:
                key_r = feature.GetField("key")
                geom = feature.GetGeometryRef()
                coord = geom.GetPoint(0)
                exposed = False
                f.write("R" + str(key_r) + ",")
                f.write("R" + feature.GetField("downstream").upper() + ',')
                f.write(str(round(geom.Length(), 1)) + ",")
                # noinspection SpellCheckingInspection
                f.write(str(round(float(feature.GetField("btmwidth")), 2)) + ",")
                # noinspection SpellCheckingInspection
                f.write(str(round(1 / float(feature.GetField("bankslope")), 2)) + ",")
                f.write(str(round(float(suspended_solids), 1)) + ",")
                f.write(str(round(float(feature.GetField("oc")) * 1.742, 2)) + ",")
                f.write(str(round(float(feature.GetField("dens")) * 1e3)) + ",")
                f.write(str(round(float(feature.GetField("porosity")), 2)) + ",")
                f.write(str(round(float(feature.GetField("oc")) * 1.742, 2)) + ",")
                f.write(str(coord[0]) + ",")
                f.write(str(coord[1]) + ",")
                i = int(np.where(reaches == key_r)[0])
                discharge = self.inputs["WaterDischarge"].read(slices=(slice(number_time_steps), i)).values
                depth = self.inputs["WaterDepth"].read(slices=(slice(number_time_steps), i)).values
                mass_loading_spray_drift = self.inputs["MassLoadingSprayDrift"].read(
                    slices=(slice(int(number_time_steps / 24)), i)).values
                with open(os.path.join(output_path, "R" + str(key_r) + ".csv"), "w") as f2:
                    f2.write("Time,QBou,DepWat,LoaDrf\n-,m3.s-1,m,mg.m-2\n")
                    for t in range(number_time_steps):
                        if t % 24 == 11:
                            loading = mass_loading_spray_drift[int((t - 11) / 24)]
                            if loading > 0:
                                exposed = True
                        else:
                            loading = 0
                        f2.write(
                            (time_series_start + datetime.timedelta(hours=t)).strftime("%d-%b-%Y-%Hh%M") + ",")  # Time
                        f2.write(format(float(discharge[t]), "E") + ",")  # QBou
                        f2.write(str(round(float(depth[t]), 3)) + ",")  # DepWat
                        f2.write(format(float(loading), "E") + "\n")  # LoaDrf
                f.write(str(exposed) + "\n")
        return

    def prepare_temperature(self, output_file):
        """
        Prepares the temperature input for the module.
        :param output_file: The path for the input file.
        :return: Nothing.
        """
        temperature = self.inputs["Temperature"].read().values
        time_series_start = self.inputs["TimeSeriesStart"].read().values.date()
        with open(output_file, "w") as f:
            f.write("Time,TemAir\n-,C\n")
            for i in range(len(temperature)):
                f.write((time_series_start + datetime.timedelta(i)).strftime("%d-%b-%Y") + ",")
                f.write(str(round(temperature[i], 2)) + "\n")
        return

    def prepare_substance(self, output_file):
        """
        Prepares the substance information for the module.
        :param output_file: The name for the input file.
        :return: Nothing.
        """
        with open(output_file, "w") as f:
            f.write("SubName,MolMas,PreVapRef,TemRefVap,MolEntVap,SlbWatRef,TemRefSlb,MolEntSlb,CofDifWatRef," +
                    "TemRefDif,DT50WatRef,TemRefTraWat,MolEntTraWat,DT50SedRef,TemRefTraSed,MolEntTraSed,KomSed," +
                    "ConLiqRefSed,ExpFreSed,KomSusSol,ConLiqRefSusSol,ExpFreSusSol,CofSorMph,NumDauWat,SubName," +
                    "FraPrtDauWat,NumDauSed,SubName,FraPrtDauSed\n-,g.mol-1,Pa,C,kJ.mol-1,mg.L-1,C,kJ.mol-1,m2.d-1," +
                    "C,d,C,kJ.mol-1,d,C,kJ.mol-1,L.kg-1,mg.L-1,-,L.kg-1,mg.L-1,-,L.kg-1,-,-,mol.mol-1,-,-,mol.mol-1\n")
            f.write("CMP_A,{},".format(self.inputs["MolarMass"].read().values))
            f.write(str(self.inputs["SaturatedVapourPressure"].read().values) + ",")
            f.write(str(self.inputs["ReferenceTemperatureForSaturatedVapourPressure"].read().values) + ",")
            f.write(str(self.inputs["MolarEnthalpyOfVaporization"].read().values) + ",")
            f.write(str(self.inputs["SolubilityInWater"].read().values) + ",")
            f.write(str(self.inputs["ReferenceTemperatureForWaterSolubility"].read().values) + ",")
            f.write(str(self.inputs["MolarEnthalpyOfDissolution"].read().values) + ",")
            f.write(str(self.inputs["DiffusionCoefficient"].read().values) + ",")
            f.write(str(self.inputs["ReferenceTemperatureForDiffusion"].read().values) + ",")
            f.write(str(self.inputs["HalfLifeTransformationInWater"].read().values) + ",")
            f.write(str(self.inputs["TemperatureAtWhichHalfLifeInWaterWasMeasured"].read().values) + ",")
            f.write(str(self.inputs["MolarActivationEnthalpyOfTransformationInWater"].read().values) + ",")
            f.write(str(self.inputs["HalfLifeTransformationInSediment"].read().values) + ",")
            f.write(str(self.inputs["TemperatureAtWhichHalfLifeInSedimentWasMeasured"].read().values) + ",")
            f.write(str(self.inputs["MolarActivationEnthalpyOfTransformationInSediment"].read().values) + ",")
            f.write(str(self.inputs["CoefficientForEquilibriumAdsorptionInSediment"].read().values) + ",")
            f.write(str(self.inputs["ReferenceConcentrationInLiquidPhaseInSediment"].read().values) + ",")
            f.write(str(self.inputs["FreundlichExponentInSediment"].read().values) + ",")
            f.write(str(self.inputs["CoefficientForEquilibriumAdsorptionOfSuspendedSoils"].read().values) + ",")
            f.write(str(self.inputs["ReferenceConcentrationForSuspendedSoils"].read().values) + ",")
            f.write(str(self.inputs["FreundlichExponentForSuspendedSoils"].read().values) + ",")
            f.write(str(self.inputs["CoefficientForLinearAdsorptionOnMacrophytes"].read().values) + ",0,-,0,0,-\n")
        return

    def prepare_parameterization(self, parameter_file, processing_path, reach_file, temperature_file, substance_file):
        """
        Prepares the module's parameterization.
        :param parameter_file: The path for the parameterization file.
        :param processing_path: The processing path for the module.
        :param reach_file: The path of the reach file.
        :param temperature_file: The path of the temperature file.
        :param substance_file: The path of the substance file.
        :return: Nothing.
        """
        with open(parameter_file, "w") as f:
            f.write("[general]\n")
            f.write("nWorker = {}\n".format(self.inputs["NumberWorkers"].read().values))
            f.write("inputDir = " + processing_path + "\n")
            f.write("experimentName = e1\n")
            f.write("reachSelection = all\n")
            f.write("reachFile = " + reach_file + "\n")
            f.write("startDateSim = " + self.inputs["TimeSeriesStart"].read().values.strftime("%d-%b-%Y") + "\n")
            f.write("endDateSim = " +
                    (self.inputs["TimeSeriesStart"].read().values + datetime.timedelta(
                        self.inputs["MassLoadingSprayDrift"].describe()["shape"][0] - 1)).strftime("%d-%b-%Y") +
                    "\n")
            f.write("\n[toxswa]\n")
            f.write("toxswaDir = " + os.path.join(os.path.dirname(__file__), "module", "TOXSWA") + "\n")
            f.write("fileNameHydMassLoad = \n")
            f.write("timeStepDefault = 600\n")
            f.write("temperatureFile = " + temperature_file + "\n")
            f.write("substanceFile = " + substance_file + "\n")
            f.write("substanceNames = CMP_A\n")
            f.write("timeStepMin = 10\n")
            f.write("outputVars = ConLiqWatTgtAvg,ConLiqWatTgtAvgHrAvg,CntSedTgt1\n")
            f.write("keepOrigOutFiles = False\n")
            # noinspection SpellCheckingInspection
            f.write("massFlowTimestepParam = 1\n")
            # noinspection SpellCheckingInspection
            f.write("minMassFlowTimestep = 0.1\n")
            f.write("deleteMfuFiles = True\n")
            return

    def run_cascade_toxswa(self, parameterization_file, processing_path):
        """
        Runs the module.
        :param parameterization_file: The path of the parameterization file.
        :param processing_path: The processing path of the module.
        :return: Nothing.
        """
        python_exe = os.path.join(os.path.dirname(__file__), "module", "WPy64-3760", "python-3.7.6.amd64",
                                  "python.exe")
        # noinspection SpellCheckingInspection
        python_script = os.path.join(os.path.dirname(__file__), "module", "src", "TOXSWA_IFEM.py")
        base.run_process(
            (python_exe, python_script, parameterization_file),
            processing_path,
            self.default_observer,
            {"PATH": ""}
        )
        return

    def read_outputs(self, output_path):
        """
        Reads the module's outputs into the Landscape Model data store.
        :param output_path: The output path of the module.
        :return: Nothing.
        """
        reaches = self.inputs["Reaches"].read().values
        self.outputs["Reaches"].set_values(reaches.tolist())
        number_time_steps = self.inputs["WaterDischarge"].describe()["shape"][0]
        self.outputs["ConLiqWatTgtAvg"].set_values(
            np.ndarray, shape=(number_time_steps, reaches.shape[0]), chunks=(min(65536, number_time_steps), 1))
        self.outputs["ConLiqWatTgtAvgHrAvg"].set_values(
            np.ndarray, shape=(number_time_steps, reaches.shape[0]), chunks=(min(65536, number_time_steps), 1))
        self.outputs["CntSedTgt1"].set_values(
            np.ndarray, shape=(number_time_steps, reaches.shape[0]),  chunks=(min(65536, number_time_steps), 1))
        for i, reach in enumerate(reaches):
            water_concentration = np.zeros(number_time_steps)
            water_concentration_hr = np.zeros(number_time_steps)
            sediment_concentration = np.zeros(number_time_steps)
            with open(os.path.join(output_path, "R" + str(reach) + ".csv")) as f:
                f.readline()
                for t in range(number_time_steps):
                    fields = f.readline().split(",")
                    water_concentration[t] = float(fields[2])
                    water_concentration_hr[t] = float(fields[3])
                    sediment_concentration[t] = float(fields[4])
            self.outputs["ConLiqWatTgtAvg"].set_values(
                water_concentration, slices=(slice(number_time_steps), i), create=False)
            self.outputs["ConLiqWatTgtAvgHrAvg"].set_values(
                water_concentration_hr, slices=(slice(number_time_steps), i), create=False)
            self.outputs["CntSedTgt1"].set_values(
                sediment_concentration, slices=(slice(number_time_steps), i), create=False)
        return
