# Astronomy Data

This page gives an overview of the available astronomical data, and how it is used, in the [Sonification Suite](https://sonificationsuite.ncl.ac.uk) domain for Planetaria and Astronomy Communicators.

## Light Curves 
 These data are stellar light curves. They are in the format of a star's flux (i.e., measured brightness) as a function of time. The units of time are in days. The flux values are not in physical units. However, as the sonification approach uses the values to scale the sound, relative to the data itself, the units are arbitrary. 
 
 These data are presented in a form that is univariate, i.e., there is only one variable (star brightness) changing with time. Therefore, the expectation is that for the purposes of the sonification, time in the data is mapped to time in the sonification. The flux values are expected to be mapped to an evolving sound parameter, such as pitch, volume, cut off frequency etc. For more information on how parameter mapping of sound works see: **GEORGE GIVE LINK**

### Suggested Examples
The Audio Universe team have curated some example light curves that we think might be interesting for astronomy communicators. These are available on the first page of the Light Curve section of the Suite (below the search box). We have grouped these into different stellar classes. For a quick visualisation of these data, you can click the graph icon on the top left of the buttons provided for each example star. If you wish to use the example, you can simply click no the example's button and you will be taken directly to the Suite's Data Refinement step. You can then proceed with the standard sonification steps. See: **GEORGE GIVE LINK**

### User query

#### Searching for a star
In the Suite you can query for stellar lightcurve data.

You can search for a star in the provided search box. This search makes use of the [astroquery.simbad](https://astroquery.readthedocs.io/en/latest/simbad/simbad.html) packagage. In practise, this means that you can search for a star based on it (various) names, or mission identifiers, as resolved by [SIMBAD's basic query](https://simbad.cds.unistra.fr/simbad/sim-fbasic). For example, the available data for Kepler 7 can be found via searching for any of the following terms:

* Kepler-7 or Kepler 7 (which is a popular name)
* KIC 5780885 (which is the Kepler mission unique identifier)
* Gaia DR3 2102117871259036672 (which is a GAIA mission identifier)
* TIC 121660904 (which is the TESS identifier)
* etc. see the full list of identifiers on [SIMBAD](https://simbad.cds.unistra.fr/simbad/sim-basic?Ident=Kepler+7&submit=SIMBAD+search) 

#### Table of available data products
We make use of the [lightkurve](https://lightkurve.github.io/lightkurve/) package to perform the search query for lightcurve data. For detailed information about the query you can look at their documentation. We only provide brief details here. 

The query searches publically available light curve data from the Kepler, K2, and TESS missions that are stored on the [Mikulski Archive for Space Telescopes (MAST)](https://archive.stsci.edu/) archive. If you wish, you can customise which of the three missions you want to include in the search using the options button next to the search box. The available datasets are returned to the interface in the form of a table.

Individual observational sectors for each of the missions are provided (i.e., an individual visit by the telescope). These are returned in the table, with one observation per row. We have ordered these in our best guess of which might be the most useful to a typical user (e.g., putting the most recent Kepler data at the top). However, the user should inspect the datasets to find the best one for their own purposes. 

You can have a quick visual preview of the data by clicking the "View Plot" button. Once you have chosen the dataset you want to sonify, you can click "Sonify" in the appropriate column. This will then take you to the Suite's Data Refine step. Here you can trim the data, choose how to deal with empty data value, and/or smooth the data. See: **GEORGE GIVE LINK**

We note that you are not provided with joined datasets of all repeat observations of the same star. This is due to the challenges in automating this in a sensible and consistent way. If you wish to use a light curve which has joined multiple observations over a longer period of time, or any other light curve data (e.g., which has had additional cleaning/processing beyond that provided in the Suite), you will need to upload your own dataset in the form of comma separated table with the columns of time and flux. You can do this by clicking the relevant button on the first page of the Light Curve section of the Suite. 

**Table Columns**

* Mission: Which mission the data is from. 
* Exposure: The total exposure time of the observation. 
* Pipeline: Which pipeline was used to process the data (this is most relevant for TESS data, for which different choices are available)
* Year: Year of observation
* Period: Which observation visit are the data from (called quarters for Kepler, sectors for TESS, and campaigns for K2)

#### Summary of the different available mission data

**TESS**: Each standard TESS observing sector lasts for roughly 27.4 days. This is split into two spacecraft orbits of around 13.7 days each, with a brief pause for data download from the spacecraft. This means that you can expect to see a gap in the middle of every dataset. Once selected, you can choose to trim the data to avoid these gaps if you wish. Observation cadences vary from 20 seconds to 30 minutes depending on the target selection and mission year. There are different pipelines for the TESS data. QLP stands for "Quick Look Pipeline", which is available for all of the brightest stars. It is typically not the best option, as it was designed to quickly look at every available star. SPOC and TESS-SPOC are relatively similar (at least for our purposes) and produce highly precise, systematically corrected light curves for a select sample of priority stars.

**Kepler**: Each observing quarter lasts around 90 days (for the observations taking during Kepler Quarter 02 and later). The time resolution is 29.4 minutes. Around every 32 days within a quarter, science collection paused for roughly 24 hours so the telescope could downlink its stored memory. This means you will find gaps in the data. Once selected, you can choose to trim the data to avoid these gaps if you wish.

**K2**: K2 was performed on the Kepler spacecraft as a secondary survey. These are observed in campaigns rather than quarters. A standard K2 campaign lasted approximately 75 to 80 days. As for Kepler, the time resolution is 29.4 minutes, and there are gaps in the data around every 32 days. 

## Constellations

The Suite comes packaged with a table of star data and their associated constellations or asterism. Version 1 of the Suite focusses on automatically providing Western constellations/asterisms. However, it will also be possible to upload your own custom constellation. This will be helpful for different sents of Constellations, or if you do not agree on the exact subset of stars included in the database we have used. 

The star data used in the Suite comes from the HYG Database v4.2 - a compilation of the Hipparcos (Perryman et al., 1997, Astronomy and Astrophysics, 323, L49-L52), Yale Bright Star (5th Edition; Dorrit Hoffleit 1964), and Gliese catalogs (3rd Edition; Gliese et al. 1991), created by David Nash. This is available at [online](https://codeberg.org/astronexus/hyg/src/branch/main/data/hyg). 

This list of constellations and asterisms (and how to draw the lines between the stars) comes from the [Stellarium Western Sky Culture](https://github.com/Stellarium/stellarium-skycultures/tree/master/western) set. 

### Choosing a constellation and a subset of stars
In the Suite you can choose a constellation from the the dropdown menu (also searchable) which is on the landing page of the Constellations section of the Suite. You can then choose between three options:

1. **A stick figure**: which will select the subset of stars within the chosen constellation/asterism shapes, as determined by Stellarium's file (see above)
2. **A boundary**: which will select all stars within a constellation boundary, as determined by the HYG dataset (see above). This is not applicable for asterisms (e.g., the Summer Tringle, as they can cross multiple constellations). In this case you can choose how many stars you want to include (all of them is probably too many!). This subset is selected on the brightest stars (i.e., based on the apparent visual magnitudes). For example, if you select 50 stars, you will be returned the 50 stars within the constellation bounday which have the smallest (brightest) visual magnitudes
3. **Custom order**: As for "stick figure", this uses the subset of stars within the constellation/asterism shapes determined by Stellarium's file. This option is there to let you choose a custom order of the sounds in the sonification. Otherwise, the order will need to be determined by some property of the star (such as its magnitude or RA). It is important to note that if you choose a custom order, this will over-rule any other choices you make in the following steps to map star properties to time. See: **GEORGE GIVE LINK**

### Star properties

The full HYG dataset contains a lot of information about each star, with full details of all the properties available [on this page](https://codeberg.org/astronexus/hyg/src/branch/main/data/hyg). For the current purposes of the Suite, we only provide to the user a subset of the available star properties to map onto sound parameters. These are:

* **RA** and **DEC**: star positions in the J2000 epoch. 
* **Magnitude**: The star visual apparent magnitudes (where smaller values mean brighter).
* **Distance**: The distance to the star from Earth (in parsecs).
* **Proper Motion (RA)** and **Proper Motion (DEC)**: The measured proper motions of the stars in RA and DEC, in milliarcseconds per year.
* **Absolute Magnitude**: The star's absolute visual magnitude (its apparent magnitude from a distance of 10 parsecs; again smaller means brighter)
* **Colour**: The star's colour. Specifically, this is the star's color index (blue magnitude - visual magnitude). The larger the number, the redder the star.

As with all datasets, there may be missing values (especially for fainter stars). These can be dealt with on the Data Refinement step. See: **GEORGE GIVE LINK**

In addition to these data, we make use of a **display name** for each star, which can be used to identify specific stars (e.g., when choosing a custom order or when downloading the table which shows how the data were mapped to the sound properties in the final step of the sonification). This display name is produced by taking our "favourite" star identifier from the HYG data set, based on the following priority order: (1) Proper name; (2) Flamsteed Designation; (3) Bayer designation; (4) HIP id (Hipparcos ID); (5) HD (Henry Draper catalogue ID).

### Constellation Location for "Place on Dome" Feature

If the user wishes to place the constellation sonification in the correct location in a speaker system, the user can make use of the "Place on Dome" feature. For example, if you want to portray Orion during a planetarium show, and it is currently on the user's left. For a user chosen location and time, the altitude and azimuth of the constellation is calculated by the [SkyField](https://rhodesmill.org/skyfield/) package. The user can also input the direction that the observer would be facing (the Orientation). This is crucial for mapping the sounds to positions, such that stars on the observer's left, are heard on the left in the sonification etc. Note that the local timezone to the specified location is used to perform this calculation. A rough RA and DEC of the constellation is used for this constellation by taking the average position of the stars. 

## Night Sky

The Suite allows you to sonify all of the stars visible above a specified location, at a specified time. A user of the Suite can input their location (either using a search for a placename, or using an exact longititude and latitude position). They can also input the exact time that they want the sky field to be calculated for. Note that the local timezone to the specified location is used to perform this calculation. The user can also input the direction that the observer would be facing (the Orientation). This is crucial for mapping the sounds to positions, such that stars on the obersver's left, are heard on the left in the sonification etc. 

For the chosen location and time, the altitude and azimuth of stars are calculated by the [SkyField](https://rhodesmill.org/skyfield/) package. This also determines which stars are above the horizon (and therefore automatically included in the sonification). The location of these stars <em>with respect to the observer</em> (i.e., in degrees around the horizon for the direction of facing), is determined by the user's chosen Orientation. Once a time, location, and orientation has been chosen, the user can reduce the number of stars to include in the sonification by filtering by apparent visible magnitude. We make use of SkyField to also do this step, which obtains the magnitude properties from the [Hipparcos catalogue](https://rhodesmill.org/skyfield/stars.html#the-hipparcos-catalog). 

The magnitude, colour, altitude and azimuth of the visible stars are then made available to the user during the sonification mapping step. The magnitudes and colours (blue magnitude - visual magnitude) also come from the same Hipparocs catalogue. As always, smaller magnitudes mean visibly brighter objects and high colour values mean redder objects. 
