# Building Extensions

<small>
  :octicons-light-bulb-16:
  This document is intended for developers building and running their own local version of the Suite, as well as future developers contributing to the production web app.
</small>

The Suite is designed to be extensible, allowing developers to introduce new sonification types without having to build each one from scratch. A code generation framework is provided to automate much of the process, creating the necessary frontend and backend files and registering the new sonification type throughout the application.

This means developers can focus primarily on the scientific data, sonification methods and user experience specific to their extension, rather than having to worry too much about the underlying application architecture.

Note that this feature is exclusive to the ***Planetaria*** module. If new modules are added in future, it would be wise to update the template generator to reflect this.

## Overview

Each sonification type follows a common structure and integrates with the Suite through a number of shared components and configuration files. The generator creates the initial scaffolding for a new type, including:

- **Frontend:** A landing page component, basic refine menu and API configuration.
- **Backend:** A dedicated API router and the necessary registrations in shared backend modules.
- **Data & Styles:** A suggested data directory (containing mockup datasets) and a style files directory (containing one basic style).
- **Application integration:** Updates to routing, navigation, breadcrumbs and sonification type metadata.

The generated files provide a starting point rather than a finished implementation. Developers will need to customise the generated components, add static assets (images and audio), implement the relevant backend functionality and add suggested data sets and styles.

## Using the Generator

The generator is located in the `src/template_generator/` directory of the repository, and the `templates` directory contains the Jinja2 templates of the files to be generated.

The `add_soni_type.py` script is the one you will need to run directly to start the generator.

!!! warning "Hold Your Horses!"
    Running the generator will create and make changes to numerous files across the codebase. This is not something that is easy to quickly undo. 
    
    Therefore, if you are just testing out the generator and don't mean to make permanent changes, I would recommend switching to a throwaway branch in git which you can just delete after testing the generator. E.g:

    ```bash
    git switch -c generator-test
    ```

    Then when you have finished testing:

    ```bash
    git reset --hard HEAD           # Undo changes to shared files
    git clean -fd                   # Remove generated files
    git switch -                    # Switch back to original branch
    git branch -D generator-test    # Delete branch
    ```

When you are ready, run `add_soni_type.py`.

Via a command line interface (CLI), the generator will prompt you for:

1. **Sonification type name:** The name of your new type (e.g. `Exoplanets` or `Black Holes`).
This can be in upper or lower case, as we normalise the text anyway.

2. **Singular form:** The singular form of the name (e.g. `exoplanet` or `black hole`).
This is used to format error messages.

3. **Description:** A short description displayed to users on the Planetaria landing page.

The generator automatically derives the naming conventions used throughout the codebase, including `snake_case`, `PascalCase` and `camelCase` variations.

Before making any changes, it displays the generated values and asks you to confirm that they are correct.

Once confirmed, the generator creates the necessary files and updates the relevant shared files. Generated files are intended to provide a consistent starting point for your extension.

!!! success "Generation Complete!"
    You should now be able to run the app and see your new sonification type added to the Planetaria landing page. 
    
    It is fully integrated using mockup data and styles, so it should work end-to-end in the sonification workflow.

## Customising Your Extension

After generation, you will need to implement the functionality specific to your sonification type. 

I have provided a checklist below, to ensure nothing is missed. We will use **Exoplanets** as the example sonification type added.

### 1. Landing Page

The landing page for your sonification type will be generated into `src/frontend/src/components/pages/Exoplanets.tsx`.

Visit this file first, as it contains lots of comments explaining basic React concepts (useful if you are new to TypeScript/React) as well as conventions we use throughout the Suite.

Once you understand the basics of what the page is doing, you can build in your own function and components to search for/retrieve data from the backend. You may also want to change the layout completely, if your sonification type is more like Night Sky, for example.

I would also change the generic 'Search for an item...' text below the header to something more specific to your data type (e.g. search for an exoplanet...).

### 2. API

The API module will be created at `src/backend/exoplanets.py`.

It contains basic endpoints for retrieving, refining, and plotting data, but you should edit the endpoints to match your desired data source.

!!! info "Note"
    If you change any of the endpoint addresses e.g. you change `/select-item/` to `/select-exoplanet/`, just make sure to reflect this change in the frontend where the api request is being made.

    As a reminder, all endpoint addresses throughout the Suite end with a trailing slash (this may be one of the first things to check if debugging a failed api call).

### 3. Suggested Data

A suggested data directory has been generated at `src/backend/suggested_data/exoplanets`. It is initially filled with random datasets.

Once you have some example datasets to provide for your sonification type, you can add them to the suggested data directory and delete the placeholders.

**The Suite exclusively handles CSV data files, so ensure that both your suggested data and any data downloaded from a 3rd party are all converted to CSV. You should also ensure that both suggested datasest and downloaded datasets contain the same column headers, as these are used for parameter mapping.**

!!! info "YAML files"
    You'll notice that each suggested dataset has its own .yml file. This contains the name and description of the dataset to display on the landing page. Make sure you have one for each of your suggested datasets (using the same file name as the data, but with .yml extension).

    These files can contain additional information about the suggestions which might be necessary, for example, the light curves also contain `category` for splitting them into different tabs, and `ra` and `dec` for use with the Place on Dome feature.

#### Images
You will want to add images or icons for your suggested data cards. 

Put these in the `src/frontend/src/assets/images` directory, and make sure the file names match the names given in the suggested data yaml files.

By default, your `Exoplanets.tsx` will look for the images with .svg extension, as we use SVG images for all light curve and constellation cards.

SVGs are made up of shapes and lines (no background) which makes them ideal for animating with the 'twinkle' CSS animation we use throughout the app. I would recommend finding or creating SVG images for your suggestions if you want to maintain a cohesive style with the other sonification types.

### 4. Refine Menu

A basic refine menu component has been generated at `src/frontend/src/components/refine_menus/exoplanets.tsx`.

This just contains a slider for trimming the start and end of the dataset, but you will most likely want to add some more bespoke operations for your sonification type.

If your datasets can include missing data, you may want to handle the NaNs in your refine menu. If so, you can import the `NaNHandler.tsx` from `components/ui`, which is used for both Light Curves and Data Composer. Take a look how it works in the light curves refine menu to mirror the approach in your extension.

### 5. Add Parameter Names & Descriptions

Once you have decided which columns to make available for parameter mapping, you should add these to the INPUTS dictionary in `src/backend/inputs_outputs.py`.

A placeholder entry has been generated for you, but be sure to update the names and descriptions of the columns you want to add, as these will be displayed in the custom style menu 'input' dropdown.

### 6. Style Files

You will want to create some suggested styles for your new sonification type. 

Once you have made the style files, drop them into the `src/backend/style_files/exoplanets` directory. They will then display on the Styles page.

Make sure to include a name and description in the style files, as the description will be displayed if users click the info icon on the style, and on the final Sonify page.

#### Audio Previews
You will also need to manually create a short audio clip for each of your styles.

I suggest using a dataset which can exemplify the style well over a short duration (all current style previews are 8 seconds), and sonifying this with the style to create the preview. 

For the V1 styles, we also manually add a short fade-out to the previews, and save them as MP3 files.

When you have created the previews, make sure the file names matches the style names, and put them in `src/frontend/src/assets/audio`. You should now be able to click the speaker icon on each style card to hear the previews play.

### 7. Image on Planetaria Page
To add an image to the new ***Exoplanets*** card on the Planetaria landing page, you can put an image called `exoplanets.jpg` in `src/frontend/src/assets/images`. 

If using an image, it is important to add alt text so tha screen readers can read out a description of the image. You can add the alt text in `src/frontend/src/types/soniTypes.ts`.

You may also choose to use an icon, similar to Data Composer and Suggestions & Examples. If so, choose an icon from the [Lucide library](https://lucide.dev/icons/) and import it at the top of the `soniTypes.ts` file. You can then specify 'icon: Lu[icon name]' in the metadata, and the Suite should render the icon instead of looking for `exoplanets.jpg`.

### 8. (Optional) Configure Imports
By default, it is possible on all sonification types to 'import' a previously downloaded dataset of that type. This also applies to your generated sonification type.

Depending on the features of your implemented Refine menu, you may want to gather some information about the imported dataset to set up the refine menu.

For instance, with Night Sky, we find the maximum magnitude in the imported dataset and update the limit of the Magnitude input on the refine menu so that it is impossible to go past the new maximum. For constellations, we check whether the imported dataset is an asterism, if it uses a custom order, and whether it used boundaries or stick figure mode. These all affect what options are made available or pre-populated on the constellations refine menu when importing data.

If you want to implement similar conditions for your extension, you will find an `elif` branch has been generated for you in the `validate_import` function in `core.py`. You just need to add things to the `import_info` dictionary and then add them to the NavigationState object in `handleImportSuccess` in your landing page.

<small>
  :octicons-light-bulb-16:
  If doing this, you will need to add to the NavigationState definition in `types/navigation.ts`, as well as the RefineMenuProps definition in `types/refine_menu.ts` so that the values can successfully get passed down into the refine menu to take effect.
</small>

## Testing Your Extension

Before deploying your extension, test it locally to ensure that it integrates correctly with the rest of the Suite.

Check that:

- The new sonification type appears on the Planetaria landing page (with an image).
- Navigation, routing and breadcrumbs work as expected.
- Suggested datasets appear on the landing page with names, descriptions, and images.
- Users can select or download the appropriate data.
- Users can import previously refined/downloaded data.
- The refine menu works correctly.
- The suggested styles display and audio previews work.
- The custom style menu renders the expected parameters in the ***Inputs*** dropdown.
- The backend endpoints return the expected responses.
- Sonification generates successfully and produces the expected audio/mapping table.
- Existing sonification types continue to work as expected.
