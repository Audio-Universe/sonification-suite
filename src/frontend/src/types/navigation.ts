import { Layer } from "./layers";
import { ConstellationType } from "./refine_menu";

export interface NavigationState {
    soniType?: string;
    dataName?: string | null;
    dataRef?: string | null;
    sourceDataRef?: string | null;
    styleRef?: string;
    styleName?: string;
    styleDescription?: string;
    ra?: number | null;
    dec?: number | null;
    editStyle?: string;
    layers?: Layer[];
    layerID?: string;
    idColumn?: string | null;
    customOrder?: boolean;
    constellationType?: ConstellationType;
    importedNStars?: number | null;
    importedOrder?: number[] | null;
    importedMaxMag?: number | null;
    nStars?: number;
  }