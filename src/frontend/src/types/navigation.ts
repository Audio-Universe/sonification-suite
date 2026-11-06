/**
 * This interface defines the NavigationState object that carries data from page to page
 * through each navigation.
 */

import { Layer } from "./layers";
import { ConstellationType } from "./refine_menu";

export interface NavigationState {
    // soniType is the key that identifies each sonification type (e.g. 'light_curves', 'constellations', etc.)
    soniType?: string;

    // The display name for the dataset
    dataName?: string | null;
    // File reference to the data in the backend
    dataRef?: string | null;
    // File ref to the original (unrefined) data in backend
    sourceDataRef?: string | null;

    // File ref to the style file in backend
    styleRef?: string;
    // Name of the style (if using a preset)
    styleName?: string;
    // Style description (if using a preset)
    styleDescription?: string;

    // Right Ascension value (if this soni type supports Place on Dome feature)
    ra?: number | null;
    // Declination value (if this soni type supports Place on Dome feature)
    dec?: number | null;

    // The file ref of the Style to edit (if we are opening the custom style menu from the 'Edit' button on Sonify page)
    editStyle?: string;

    // The array of Layer obects (if using Data Composer)
    layers?: Layer[];
    // The unique ID of an individual layer
    layerID?: string;
    // The chosen identifier column (if using Data Composer)
    idColumn?: string | null;

    // A flag to indicate whether the user has chosen a custom constellation order
    customOrder?: boolean;
    // The type of constellation we are refining (this is used to set up the refine menu correctly)
    constellationType?: ConstellationType;
    // If importing a constellation, how many stars are in it
    importedNStars?: number | null;
    // The custom constellation order, if importing a constellation which previously selected a custom order
    importedOrder?: number[] | null;
    // If importing a Night Sky, the maximum magnitude in the dataset
    importedMaxMag?: number | null;
    // The number of stars in the chosen constellation (this is used to display a warning if using the Orchestra style)
    nStars?: number;
  }