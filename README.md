## Table of Contents
* [About the project](#about-the-project)
  * [Built With](#built-with)
* [Getting Started](#getting-started)
  * [Prerequisites](#prerequisites)
  * [Installation](#installation)
* [Usage](#usage)
  * [Inputs](#inputs)
  * [Outputs](#outputs)
* [Roadmap](#roadmap)
* [Contributing](#contributing)
* [License](#license)
* [Contact](#contact)
* [Acknowledgements](#acknowledgements)


## About the project
A component that encapsulates the CascadeToxswa module for usage within the Landscape Model.  
This is an automatically generated documentation based on the available code and in-line documentation. The current
version of this document is from 2021-08-10.  

### Built with
* Landscape Model core version 1.5.5
* CMF-TOXWA_coupling version 0.5 (see `https://doi.org/10.18174/547183` for details)


## Getting Started
The component can be used in any Landscape Model based on core version 1.5.5 or newer. See the Landscape Model
core's `README` for general tips on how to add a component to a Landscape Model.

### Prerequisites
A model developer that wants to add the `CascadeToxswa` component to a Landscape Model needs to set up the general 
structure for a Landscape Model first. See the Landscape Model core's `README` for details on how to do so.

### Installation
1. Copy the `CascadeToxswa` component into the `model\variant` sub-folder.
2. Make use of the component by including it into the model composition using `module=CascadeToxswa` and 
   `class=CascadeToxswa`. 


## Usage
The following gives a sample configuration of the `CascadeToxswa` component. See [inputs](#inputs) and 
[outputs](#outputs) for further details on the component's interface.
```xml
<CascadeToxswa module="CascadeToxswa" class="CascadeToxswa" enabled="$(RunCascadeToxswa)">
    <ProcessingPath>$(_MCS_BASE_DIR_)\$(_MC_NAME_)\processing\fate\cascade</ProcessingPath>
    <Hydrography>
        <FromOutput component="LandscapeScenario" output="hydrography" />
    </Hydrography>
    <SuspendedSolids type="float" unit="g/m&#179;">15</SuspendedSolids>
    <Reaches>
        <FromOutput component="DepositionToReach" output="Reaches" />
    </Reaches>
    <TimeSeriesStart>
        <FromOutput component="Hydrology" output="TimeSeriesStart" />
    </TimeSeriesStart>
    <WaterDischarge>
        <FromOutput component="Hydrology" output="Flow" />
    </WaterDischarge>
    <WaterDepth>
        <FromOutput component="Hydrology" output="Depth" />
    </WaterDepth>
    <Temperature>
        <FromOutput component="Weather" output="TEMPERATURE_AVG" />
    </Temperature>
    <MassLoadingSprayDrift>
        <FromOutput component="DepositionToReach" output="Deposition" />
    </MassLoadingSprayDrift>
    <MolarMass type="float" unit="g/mol">$(MolarMass)</MolarMass>
    <SaturatedVapourPressure type="float" unit="Pa">$(SaturatedVapourPressure)</SaturatedVapourPressure>
    <ReferenceTemperatureForSaturatedVapourPressure type="float" unit="&#176;C">
        $(Temp0)
    </ReferenceTemperatureForSaturatedVapourPressure>
    <MolarEnthalpyOfVaporization type="float" unit="kJ/mol">
        $(MolarEnthalpyOfVaporization)
    </MolarEnthalpyOfVaporization>
    <SolubilityInWater type="float" unit="mg/l">$(SolubilityInWater)</SolubilityInWater>
    <ReferenceTemperatureForWaterSolubility type="float" unit="&#176;C">
        $(Temp0)
    </ReferenceTemperatureForWaterSolubility>
    <MolarEnthalpyOfDissolution type="float" unit="kJ/mol">
        $(MolarEnthalpyOfDissolution)
    </MolarEnthalpyOfDissolution>
    <DiffusionCoefficient type="float" unit="m&#178;/d">$(DiffusionCoefficient)</DiffusionCoefficient>
    <ReferenceTemperatureForDiffusion type="float" unit="&#176;C">$(Temp0)</ReferenceTemperatureForDiffusion>
    <HalfLifeTransformationInWater type="float" unit="d">$(DT50sw)</HalfLifeTransformationInWater>
    <TemperatureAtWhichHalfLifeInWaterWasMeasured type="float" unit="&#176;C">
        $(Temp0)
    </TemperatureAtWhichHalfLifeInWaterWasMeasured>
    <MolarActivationEnthalpyOfTransformationInWater type="float" unit="kJ/mol">
        $(MolarActivationEnthalpyOfTransformationInWater)
    </MolarActivationEnthalpyOfTransformationInWater>
    <HalfLifeTransformationInSediment type="float" unit="d">$(DT50sed)</HalfLifeTransformationInSediment>
    <TemperatureAtWhichHalfLifeInSedimentWasMeasured type="float" unit="&#176;C">
        $(Temp0)
    </TemperatureAtWhichHalfLifeInSedimentWasMeasured>
    <MolarActivationEnthalpyOfTransformationInSediment type="float" unit="kJ/mol">
        $(MolarActivationEnthalpyOfTransformationInSediment)
    </MolarActivationEnthalpyOfTransformationInSediment>
    <CoefficientForEquilibriumAdsorptionInSediment type="float" unit="l/kg" eval="true">
        $(KOC) / 1.742
    </CoefficientForEquilibriumAdsorptionInSediment>
    <ReferenceConcentrationInLiquidPhaseInSediment type="float" unit="mg/l">
        $(ReferenceConcentrationForKOC)
    </ReferenceConcentrationInLiquidPhaseInSediment>
    <FreundlichExponentInSediment type="float" unit="1">
        $(FreundlichExponentInSedimentAndSuspendedParticles)
    </FreundlichExponentInSediment>
    <CoefficientForEquilibriumAdsorptionOfSuspendedSoils type="float" unit="l/kg" eval="true">
        $(KOC) / 1.742
    </CoefficientForEquilibriumAdsorptionOfSuspendedSoils>
    <ReferenceConcentrationForSuspendedSoils type="float" unit="mg/l">
        $(ReferenceConcentrationForKOC)
    </ReferenceConcentrationForSuspendedSoils>
    <FreundlichExponentForSuspendedSoils type="float" unit="1">
        $(FreundlichExponentInSedimentAndSuspendedParticles)
    </FreundlichExponentForSuspendedSoils>
    <CoefficientForLinearAdsorptionOnMacrophytes type="float" unit="l/kg">
        0
    </CoefficientForLinearAdsorptionOnMacrophytes>
    <NumberWorkers type="int">$(CascadeToxswaWorkers)</NumberWorkers>
</CascadeToxswa>
```

### Inputs
#### ProcessingPath
The working directory for the module. It is used for all files prepared as module inputs
or generated as module outputs.  
`ProcessingPath` expects its values to be of type `str`.
Values of the `ProcessingPath` input may not have a physical unit.
Values have to refer to the `global` scale.

#### Hydrography
The spatial delineation of the hydrographic features in the simulated landscape. This
input basically represents the flow-lines used during preparation of the hydrology. The hydrography is
consistently for all components of the Landscape Model subdivided into individual segments (*reaches*).  
`Hydrography` expects its values to be of type `str`.
Values of the `Hydrography` input may not have a physical unit.
Values have to refer to the `global` scale.

#### SuspendedSolids
The density of suspended solids that applies to all reaches.  
`SuspendedSolids` expects its values to be of type `float`.
The physical unit of the `SuspendedSolids` input values is `g/m³`.
Values have to refer to the `global` scale.

#### Reaches
The numeric identifiers for individual reaches (in the order of the `Hydrography` input)
that apply scenario-wide.  
`Reaches` expects its values to be of type `ndarray`.
Values of the `Reaches` input may not have a physical unit.
Values have to refer to the `space/reach` scale.

#### TimeSeriesStart
The first time step for which input data is provided. This is also the time step of where
the CascadeToxswa simulation starts.  
`TimeSeriesStart` expects its values to be of type `date`.
Values of the `TimeSeriesStart` input may not have a physical unit.
Values have to refer to the `global` scale.

#### WaterDischarge
The amount of water that leaves a reach within a time step.  
`WaterDischarge` expects its values to be of type `ndarray`.
The physical unit of the `WaterDischarge` input values is `m³/s`.
Values have to refer to the `time/hour, space/reach` scale.

#### WaterDepth
The depth of the water body measured from the surface to the lowest point of the 
cross-section profile.  
`WaterDepth` expects its values to be of type `ndarray`.
The physical unit of the `WaterDepth` input values is `m`.
Values have to refer to the `time/hour, space/reach` scale.

#### Temperature
The average daily air temperature. If hourly data are available, then the daily average
temperature should be calculated from these hourly values. However, if only maximum and minimum daily
temperature are available, these two values can be averaged.  
`Temperature` expects its values to be of type `ndarray`.
The physical unit of the `Temperature` input values is `°C`.
Values have to refer to the `time/day` scale.

#### MassLoadingSprayDrift
The average drift deposition onto the surface of a water body.  
`MassLoadingSprayDrift` expects its values to be of type `ndarray`.
The physical unit of the `MassLoadingSprayDrift` input values is `mg/m²`.
Values have to refer to the `time/day, space/reach` scale.

#### MolarMass
The molar mass of the substance depositing at the water body surface.  
`MolarMass` expects its values to be of type `float`.
The physical unit of the `MolarMass` input values is `g/mol`.
Values have to refer to the `global` scale.

#### SaturatedVapourPressure
The saturated vapor pressure of the substance depositing at the water body surface.  
`SaturatedVapourPressure` expects its values to be of type `float`.
The physical unit of the `SaturatedVapourPressure` input values is `Pa`.
Values have to refer to the `global` scale.

#### ReferenceTemperatureForSaturatedVapourPressure
The temperature to which the value of the `SaturatedVaporPressure` applies.  
`ReferenceTemperatureForSaturatedVapourPressure` expects its values to be of type `float`.
The physical unit of the `ReferenceTemperatureForSaturatedVapourPressure` input values is `°C`.
Values have to refer to the `global` scale.

#### MolarEnthalpyOfVaporization
The molar vaporization enthalpy of the substance depositing at the water body surface.  
`MolarEnthalpyOfVaporization` expects its values to be of type `float`.
The physical unit of the `MolarEnthalpyOfVaporization` input values is `kJ/mol`.
Values have to refer to the `global` scale.

#### SolubilityInWater
The water solubility of the substance depositing at the water body surface.  
`SolubilityInWater` expects its values to be of type `float`.
The physical unit of the `SolubilityInWater` input values is `mg/l`.
Values have to refer to the `global` scale.

#### ReferenceTemperatureForWaterSolubility
The temperature to which the value of the `SolubilityInWater` applies.  
`ReferenceTemperatureForWaterSolubility` expects its values to be of type `float`.
The physical unit of the `ReferenceTemperatureForWaterSolubility` input values is `°C`.
Values have to refer to the `global` scale.

#### MolarEnthalpyOfDissolution
The molar dissolution enthalpy of the substance depositing at the water body surface.  
`MolarEnthalpyOfDissolution` expects its values to be of type `float`.
The physical unit of the `MolarEnthalpyOfDissolution` input values is `kJ/mol`.
Values have to refer to the `global` scale.

#### DiffusionCoefficient
The diffusion coefficient of the substance depositing at the water body surface.  
`DiffusionCoefficient` expects its values to be of type `float`.
The physical unit of the `DiffusionCoefficient` input values is `m²/d`.
Values have to refer to the `global` scale.

#### ReferenceTemperatureForDiffusion
The temperature to which the value of the `DiffusionCoefficient` applies.  
`ReferenceTemperatureForDiffusion` expects its values to be of type `float`.
The physical unit of the `ReferenceTemperatureForDiffusion` input values is `°C`.
Values have to refer to the `global` scale.

#### HalfLifeTransformationInWater
The half-life transformation time in water of the substance depositing at the water body 
surface.  
`HalfLifeTransformationInWater` expects its values to be of type `float`.
The physical unit of the `HalfLifeTransformationInWater` input values is `d`.
Values have to refer to the `global` scale.

#### TemperatureAtWhichHalfLifeInWaterWasMeasured
The temperature to which the value of the `HalfLifeTransformationInWater` applies.  
`TemperatureAtWhichHalfLifeInWaterWasMeasured` expects its values to be of type `float`.
The physical unit of the `TemperatureAtWhichHalfLifeInWaterWasMeasured` input values is `°C`.
Values have to refer to the `global` scale.

#### MolarActivationEnthalpyOfTransformationInWater
The molar activation enthalpy relating to the transformation in water.  
`MolarActivationEnthalpyOfTransformationInWater` expects its values to be of type `float`.
The physical unit of the `MolarActivationEnthalpyOfTransformationInWater` input values is `kJ/mol`.
Values have to refer to the `global` scale.

#### HalfLifeTransformationInSediment
The half-life transformation time in sediment of the substance depositing at the water 
body surface.  
`HalfLifeTransformationInSediment` expects its values to be of type `float`.
The physical unit of the `HalfLifeTransformationInSediment` input values is `d`.
Values have to refer to the `global` scale.

#### TemperatureAtWhichHalfLifeInSedimentWasMeasured
The temperature to which the value of the `HalfLifeTransformationInSediment` applies.  
`TemperatureAtWhichHalfLifeInSedimentWasMeasured` expects its values to be of type `float`.
The physical unit of the `TemperatureAtWhichHalfLifeInSedimentWasMeasured` input values is `°C`.
Values have to refer to the `global` scale.

#### MolarActivationEnthalpyOfTransformationInSediment
The molar activation enthalpy relating to the transformation in sediment.  
`MolarActivationEnthalpyOfTransformationInSediment` expects its values to be of type `float`.
The physical unit of the `MolarActivationEnthalpyOfTransformationInSediment` input values is `kJ/mol`.
Values have to refer to the `global` scale.

#### CoefficientForEquilibriumAdsorptionInSediment
The coefficient for equilibrium adsorption in sediment of the substance depositing at 
the water body surface.  
`CoefficientForEquilibriumAdsorptionInSediment` expects its values to be of type `float`.
The physical unit of the `CoefficientForEquilibriumAdsorptionInSediment` input values is `l/kg`.
Values have to refer to the `global` scale.

#### ReferenceConcentrationInLiquidPhaseInSediment
The reference concentration in liquid phase in sediment of the substance depositing at 
the water body surface.  
`ReferenceConcentrationInLiquidPhaseInSediment` expects its values to be of type `float`.
The physical unit of the `ReferenceConcentrationInLiquidPhaseInSediment` input values is `mg/l`.
Values have to refer to the `global` scale.

#### FreundlichExponentInSediment
The Freundlich exponent in sediment of the substance depositing at the water body 
surface.  
`FreundlichExponentInSediment` expects its values to be of type `float`.
The physical unit of the `FreundlichExponentInSediment` input values is `1`.
Values have to refer to the `global` scale.

#### CoefficientForEquilibriumAdsorptionOfSuspendedSoils
The coefficient for equilibrium adsorption of suspended soils.  
`CoefficientForEquilibriumAdsorptionOfSuspendedSoils` expects its values to be of type `float`.
The physical unit of the `CoefficientForEquilibriumAdsorptionOfSuspendedSoils` input values is `l/kg`.
Values have to refer to the `global` scale.

#### ReferenceConcentrationForSuspendedSoils
The reference concentration for suspended soils.  
`ReferenceConcentrationForSuspendedSoils` expects its values to be of type `float`.
The physical unit of the `ReferenceConcentrationForSuspendedSoils` input values is `mg/l`.
Values have to refer to the `global` scale.

#### FreundlichExponentForSuspendedSoils
The Freundlich exponent for suspended particles.  
`FreundlichExponentForSuspendedSoils` expects its values to be of type `float`.
The physical unit of the `FreundlichExponentForSuspendedSoils` input values is `1`.
Values have to refer to the `global` scale.

#### CoefficientForLinearAdsorptionOnMacrophytes
The coefficient for the linear adsorption of the substance on macrophytes.  
`CoefficientForLinearAdsorptionOnMacrophytes` expects its values to be of type `float`.
The physical unit of the `CoefficientForLinearAdsorptionOnMacrophytes` input values is `l/kg`.
Values have to refer to the `global` scale.

#### NumberWorkers
The number of individual worker processes for the CascadeToxswa simulation. Higher values
usually result in a faster processing, but performance will drop if the available processors are 
overloaded with workers. Consider for an optimal value also other processes running on the same 
machine, especially other Monte Carlo runs of the Landscape Model.  
`NumberWorkers` expects its values to be of type `int`.
Values of the `NumberWorkers` input may not have a physical unit.
Values have to refer to the `global` scale.

### Outputs
#### Reaches
The numerical identifiers of the reaches in the order presented by the other outputs. See the 
`Reaches` input for further details on identifiers.  
Values are expectedly of type `list[int]`.
The values apply to the following scale: `space/reach`.
Values have no physical unit.
#### ConLiqWatTgtAvg
The average concentration along the reach at the specified moment in time in the water phase.  
Values are expectedly of type `ndarray`.
Value representation is in a 2-dimensional array.
Dimension 1 spans the number of time steps as given by the [WaterDischarge](#WaterDischarge) input.
Dimension 2 spans the number of reaches as given by the `Reaches` input.
Chunking of the array is for fast retrieval of time series.
Individual array elements have a type of `float`.
The values apply to the following scale: `time/hour, space/base_geometry`.
The physical unit of the values is `g/m³`.
#### CntSedTgt1
The total content in target layer 1 of sediment atb the specified time.  
Values are expectedly of type `ndarray`.
Value representation is in a 2-dimensional array.
Dimension 1 spans the number of time steps as given by the [WaterDischarge](#WaterDischarge) input.
Dimension 2 spans the number of reaches as given by the `Reaches` input.
Chunking of the array is for fast retrieval of time series.
Individual array elements have a type of `float`.
The values apply to the following scale: `time/hour, space/base_geometry`.
The physical unit of the values is `g/kg`.


## Roadmap
The following changes will be part of future `CascadeToxswa` versions:
* Replace shapefile input
([#1](https://gitlab.bayer.com/aqrisk-landscape/cascadetoxswa-component/-/issues/1))
* Rename Reaches input or output 
([#3](https://gitlab.bayer.com/aqrisk-landscape/cascadetoxswa-component/-/issues/3))


## Contributing
Contributions are welcome. Please contact the authors (see [Contact](#contact)). Also consult the `CONTRIBUTING` 
document for more information.


## License
Distributed under the CC0 License. See `LICENSE` for more information.


## Contact
Sascha Bub (component) - sascha.bub@gmx.de  
Thorsten Schad (component) - thorsten.schad@bayer.com  
Wim Beltman (module) - wim.beltman@wur.nl  
Maarten Braakhekke (module) - maarten.braakhekke@wur.nl  
Louise Wipfler (module) - louise.wipfler@wur.nl  


## Acknowledgements
* [TOXSWA](https://www.pesticidemodels.eu/toxswa)  
