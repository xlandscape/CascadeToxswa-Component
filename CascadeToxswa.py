"""Component that encapsulates the CascadeToxswa module."""
import datetime
import numpy as np
import os
import base
from osgeo import ogr
import attrib


class CascadeToxswa(base.Component):
    """A component that encapsulates the CascadeToxswa module for usage within the Landscape Model."""
    # RELEASES
    VERSION = base.VersionCollection(
        base.VersionInfo("2.3.1", "2022-03-08"),
        base.VersionInfo("2.3.0", "2021-12-13"),
        base.VersionInfo("2.2.2", "2021-12-10"),
        base.VersionInfo("2.2.1", "2021-12-07"),
        base.VersionInfo("2.2.0", "2021-11-24"),
        base.VersionInfo("2.1.6", "2021-11-18"),
        base.VersionInfo("2.1.5", "2021-10-12"),
        base.VersionInfo("2.1.4", "2021-10-11"),
        base.VersionInfo("2.1.3", "2021-09-21"),
        base.VersionInfo("2.1.2", "2021-09-17"),
        base.VersionInfo("2.1.1", "2021-09-14"),
        base.VersionInfo("2.1.0", "2021-09-13"),
        base.VersionInfo("2.0.6", "2021-08-16"),
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
    VERSION.roadmap.extend(())

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
    VERSION.added("2.0.6", "`ConLiqWatTgtAvgHrAvg` output")
    VERSION.changed("2.1.0", "Replaced shapefile input")
    VERSION.changed("2.1.1", "`Reaches` input renamed to `HydrographyReachesIds` ")
    VERSION.changed("2.1.2", "Make use of generic types for class attributes")
    VERSION.added("2.1.3", "Input descriptions")
    VERSION.changed("2.1.4", "Replaced legacy format strings by f-strings")
    VERSION.changed("2.1.5", "Switched to Google docstring style")
    VERSION.changed("2.1.6", "Removed reach inputs and output")
    VERSION.changed("2.1.6", "Reports element names of outputs")
    VERSION.changed("2.2.0", "Updated module to version 0.5-211124")
    VERSION.changed("2.2.1", "Spell checking")
    VERSION.changed("2.2.2", "Specifies offset of outputs")
    VERSION.changed("2.3.0", "Updated module to version 0.5-211213")
    VERSION.changed("2.3.1", "Usage of native coordinates for temperature timeseries input")

    def __init__(self, name, observer, store):
        """
        Initializes the CascadeToxswa component.

        Args:
            name: The name of the component.
            observer: The default observer used by the component.
            store: The data store used by the component.
        """
        super(CascadeToxswa, self).__init__(name, observer, store)
        self._module = base.Module("CMF-TOXWA_coupling", "0.5-211213", "https://doi.org/10.18174/547183")
        self._inputs = base.InputContainer(self, [
            base.Input(
                "ProcessingPath",
                (attrib.Class(str, 1), attrib.Unit(None, 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="""The working directory for the module. It is used for all files prepared as module inputs
                or generated as module outputs."""
            ),
            base.Input(
                "SuspendedSolids",
                (attrib.Class(float, 1), attrib.Unit("g/m³", 1), attrib.Scales("global", 1)),
                self.default_observer,
                description="The density of suspended solids of all reaches."
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
                description="""The reference concentration of the deposited substance in the liquid phase of the 
                sediment ."""
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
            ),
            base.Input(
                "HydrographyGeometries",
                (attrib.Class(list[bytes]), attrib.Unit(None), attrib.Scales("space/base_geometry")),
                self.default_observer,
                description="The geometries of individual water body segments (reaches) in WKB representation."
            ),
            base.Input(
                "DownstreamReach",
                (attrib.Class(list[str]), attrib.Unit(None), attrib.Scales("space/base_geometry")),
                self.default_observer,
                description="The identifier of the reach that is located downstream of the current reach."
            ),
            base.Input(
                "BottomWidth",
                (attrib.Class(list[float]), attrib.Unit("m"), attrib.Scales("space/base_geometry")),
                self.default_observer,
                description="The width of the reach at its bottom."
            ),
            base.Input(
                "BankSlope",
                (attrib.Class(list[float]), attrib.Unit("1"), attrib.Scales("space/base_geometry")),
                self.default_observer,
                description="The slope of the reach."
            ),
            base.Input(
                "OrganicContent",
                (attrib.Class(list[float]), attrib.Unit("g/g"), attrib.Scales("space/base_geometry")),
                self.default_observer,
                description="The amount of organic material in the sediment of the reach."
            ),
            base.Input(
                "BulkDensity",
                (attrib.Class(list[float]), attrib.Unit("kg/m³"), attrib.Scales("space/base_geometry")),
                self.default_observer,
                description="The mass density of the reach sediment."
            ),
            base.Input(
                "Porosity",
                (attrib.Class(list[float]), attrib.Unit("m³/m³"), attrib.Scales("space/base_geometry")),
                self.default_observer,
                description="The porosity of the reach sediment."
            )
        ])
        self._outputs = base.OutputContainer(
            self,
            (
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
            )
        )

    def run(self):
        """
        Runs the component.

        Returns:
            Nothing.
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

    def prepare_hydrological_data(self, output_path, reaches_file):
        """
        Prepares the hydrological input data for the module.

        Args:
            output_path: The path for the hydrological input data.
            reaches_file: The path for the reaches input file.

        Returns:
            Nothing.
        """
        hydrography_geometries = self.inputs["HydrographyGeometries"].read()
        hydrography_reaches = hydrography_geometries.element_names[0].get_values()
        suspended_solids = self.inputs["SuspendedSolids"].read().values
        reaches = self.inputs["MassLoadingSprayDrift"].describe()["element_names"][1].get_values()
        time_series_start = self.inputs["TimeSeriesStart"].read().values
        number_time_steps = self.inputs["WaterDischarge"].describe()["shape"][0]
        downstream_reaches = self.inputs["DownstreamReach"].read().values
        bottom_widths = self.inputs["BottomWidth"].read().values
        bank_slopes = self.inputs["BankSlope"].read().values
        organic_contents = self.inputs["OrganicContent"].read().values
        bulk_densities = self.inputs["BulkDensity"].read().values
        porosity = self.inputs["Porosity"].read().values
        with open(reaches_file, "w") as f:
            # noinspection SpellCheckingInspection
            f.write(
                "RchID,RchIDDwn,Len,WidWatSys,SloSidWatSys,ConSus,CntOmSusSol,Rho,ThetaSat,CntOM,X,Y,Expsd\n"
                "-,-,m,m,-,g/m3,g/g,kg/m3,m3/m3,g/g,-,-,-\n"
            )
            for i in range(len(hydrography_reaches)):
                key_r = hydrography_reaches[i]
                geom = ogr.CreateGeometryFromWkb(hydrography_geometries.values[i])
                coord = geom.GetPoint(0)
                exposed = False
                f.write(f"R{key_r},")
                f.write(f"R{downstream_reaches[i].upper()},")
                f.write(f"{round(geom.Length(), 1)},")
                f.write(f"{round(bottom_widths[i], 2)},")
                f.write(f"{round(1 / bank_slopes[i], 2)},")
                f.write(f"{round(suspended_solids, 1)},")
                f.write(f"{round(organic_contents[i] * 1.742, 2)},")
                f.write(f"{round(bulk_densities[i])},")
                f.write(f"{round(porosity[i], 2)},")
                f.write(f"{round(organic_contents[i] * 1.742, 2)},")
                f.write(f"{coord[0]},")
                f.write(f"{coord[1]},")
                i = int(np.where(reaches == key_r)[0])
                discharge = self.inputs["WaterDischarge"].read(slices=(slice(number_time_steps), i)).values
                depth = self.inputs["WaterDepth"].read(slices=(slice(number_time_steps), i)).values
                mass_loading_spray_drift = self.inputs["MassLoadingSprayDrift"].read(
                    slices=(slice(int(number_time_steps / 24)), i)).values
                with open(os.path.join(output_path, f"R{key_r}.csv"), "w") as f2:
                    # noinspection GrazieInspection
                    f2.write("Time,QBou,DepWat,LoaDrf\n-,m3.s-1,m,mg.m-2\n")
                    for t in range(number_time_steps):
                        if t % 24 == 11:
                            loading = mass_loading_spray_drift[int((t - 11) / 24)]
                            if loading > 0:
                                exposed = True
                        else:
                            loading = 0
                        f2.write(
                            f"{(time_series_start + datetime.timedelta(hours=t)).strftime('%d-%b-%Y-%Hh%M')},")
                        f2.write(f"{format(float(discharge[t]), 'E')},")
                        f2.write(f"{round(float(depth[t]), 3)},")
                        f2.write(f"{format(float(loading), 'E')}\n")
                f.write(f"{exposed}\n")

    def prepare_temperature(self, output_file):
        """
        Prepares the temperature input for the module.

        Args:
            output_file: The path for the input file.

        Returns:
            Nothing.
        """
        time_series_start = self.inputs["TimeSeriesStart"].read().values.date()
        end_date_sim = (
                time_series_start + datetime.timedelta(self.inputs["MassLoadingSprayDrift"].describe()["shape"][0]))
        temperature = self.inputs["Temperature"].read(
            select={"time/day": {"from": time_series_start, "to": end_date_sim}}).values

        with open(output_file, "w") as f:
            f.write("Time,TemAir\n-,C\n")
            for i in range(len(temperature)):
                f.write(f"{(time_series_start + datetime.timedelta(i)).strftime('%d-%b-%Y')},")
                f.write(f"{round(temperature[i], 2)}\n")

    def prepare_substance(self, output_file):
        """
        Prepares the substance information for the module.

        Args:
            output_file: The name for the input file.

        Returns:
            Nothing.
        """
        with open(output_file, "w") as f:
            # noinspection GrazieInspection
            f.write(
                "SubName,MolMas,PreVapRef,TemRefVap,MolEntVap,SlbWatRef,TemRefSlb,MolEntSlb,CofDifWatRef,TemRefDif,"
                "DT50WatRef,TemRefTraWat,MolEntTraWat,DT50SedRef,TemRefTraSed,MolEntTraSed,KomSed,ConLiqRefSed,"
                "ExpFreSed,KomSusSol,ConLiqRefSusSol,ExpFreSusSol,CofSorMph,NumDauWat,SubName,FraPrtDauWat,NumDauSed,"
                "SubName,FraPrtDauSed\n-,g.mol-1,Pa,C,kJ.mol-1,mg.L-1,C,kJ.mol-1,m2.d-1,C,d,C,kJ.mol-1,d,C,kJ.mol-1,"
                "L.kg-1,mg.L-1,-,L.kg-1,mg.L-1,-,L.kg-1,-,-,mol.mol-1,-,-,mol.mol-1\n")
            f.write(f"CMP_A,{self.inputs['MolarMass'].read().values},")
            f.write(f"{self.inputs['SaturatedVapourPressure'].read().values},")
            f.write(f"{self.inputs['ReferenceTemperatureForSaturatedVapourPressure'].read().values},")
            f.write(f"{self.inputs['MolarEnthalpyOfVaporization'].read().values},")
            f.write(f"{self.inputs['SolubilityInWater'].read().values},")
            f.write(f"{self.inputs['ReferenceTemperatureForWaterSolubility'].read().values},")
            f.write(f"{self.inputs['MolarEnthalpyOfDissolution'].read().values},")
            f.write(f"{self.inputs['DiffusionCoefficient'].read().values},")
            f.write(f"{self.inputs['ReferenceTemperatureForDiffusion'].read().values},")
            f.write(f"{self.inputs['HalfLifeTransformationInWater'].read().values},")
            f.write(f"{self.inputs['TemperatureAtWhichHalfLifeInWaterWasMeasured'].read().values},")
            f.write(f"{self.inputs['MolarActivationEnthalpyOfTransformationInWater'].read().values},")
            f.write(f"{self.inputs['HalfLifeTransformationInSediment'].read().values},")
            f.write(f"{self.inputs['TemperatureAtWhichHalfLifeInSedimentWasMeasured'].read().values},")
            f.write(f"{self.inputs['MolarActivationEnthalpyOfTransformationInSediment'].read().values},")
            f.write(f"{self.inputs['CoefficientForEquilibriumAdsorptionInSediment'].read().values},")
            f.write(f"{self.inputs['ReferenceConcentrationInLiquidPhaseInSediment'].read().values},")
            f.write(f"{self.inputs['FreundlichExponentInSediment'].read().values},")
            f.write(f"{self.inputs['CoefficientForEquilibriumAdsorptionOfSuspendedSoils'].read().values},")
            f.write(f"{self.inputs['ReferenceConcentrationForSuspendedSoils'].read().values},")
            f.write(f"{self.inputs['FreundlichExponentForSuspendedSoils'].read().values},")
            f.write(f"{self.inputs['CoefficientForLinearAdsorptionOnMacrophytes'].read().values},0,-,0,0,-\n")

    def prepare_parameterization(self, parameter_file, processing_path, reach_file, temperature_file, substance_file):
        """
        Prepares the module's parameterization.

        Args:
            parameter_file: The path for the parameterization file.
            processing_path: The processing path for the module.
            reach_file: The path of the reach file.
            temperature_file: The path of the temperature file.
            substance_file: The path of the substance file.

        Returns:
            Nothing.
        """
        end_date_sim = (self.inputs["TimeSeriesStart"].read().values + datetime.timedelta(
            self.inputs["MassLoadingSprayDrift"].describe()["shape"][0] - 1)).strftime("%d-%b-%Y")
        with open(parameter_file, "w") as f:
            f.write("[general]\n")
            f.write(f"nWorker = {self.inputs['NumberWorkers'].read().values}\n")
            f.write(f"inputDir = {processing_path}\n")
            f.write("experimentName = e1\n")
            f.write("reachSelection = all\n")
            f.write(f"reachFile = {reach_file}\n")
            f.write(f"startDateSim = {self.inputs['TimeSeriesStart'].read().values.strftime('%d-%b-%Y')}\n")
            f.write(f"endDateSim = {end_date_sim}\n")
            f.write("\n[toxswa]\n")
            f.write(f"toxswaDir = {os.path.join(os.path.dirname(__file__), 'module', 'TOXSWA')}\n")
            f.write("fileNameHydMassLoad = \n")
            f.write("timeStepDefault = 600\n")
            f.write(f"temperatureFile = {temperature_file}\n")
            f.write(f"substanceFile = {substance_file}\n")
            f.write("substanceNames = CMP_A\n")
            f.write("timeStepMin = 10\n")
            f.write("outputVars = ConLiqWatTgtAvg,ConLiqWatTgtAvgHrAvg,CntSedTgt1\n")
            f.write("keepOrigOutFiles = False\n")
            # noinspection SpellCheckingInspection
            f.write("massFlowTimestepParam = 1\n")
            # noinspection SpellCheckingInspection
            f.write("minMassFlowTimestep = 0.1\n")
            f.write("deleteMfuFiles = True\n")

    def run_cascade_toxswa(self, parameterization_file, processing_path):
        """
        Runs the module.

        Args:
            parameterization_file: The path of the parameterization file.
            processing_path: The processing path of the module.

        Returns:
            Nothing.
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

    def read_outputs(self, output_path):
        """
        Reads the module's outputs into the Landscape Model data store.

        Args:
            output_path: The output path of the module.

        Returns:
            Nothing.
        """
        deposition_info = self.inputs["MassLoadingSprayDrift"].read()
        number_time_steps = self.inputs["WaterDischarge"].describe()["shape"][0]
        time_series_start = self.inputs["TimeSeriesStart"].read().values
        self.outputs["ConLiqWatTgtAvg"].set_values(
            np.ndarray,
            shape=(number_time_steps, deposition_info.values.shape[1]),
            chunks=(min(65536, number_time_steps), 1),
            element_names=(None, deposition_info.element_names[1]),
            offset=(time_series_start, None)
        )
        self.outputs["ConLiqWatTgtAvgHrAvg"].set_values(
            np.ndarray,
            shape=(number_time_steps, deposition_info.values.shape[1]),
            chunks=(min(65536, number_time_steps), 1),
            element_names=(None, deposition_info.element_names[1]),
            offset=(time_series_start, None)
        )
        self.outputs["CntSedTgt1"].set_values(
            np.ndarray,
            shape=(number_time_steps, deposition_info.values.shape[1]),
            chunks=(min(65536, number_time_steps), 1),
            element_names=(None, deposition_info.element_names[1]),
            offset=(time_series_start, None)
        )
        for i, reach in enumerate(deposition_info.element_names[1].get_values()):
            water_concentration = np.zeros(number_time_steps)
            water_concentration_hr = np.zeros(number_time_steps)
            sediment_concentration = np.zeros(number_time_steps)
            with open(os.path.join(output_path, f"R{reach}.csv")) as f:
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
