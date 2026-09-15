# User Guide

These pages walk through the complete sonification workflow, from choosing data to generating final audio output.

## Quick Start

The Suite generally follows a 4-step process, each of which is given in more detail below: 

1. Choose your data
2. Optionally refine the data
3. Select a Style
4. Generate your sonification

<small>
  **Note:** The only exception to this workflow is the Data Composer, details of which can be found [here](../data-composer).
</small>

!!! info "In-App Navigation"

    To go back to a previous step, click the corresponding step at the top of the page. For example, if you see **Planetaria > Constellations > Refine > Style** in the header, click on any of those to return to that step.
    
    Alternatively, you can use your browser's back button to go back.

## Step 1: Data :test_tube:

Select the data source you wish to sonify. You can also [import a dataset]() you previously downloaded from the Suite.

### Light Curves

These data are brightness versus time for individual stars (I.E. how a star's brightness changes over time), which are interesting for different types of variable stars or exoplanet transits.

You can choose from one of our suggested light curves (a plot of each can be accessed by clicking on the graph icon in the top left), or you can search for a star of your choice.

If searching, use the search bar to enter the common name or any identifier of a star. The Suite uses SIMBAD to resolve the identifier, so if you are struggling to find a light curve for a star that definitely exists, check on SIMBAD for an alternative identifier to use.

If the star you searched for was captured in the TESS or Kepler/K2 missions, a list of light curves will display. Click the ***View Plot*** button on a row to see a light curve as a graph. When you have found a light curve you wish to sonify, click the ***Sonify*** button on that row.

### Constellations

These data contain various properties of the individual stars within specific constellations and asterisms (Right Ascension, Declination, apparent and absolute magnitudes, distances, colours, etc). 

Use the search bar (or click the arrow to see a drop-down menu) to find the constellation or asterism of interest, or click on one of the suggestions.

### Night Sky

These data contain information about all of the stars (above a magnitude limit) which are visible to an observer for a chosen location and time. These star data include magnitudes, colours, altitude and azimuth.

Click ***allow*** on the browser location pop-up to allow the Suite to auto-detect your location, or enter your location manually using a place name or lat/long coordinates (the location search is quite granular, so don't be afraid to try smaller/more rural locations).

Select the orientation of your dome which is at the front (with respect to your speaker system). In other words, if the audience got a compass out, which direction would they be facing?

Enter the date and time for which you sonify the night sky (this is the same time zone as your chosen location).

## Step 2: Refine :scissors:

Here you can optionally make edits to the data before sonifying. The refine options change depending on the data type.

### Light Curves

You can trim the start and end points of the light curve by dragging the slider or typing in the input boxes. This is useful if there is a gap in your light curve which you want to trim off.

You can also apply smoothing to the light curve using the second slider. This reduces noise in the signal (lots of little ups and downs) and leaves the more prominent features intact.

### Constellations

Choose whether to sonify only the stars that are typically included in the stick figure, or you can sonify an arbitrary number of stars inside the official constellation boundary lines. If using the boundaries, the number of stars you enter will choose the brightest stars within the constellation boundaries.

<small>
  :octicons-alert-16:
  **Note:** More stars will result in the sonification taking longer to generate.
</small>

!!! tip "Custom Order"
    Click ***Custom Order*** to choose the order in which the stars will play. 
    
    With this enabled, click on the stars in the plot on the right in the order you want to hear them (they will play equally spaced in time). Click the ***Reset*** button at any point to deselect all stars and start again.

    Using this feature will automatically map your chosen order to time, no matter which Style you choose (custom included) in the next step.

### Night Sky

Apply a magnitude limit to which stars are included in the sonification. Only stars brighter than the magnitude limit will be included. Magnitude values increase as stars get dimmer, so setting a higher magnitude limit will include more stars in the sonification. 

<small>
  :octicons-alert-16:
  **Note:** More stars will result in the sonification taking longer to generate.
</small>

## Step 3: Style :paintbrush:

The Style of a sonification is made up of 4 elements:

1. The base sound (or instrument) that is played.
2. The characteristics of the sound (parameters) that are controlled by the data.
3. The musical notes that the sonification adheres to.
4. Whether the data is heard as a continuous stream or as individual discrete events.

For each data type, some preset styles have been provided for you to get started. You can preview how these sound by clicking on the speaker icon in the top left (note that these previews are not applied to the dataset you chose), or read the description of the style by clicking the info icon.

!!! warning "Important"
    Consider the [guidance documentation](https://www.audiouniverse.org/sonification-suite/good-practise-guidelines) on how to choose effective sound designs.

Click on a preset style if you wish to use it and you will be taken straight to Step 4. Alternatively, click ***Custom*** to design your own style:

### Custom Styles

#### Parameter Mappings

- The ***Input*** is the data parameter (e.g., light curve time, absolute magnitude for stars etc.). In other words, the aspect of the data which you want to control the sound 
- The ***Output*** is the sound parameter you want to change (e.g., time of the sonification, filter cut off, pitch, volume etc.). In other words, the aspect of the sound you want to be controlled by the ***Input***. [Click here]() for more details on what the output parameters do.

Click ***+ Options*** under each mapping to control the parameters further:

- ***Range***: Set limits on the output parameter (the range is normalised from 0 to 1). For example, if you are mapping to volume, you might not want volume to reach zero volume (silence) for the lowest data point so you might set the output range from 0.1 (10%) to 1.0 (100%).

- ***Invert data***: You can also invert the data so that the smallest data values correspond to the biggest sound properties. For example, if you want to hear the brightest stars as the loudest, you could map Magnitude (Input) to Volume (Output) and select ***Invert Data***. This is necessary because the brightest stars have the smallest magnitude values. In some of the preset Styles, we also invert the colour values (which usually increase from blue to red) so that the bluer stars play higher notes.

!!! warning "Parameter mapping restrictions"

    - Some ***Input*** property must be mapped to the ***Output*** of time. For example, the time of a light curve is most likely to be mapped to the time of the sonification (so you hear the light curve over time). For constellations, you might map the star's magnitude to time (so the brightest stars are heard first) or Right Ascension (so the stars are heard in order of RA). 

    - You can only have one parameter mapping per ***Output*** type, i.e., only one data property can control any one of the sound properties.

    - Only one of ***Pan*** or ***Azimuth*** can be mapped. This is because they both control the direction that the sound comes from (***Pan*** is for Stereo, ***Azimuth*** is for 5.1 or 7.1 surround sound).

#### Data Mode

Choose from either ***Continuous*** or ***Discrete***. The mode you choose will determine which sounds are available in the Base Sound dropdown.

!!! info inline end "Pitch mapping"
    If using ***Continuous***, mapping something to **Pitch** means that the pitch will bend up and down as the data increases and decreases. If this is desired, it is recommended you use either **Power Hum**, **Tri Synth** or **Default Synth** as the base sound (and use a single note in the **Notes** input, if using one of the synths).

- ***Continuous***: The data will be heard as a constant stream of sound which evolves over time. You can think of this as the sonic equivalent of a line graph. Note that for Constellations or Night Sky, Continuous is disabled. This is because each data point represents a star, rather than a value that changes continuously between points.

- ***Discrete***: The data points are heard as individual events in time. This can be thought of as the sonic equivalent of a scatter graph. The recommended base sounds to use with discrete sonifications are **Harp**, **Glockenspiel**, or **Mallets**.

#### Base Sound

Select the underlying sound/instrument that is used as a basis for the sonification. The options available are determined by the **Data Mode** you have selected. Base sounds with a :musical_keyboard: icon next to them are 'composable', meaning you have the option to choose the notes that they play in the musical setings below. 

<small>
  :octicons-light-bulb-16:
  Some base sounds aren't composable because they already have multiple notes 'baked in' to the audio, such as **Sci-Fi Strings** and **Twinkle Mallets**
</small>

#### Musical Settings

If your chosen base sound is composable ( :musical_keyboard: ), options for **Root Note**, **Harmony**, **Notes**, and **Octave Range** will appear.

- ***Root Note***: The note which the chord or scale is built from. Really, this is an arbitrary choice, unless you want the sonification to fit in a certain key to overlay some music etc.
- ***Harmony***: The chord to build from the root note. If using ***Discrete*** Data Mode, you will also have a choice of scales to use. Click the dice icon to the right to pick a random root note and harmony combination.
- ***Notes***: The set of musical notes that the sonification will ultimately use. This note set is re-generated any time you change the root note, harmony, or octave range. You can double-click on notes to edit them, click the x to delete them, or type in new notes next to them. This accepts any note (sharps and flats included) from the range C1 to B6.
- ***Octave Range***: How many octaves you want your note set to span. In other words, how low should the lowest note be, and how high should the highest be.

!!! question "How are the notes actually played?"
    In ***Continuous*** Data Mode, the notes are all played at once (as a chord) and held for the duration of the sonification. This is why you'll only see scales in the harmony options when using ***Discrete*** Data Mode - because playing all of the notes in a scale simultaneously might not sound very good (holding the notes of a Chromatic scale all at once is the equivalent of pressing every key on a piano at the same time!). This is also why you should use caution when using the ***Pitch*** output in ***Continuous*** mode - as using multiple notes means the whole chord will bend up and down in pitch.

    In ***Discrete*** Data Mode, only individual notes are played at a time. To hear different notes, you'll need to map something to the ***Pitch*** output.

#### Previewing your Custom Style
Click the ***Preview*** button at the bottom of the menu to hear a 5-second preview of your style settings. Note that this does not use your chosen dataset, but instead uses a [sine wave](https://en.wikipedia.org/wiki/Sine_wave) as the input data. This means that you can hear your parameter mappings go up and down smoothly through their full range, using your chosen ***Base Sound*** and ***Notes***.

#### Importing Custom Styles
On the final Sonify page, you have the option to download your Style file (in the Downloads section of the summary). You can then reuse this Style again by clicking ***Import*** at the top of the Custom Style Menu and uploading it.

<small>
  :octicons-alert-16:
  **Note:** You can only import a custom Style when using the same data type that it was created for. In other words, a Style created for a light curve can only be used for light curves, etc. This is because a Style file contains the ***Inputs*** which are specific to that data type.
</small>

## Step 4: Sonify :loud_sound:
The final step of the workflow. This is where you add final settings, generate the sonification, and save any outputs.

- ***Duration***: How long in seconds do you want the sonification to last? The data will be spread across this timeframe before generation, so the audio will not distort by stretching it. The maximum duration is 2 minutes (or 1 minute if you are using several layers in the Data Composer). For light curves, you also have the option to choose how many days in the data you want to pass per second. This will automatically calculate a new total duration for you.

- ***Audio System***: Choose your planetarium's audio system from Mono, Stereo, 5.1, or 7.1. This will determine how many channels the generated audio file will have.

<small>
  :octicons-light-bulb-16:
  Changing ***Duration*** or ***Audio System*** will require you to re-generate the sonification for the new settings to take effect.
</small>

Click ***Generate Sonification*** to create your audio file. For longer sonifications (or those that use lots of stars/data points), this may take some time. Once ready, the audio player will pop up at the bottom of the screen.

Click the ***Download*** button to save your sonification as either WAV or MP3. Sonifications generated for 5.1 or 7.1 audio are only available for download as WAV files.

#### Summary
In the ***Summary*** section you will find the style description (if using a preset style), the data name and the style name. In the ***Downloads*** section, you can save the dataset and Style file for later use. This may be handy if you have spent some time refining a dataset, or fine tuning a custom Style, and would like to import either of those back into the Suite for a future sonification.

#### Mapping Table
You can also download the ***Mapping Table*** for your sonification. This is a CSV file which shows the exact timing and sound parameters for each data point. For sonifications created using ***Continuous*** data mode (such as many of the preset light curve Styles), the table will show the evolving properties regularly sampled in time.

For Constellations and Night Skies, the Mapping Table will also identify each data point (star) with its Hipparcos ID and display name(1). 
{ .annotate }

1. The star's display name is taken from the first available identifier in the following order of preference: **Proper name → Flamsteed designation → Bayer designation → HIP ID (Hipparcos ID) → HD ID (Henry Draper Catalogue ID)**.

By showing when each star is heard in the sonification, the Mapping Table can help you synchronise the audio with a visual sequence in your planetarium software.

#### Spectrogram
After generating your sonification, a spectrogram will be available to view. Click the switch above the data plot to view it.

??? question "What is a Spectrogram?"
    A spectrogram is a visual picture of sound. It shows three things at the same time on one graph: how **frequency** (pitch) and **loudness** (amplitude) change as **time** goes by.

    How to Read a Spectrogram:

    - Horizontal Axis (X-axis): shows time moving from left to right.
    - Vertical Axis (Y-axis): shows frequency or pitch, with low sounds at the bottom and high sounds at the top.
    - Colours and Brightness: show the amplitude or loudness. Bright colours (like white and yellow) mean the sound is loud at that frequency, while dark or cool colours (like black/blue) mean it is quiet or absent.