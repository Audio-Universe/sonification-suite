# Data Composer

The **_Data Composer_** allows you to upload any CSV (Comma Separated Values) dataset, and create a multi-layered sonification from it.

The general workflow follows these steps (given in more detail below):

<ol>
<li><strong>Data</strong>: Upload a .CSV dataset.</li>

<li><strong>Refine</strong>: Optionally, trim the start and end points, remove or reorder columns, and choose how to handle any missing values.</li>

<li><strong>Style</strong>: Choose from a preset Style, or create your own in the Custom Style Menu.</li>
</ol>

**You can add up to 8 layers, repeating steps 1–3 for each layer.**

<ol start="4">
<li><strong>Sonify</strong>: When each layer has a dataset and Style, you can continue to the Sonify page to generate your sonification.</li>
</ol>

!!! question "What is a layer?"

    Each layer is essentially its own sonification. By using multiple layers, you can hear several aspects (or variables) of your data change over time, each represented by a different sound.

    The key difference between the Data Composer and the Planetaria module is that the Data Composer allows you to combine **multiple datasets** and **multiple Styles** in a **single sonification**. In the Planetaria module, each sonification uses only one dataset and one Style.

    **All layers will start and end at the same time, regardless of how much data is in each one.**

## Step 1: Data :test_tube:

After clicking **_Add layer_**, you will have the option to upload a file. This must be in CSV format, up to a maximum of 10MB. Check the box to say whether it has a header row or not (are the columns labelled?). The expected format is tabular data, where the columns represent the different data variables (e.g. `time`, `temperature`, `voltage`, etc.) and the rows represent the individual data points.

If this is not your first layer, you will have the option to use the same dataset as another layer.

Using the **same dataset across all layers** would allow you to hear different variables of the data, each with a different Style. If using the same dataset, you may want to make sure your chosen Styles map the same column to Time for every layer. This way, you will hear each data variable synchronised to a common time base.

> **Example:** You upload a CSV of a year's daily weather readings, with `date`, `temperature`, and `wind_speed` columns. On one layer, you create a Style that maps `temperature` to Pitch and `date` to Time. On another, you map `wind_speed` to Filter Cutoff and `date` to Time again. As both layers map the same column to Time, you'll hear the seasons unfold with temperature and wind changing together, in sync. Note that only numeric columns can be mapped - if your `date` column is in dd/mm/yyy format (or similar), you'll need to convert it to an ascending numeric format first.

Alternatively, you might want to use **multiple different datasets** to hear different data sources at the same time.

> **Example:** You have brain wave data for each hemisphere of the brain. On the first layer, you upload the left hemisphere's CSV file. You map `time` to Time, and `voltage` to Filter Cutoff, using the _Windy_ preset. On the second layer, you upload the right hemisphere's CSV file, again mapping `time` to Time and `voltage` to Filter Cutoff, this time using the _Sci-Fi_ style. You will be able to hear both hemispheres' voltage change in sync, each one with a different sound. Note that all layers start and end at the same time, so if the `time` data from each are on different timescales, they will both be either stretched or compressed to fit the duration of the sonification.

## Step 2: Refine :scissors:

Optionally, click **_Refine_** on a layer to make some changes to the dataset.

Here, you can select which columns to use, which rows to start and end at, and how to handle missing values (if they are present in your data).

### Columns

Check or uncheck the column names to include or remove them from your dataset. If you are going to create a custom Style for this layer, this might not be necessary, as you will select which columns (**_Inputs_**) to map to which **_Outputs_** in the Custom Style Menu.

However, **if you use a preset Style, the ordering of the columns matters**. All of the preset Styles use the first (left-most) column in your dataset as the Time mapping. The second column is mapped to whichever other parameter the preset uses (e.g. Filter Cutoff for _Sci-Fi_, or Pitch for _Power Hum_). You can change the order of the columns by unchecking all of the column boxes, and then re-checking them in your desired order.

<small>
  :octicons-alert-16:
  **Note:** Only numeric values can be used for sonification (e.g. 1, 2, 3.14, -100). That means you will not be able to use any columns which contain text, or any other formats such as date.
</small>

### Identifier Column
You can optionally choose a column to include as the indentifier column in the [Mapping Table](../user-guide#mapping-table) which is output after generating your sonification. 

This is useful if each row in your dataset is an individual entity (e.g. a star) which has a name or identifier. You can then see each labelled data point linked to the time it plays, and any other parameters, in the resulting Mapping Table. This may be useful for timing visuals to go alongside your sonification.

Note that only columns that contain unique values can be used as the Identifier Column.

### Missing Values
If there are missing/empty values in any of your columns, you can choose how to handle them.

By default, rows with missing values will not be played (they will be silent) but you also have the option to interpolate them, or fill them in with another value. 

Interpolating means estimating the value from surrounding rows. For instance, if the values go 4, 5, *blank*, 7, interpolating the column will fill the blank with 6.

You can also fill the missing values with another number from that column, such as the minimum, maximum, mean, median, or mode.

### Row Range
You can also trim the start and end points of your data with the Row Range slider. This may be helpful if the top of your dataset contains a lot of metadata or extra headers, for instance.

## Step 3: Style :paintbrush:

Each layer needs a ***Style***. 

**For an in-depth explanation on what Styles are and how to create your own, please visit the [User Guide](../user-guide#step-3-style).**

The preset Styles for the Data Composer will only use the first two columns of your data. The first will be mapped to Time, and the second column is mapped to whichever other parameter the preset uses (e.g. Filter Cutoff for _Sci-Fi_, or Pitch for _Power Hum_).

## Adding, Duplicating, and Deleting Layers
You have the option to add up to 8 layers using the ***Add Layer*** button beneath your existing layers.

For each layer, you can click the pencil icon next to its name to rename the layer. You can also click the copy icon on the right to duplicate the layer. This may be handy if you've spent a while creating a custom Style for a layer and you want to use the same Style on another layer.

You can delete layers by clicking the bin icon on the right. Note that some layers may be using the same dataset as the layer you intend to delete - you will receive a warning if this is the case.

Once all layers have a valid dataset and Style added, you can click ***Continue to Sonify***.

## Step 4: Sonify :loud_sound:
The final step of the workflow. This is where you add final settings, generate the sonification, and save any outputs.

- ***Duration***: How long in seconds do you want the sonification to last? The data will be spread across this timeframe before generation, so the audio will not distort by stretching it. The maximum duration is 2 minutes (or 1 minute if you are using more than 2 layers).

- ***Audio System***: Choose your audio system from Mono, Stereo, 5.1, or 7.1. This will determine how many channels the generated audio file will have.

<small>
  :octicons-light-bulb-16:
  Changing ***Duration*** or ***Audio System*** will require you to re-generate the sonification for the new settings to take effect.
</small>

Click ***Generate Sonification*** to create your audio file. For longer sonifications (or those that use lots of layers/data points), this may take some time. Once ready, the audio player will pop up at the bottom of the screen.

Click the ***Download*** button to save your sonification as either WAV or MP3. Sonifications generated for 5.1 or 7.1 audio are only available for download as WAV files.

#### Volume Mixer
The volume mixer allows you to change the volumes of indiviual layers. Changing the volume of a layer will automatically re-generate the audio, and apply to the audio files you can download for individual layers.

You may find it useful to temporarily turn the volume all the way to zero for some layers, to hear exactly what each one is doing.

#### Summary
In the ***Summary*** section you will find a summary for each layer. This includes the style description (if using a preset style), the data name and the style name for each layer. If you used a custom Style, you will have the option to click ***Edit*** to go back to your Style settings and tweak anything that you like.

In the ***Downloads*** section, you can save the datasets and Style files for later use. This may be handy if you have spent some time refining a dataset, or fine tuning a custom Style, and would like to import either of those back into the Suite for a future sonification.

There are also download links for each layer's individual audio, which may be useful if you want to use them separately, for instance to trigger at different times in your content.

#### Mapping Table
You can also download a ***Mapping Table*** for each layer. This is a CSV file which shows the exact timing and sound parameters for each data point. For sonifications created using ***Continuous*** data mode (such as many of the preset light curve Styles), the table will show the evolving properties regularly sampled in time.

If you chose an [identifier column](#identifier-column) in the Refine menu, the mapping table will link each data point with its identifier from that column.

By showing when each data point is heard in the sonification, the Mapping Table may help you synchronise the audio with a visual sequence you have created.

#### Spectrogram
After generating your sonification, a spectrogram will be available to view. Click the switch above the volume mixer to view it.

??? question "What is a Spectrogram?"
    A spectrogram is a visual picture of sound. It shows three things at the same time on one graph: how **frequency** (pitch) and **loudness** (amplitude) change as **time** goes by.

    How to Read a Spectrogram:

    - Horizontal Axis (X-axis): shows time moving from left to right.
    - Vertical Axis (Y-axis): shows frequency or pitch, with low sounds at the bottom and high sounds at the top.
    - Colours and Brightness: show the amplitude or loudness. Bright colours (like white and yellow) mean the sound is loud at that frequency, while dark or cool colours (like black/blue) mean it is quiet or absent.