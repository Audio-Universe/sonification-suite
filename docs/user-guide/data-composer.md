# Data Composer

The ***Data Composer*** allows you to upload any CSV (Comma Separated Values) dataset, and create a multi-layered sonification from it.

The general workflow follows these steps (given in more detail below):

<ol>
<li><strong>Data</strong>: Upload a .CSV dataset (up to 10MB) and check the box to say whether it has a header row or not.</li>

<li><strong>Refine</strong>: Optionally, trim the start and end points, remove or reorder columns, and choose how to handle any missing values.</li>

<li><strong>Style</strong>: Choose from a preset Style, or create your own in the Custom Style Menu.</li>
</ol>

**You can add up to 8 layers, repeating steps 1–3 for each layer.**

<ol start="4">
<li><strong>Sonify</strong>: When each layer has a dataset and Style, you can continue to the Sonify page to generate your sonification.</li>
</ol>

??? question "What is a layer?"
    Each layer is essentially its own sonification. By using multiple layers, you can hear several aspects (or variables) of your data change over time, each represented by a different sound.

    The key difference between the Data Composer and the Planetaria module is that the Data Composer allows you to combine **multiple datasets** and **multiple Styles** in a **single sonification**. In the Planetaria module, each sonification uses only one dataset and one Style.


## Step 1: Data :test_tube:
After clicking ***Add layer***, you will have the option to upload a file, or (if this is not your first layer), use the same dataset as another layer.

Using the same dataset across all layers would allow you to hear different variables of the data, each with a different Style. If using the same dataset, you may want to make sure your chosen Style maps the same column to Time for every layer. This way, you will hear each data variable synchronised to a common time base.

> **Example:** You upload a CSV of a year's daily weather readings, with `date`, `temperature`, and `wind_speed` columns. On one layer, you create a Style that maps `temperature` to Pitch and `date` to Time. On another, you map `wind_speed` to Filter Cutoff and `date` to Time again. As both layers map the same column to Time, you'll hear the seasons unfold with temperature and wind changing together, in sync. Note that only numeric columns can be mapped - if your `date` column is in dd/mm/yyy format (or similar), you'll need to convert it to a numeric format first.

Alternatively, you might want to use multiple different datasets to hear different data sources at the same time.
