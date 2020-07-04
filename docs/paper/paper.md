---
title: 'BestiaPop: A Python package for climate data extraction and processing'
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

Climate data is an essential input for crop models to predict crop growth and development using site-specific (point) or gridded climate data. While point data is currently available in MET format, gridded data is provided in NetCDF file format which is difficult to store and convert to an input file readable by APSIM[^1] or other crop models. We developed `Bestiapop` (a spanish word that translates to *pop beast*), a Python package which allows model users to automatically download SILO's (Scientific Information for Land Owners) gridded climate data in MET file format that can then be inputted by APSIM for crop modelling predictions. The package offers the possibility to select a range of grids (5 km × 5 km resolution) and years producing various types of output files (csv and MET). Although the code downloads data from the SILO[^2] database, it could be applied to other climate data sources e.g. NASA POWER[^3] as was implemented in R using APSIM CRAN[^4]. `Bestiapop` was designed to be used by researchers interested in crop modelling (e.g. [@Ojeda:2020]).The combination of speed, design, and support for gridded climate data extraction and analysis in `Bestiapop` will enable exciting scientific explorations on climate change analysis and could be potentially extended to other models such as ecological and hydrological models.

[^1]: https://www.apsim.info
[^2]: https://www.longpaddock.qld.gov.au/silo/gridded-data/
[^3]: https://power.larc.nasa.gov/
[^4]: https://cran.r-project.org/web/packages/APSIM/APSIM.pdf

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