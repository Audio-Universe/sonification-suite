import { LuLayers3 } from "react-icons/lu";

export interface SoniType {
    key: string;
    label: string;
    description: string;
    page: string;
    icon?: React.ElementType;
    imgAltText?: string;
  }

  export const astroTypes: SoniType[] = [
    {
      key: "light_curves",
      label: "Light Curves",
      description: "Listen to fluctuations in a star's light.",
      page: "light-curves",
      imgAltText: "A NASA image of a binary star system"
    },
    {
      key: "constellations",
      label: "Constellations",
      description: "Hear the unique qualities of famous star patterns.",
      page: "constellations",
      imgAltText: "A photo of the Orion constellation"
    },
    {
      key: "night_sky",
      label: "Night Sky",
      description: "Hear the stars at your location appear.",
      page: "night-sky",
      imgAltText: "An image of a starry night sky, with the shape of the Milky Way visible"
    },
    {
      key: "data_composer",
      label: "Data Composer",
      description: "Upload your own data and compose sonifications in layers.",
      page: "/data-composer",
      icon: LuLayers3,
    },
    // Generated soniTypes - DO NOT REMOVE THIS COMMENT
  ];