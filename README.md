# Open Power System Data: Renewable energy power plants

## About this notebook


This Jupyter Notebook is part of the "Open Power System Data" Project and written in Python 3. The aim is to extract, merge, clean and verify different sources with data from renewable energy (RE) power plants in Germany. The data are downloaded from two different sources:

* [Netztransparenz.de](https://www.netztransparenz.de/de/Anlagenstammdaten.htm) - Information platform from the german TSOs
> In Germany historically all data has been published mandatorily by the four TSOs (50Hertz, Amprion, Tennet, TransnetBW). This obligation expired in August 2014, nonetheless the TSO reported until the end of 2014 and issued another update in November 2015 (which is used in this script).

* [BNetzA](http://www.bundesnetzagentur.de/) - The German Federal Network Agency for Electricity, Gas, Telecommunications, Posts and Railway 
> Since August 2014 the BNetzA is responsible to publish the renewable power plants register. The legal framework for the register is  specified in the [EEG 2014 (German)](http://www.gesetze-im-internet.de/eeg_2014/) [(English)](http://www.res-legal.eu/search-by-country/germany/single/s/res-e/t/promotion/aid/feed-in-tariff-eeg-feed-in-tariff/lastp/135/). Furthermore all power plants are listed in a new format: two separate MS-Excel and CSV files for roof-mounted PV power plants ["PV-Datenmeldungen"](http://www.bundesnetzagentur.de/cln_1422/DE/Sachgebiete/ElektrizitaetundGas/Unternehmen_Institutionen/ErneuerbareEnergien/Photovoltaik/DatenMeldgn_EEG-VergSaetze/DatenMeldgn_EEG-VergSaetze_node.html) and all other renewable power plants [" Anlagenregister"](http://www.bundesnetzagentur.de/cln_1412/DE/Sachgebiete/ElektrizitaetundGas/Unternehmen_Institutionen/ErneuerbareEnergien/Anlagenregister/Anlagenregister_Veroeffentlichung/Anlagenregister_Veroeffentlichungen_node.html) ).

This Jupyter Notebook downlads and extracts the original data from the sources and merges them (Part 1). <br>
Part 2 subsequently checks, validates the list of renewable power plants and creates CSV/XLSX/SQLite files. It also generates a daily timeseries of cumulated installed capacities by generation types.


## License

* This notebook is published under the GNU GPL v3 license. http://www.gnu.org/licenses/gpl-3.0.en.html.
* This notebook is developed by the project Open Power System Date (OPSD.) http://open-power-system-data.org/


## Links to the other Notebooks

* [Part 1: Download and Processing](https://github.com/Open-Power-System-Data/datapackage_renewable_power_plants/blob/master/download_and_process.ipynb)
* [Part 2: Validation and Output (power plant list and timeseries)](https://github.com/Open-Power-System-Data/datapackage_renewable_power_plants/blob/master/validation_and_output.ipynb)
