---
title: 'BestiaPop: A Python package for gridded climate data extraction and processing'
tags:
  - weather data
  - model inputs
  - APSIM modelling
  - MET file
  - Python
authors:
  - name: Jonathan J. Ojeda^[1,*]
    orcid: 0000-0002-9172-0059
    affiliation: 1
  - name: Diego Perez
affiliations:
 - name: Crop model developer, Tasmanian Institute of Agriculture, University of Tasmania
   index: 1
 - name: Independent Data Analytics Specialist
   index: 2
date: 04 July 2020
bibliography: paper.bib
---

# Summary

Climate data is an essential input for crop models to predict crop growth and development using site-specific (point) or gridded climate data. While point data is currently available in MET format, gridded data is provided in NetCDF file format which is difficult to store and convert to an input file readable by the Agricultural Production Systems sIMulator (APSIM)[^1] or other crop models. We developed `Bestiapop` (a spanish word that translates to *pop beast*), a Python package which allows model users to automatically download SILO's (Scientific Information for Land Owners) gridded climate data in MET file format that can then be inputted by APSIM for crop modelling predictions. The package offers the possibility to select a range of grids (5 km × 5 km resolution) and years producing various types of output files (csv and MET). Although the code downloads data from the SILO[^2] database, it could be applied to other climate data sources e.g. NASA POWER[^3] as was implemented in R using APSIM CRAN[^4]. `Bestiapop` was designed to be used by researchers interested in crop modelling.The combination of speed, design, and support for gridded climate data extraction and analysis in `Bestiapop` will enable exciting scientific explorations on climate change analysis and could be potentially extended to other models such as ecological and hydrological models.

# Introduction

Crop models need climate data to predict crop growth and development. The spatial resolution of this datasets ranges from site-specific (point) or gridded climate data at different spatial and temporal resolutions. A previous study integrated an automatic tool to download point climate data from NASA POWER API in R programming language with crop models [@Sparks:2018]. For Australia, point climate data is currently available in a readily APSIM format, however, gridded climate data is storage in very large NetCDF files which are difficult to convert to an input file readable by APSIM or other crop models. Although some APSIM studies used gridded climate data across Australia to simulate crop yield [@Ojeda:2020;@Zhao2013] and irrigation water requirements [@Ojeda:2020], there is no available tool to download and format these gridded data in an APSIM format. Here we present the development of `BestiaPop`, a Python package which provides functionality to interface with the SILO's (Scientific Information for Land Owners) gridded datasets [@Jeffrey:2001] hosted on Amazon Web Services under the AWS Public Data Program for reproducible data retrieval using Python. SILO’s gridded climate data are freely available for download via a web interface and contains continuous daily climate data for Australia from 1889 to present. The grid spans 112°E to 154°E, 10°S to 44°S with resolution 0.05° latitude by 0.05° longitude (approximately 5 km × 5 km).

# About APSIM and MET files

The Agricultural Production Systems sIMulator (APSIM) is internationally recognised as a highly advanced platform for modelling and simulation of agricultural systems. It contains a suite of modules that enable the simulation of systems for a diverse range of crop, animal, soil, climate and management interactions. APSIM is undergoing continual development, with new capability added to regular releases of official versions. Its development and maintenance is underpinned by rigorous science and software engineering standards. The APSIM Initiative[^5] has been established to promote the development and use of the science modules and infrastructure software of APSIM.

The APSIM Met module provided daily meteorological information to all modules within an APSIM simulation. The APSIM Met Module requires parameters to specify the climate of the site for each APSIM time step. This information is included in a MET file[^6]. APSIM MET files consist of a section name, which is always *weather.met.weather*, several constants consisting of *name = value*, followed by a headings line, a units line and then the data. Spacing in the file is not relevant. Comments can be inserted using the ! character. At a minimum three constants must be included in the file: **latitude**, **tav** and **amp**[^7]. The last two of these refer to the annual average ambient temperature and annual amplitude in mean monthly temperature. The MET file must also have a year and day column (or date formatted as *yyyy/mm/dd*), solar radiation (*MJ/m2*), maximum temperature (*&deg;C*), minimum temperature (*&deg;C*) and rainfall (*mm*). The column headings to use for these are year and day (or date), radn, maxt, mint, rain. Other constants or columns can be added to the file. These then become available to APSIM as variables that can be reported or used in manager script.

# Benefits of Bestiapop over current SILO Data Portal tools

SILO Gridded Data Portal provides the option to download MET files for a single combination of latitude and longitude at the time. In order to download climate data from more than one combination of latitude and longitude, users needs to download an entire NetCDF file. During this process there are two selection fields in which the user can select one year and one daily climate variable at the time for all latitudes and longitudes combinations across Australia. Therefore, there is not option to select multiple years and variables at the same time. Another constraint is that the downloaded NetCDF file (only one combination of year and climate variable) is considerably high in size (approximately 410 MB). If a user wants to access long-term climate data (as is usual for crop modelling purposes) they must manually download each annual NetCDF file per variable and they must have enough local storage space to save those datasets. This makes the selection of multiple years and climate variables a frustrating process under the current SILO tools. The SILO Gridded Data Portal works well for quick access or a single use. However, there are several cases in which the SILO Data Portal is not ideal:

* Requests for long-term climate datasets with more than one climate variable.

* Requests for climate data from specific combinations of latitudes and longitudes.

* Requests for newly released data that are identical to previous requests.

`Bestiapop` addresses each of these issues by making the SILO Data Portal API accessible with Python code. This allows the user to automatically create MET files for several year, variable and geographical combinations in a faster way than the current available SILO Data Portal options and to execute a climate data request repeatedly to access new data with the same query.

# Bestiapop functionality

# Can I use Bestiapop to generate climate files for other process-based crop models?

So far, the code is producing CSV or MET files to be directly used by APSIM, however, it also could be applied to produce input climate data for other crop models such as DSSAT[^8] and STICS[^9]. Decision Support System for Agrotechnology Transfer (DSSAT) is a software application program that comprises dynamic crop growth simulation models for over 40 crops. DSSAT is supported by a range of utilities and apps for weather, soil, genetic, crop management, and observational experimental data, and includes example data sets for all crop models. The STICS (Simulateur mulTIdisciplinaire pour les Cultures Standard, or multidisciplinary simulator for standard crops) model is a dynamic, generic and robust model aiming to simulate the soil-crop-atmosphere system.

[^1]: https://www.apsim.info
[^2]: https://www.longpaddock.qld.gov.au/silo/gridded-data/
[^3]: https://power.larc.nasa.gov/
[^4]: https://cran.r-project.org/web/packages/APSIM/APSIM.pdf
[^5]: https://www.apsim.info/about-us/
[^6]: https://www.apsim.info/documentation/model-documentation/infrastructure-and-management-documentation/met/
[^7]: https://www.apsim.info/wp-content/uploads/2019/10/tav_amp-1.pdf
[^8]: https://dssat.net/
[^9]: https://www6.paca.inrae.fr/stics_eng/About-us/Stics-model-overview

# Acknowledgements

We acknowledge contributions from Ehsan Eyshi Rezaei and Holger Meinke during the genesis of this project.

# References

@article{ojeda2020effects,
  title={Effects of soil-and climate data aggregation on simulated potato yield and irrigation water requirement},
  author={Ojeda, Jonathan J and Rezaei, Ehsan Eyshi and Remenyi, Tomas A and Webb, Mathew A and Webber, Heidi A and Kamali, Bahareh and Harris, Rebecca MB and Brown, Jaclyn N and Kidd, Darren B and Mohammed, Caroline L and others},
  journal={Science of The Total Environment},
  volume={710},
  pages={135589},
  year={2020},
  publisher={Elsevier}
}