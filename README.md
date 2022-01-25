![Update SDRs](https://github.com/ONEcampaign/sdr_tracker/actions/workflows/update_sdrs.yml/badge.svg)

# **Special Drawing Rights (SDR) Tracker**
This repository contains data and scripts powering ONE's [SDR Tracker](https://www.one.org/africa/issues/covid-19-tracker/explore-sdrs/)

## Repository Structure and Information

This repository contains data and scripts to create the csv file powering the flourish visualization for the tracker. Python (>=3.7) is required and additional packages required are listed under `requirements.txt`. The main purpose of the repository is to update the SDR tracker with data extracted from the [IMF](https://www.imf.org/external/np/fin/tad/extsdr1.aspx) on SDR annoucements on holdings and allocations, and ONE's [qualitative analysis](https://docs.google.com/spreadsheets/d/1fQi941fLyk2zSyGRRkRNhct8OZU2SXGCXmDOhH4XD1c/edit#gid=0). The update can be manually triggered through the `Actions` tab.

The repository includes the following subfolders:
- `output`: contains the CSV that powers the tracker (`sdr.csv`) and a CSV tracking each update.
- `scripts`: scripts for extracting and transforming data. `imf.py` queries the imf api to extract GDP data. `download_sdr.py` extracts the latest SDR annoucements from the [IMF](https://www.imf.org/external/np/fin/tad/extsdr1.aspx).`sdr_tracker.py` created the final csv that powers the tracker, incuding concordance of countries, calculating columns including %gdp, and creating html code for popups and panels. Additionally, a `config.py` file manages file paths to different folders; `utils.py` contains helper functions for a variety of frequently-used tasks
- `glossaries`: Found inside the `scripts`  folder. `glossaries` contains a json file for Flourish geometries for Africa. Other intermediate files including map templates and WEO data is saved in this folder

## Website and Charts

The SDR tracker can be found here: https://www.one.org/africa/issues/covid-19-tracker/explore-sdrs/

## Sources 

- SDR annoucements can be found here: https://www.imf.org/external/np/fin/tad/extsdr1.aspx
- Qualitative data and annoucements made on 23 August 2021 can be found on this [google sheet](https://docs.google.com/spreadsheets/d/1fQi941fLyk2zSyGRRkRNhct8OZU2SXGCXmDOhH4XD1c/edit#gid=0).
- GDP values (2021 values) used to calculate SDR values as a % of GDP are taken from the October 2021 [World Economic Outlook](https://www.imf.org/en/Publications/WEO/weo-database/2021/October).
