const viteEnv = import.meta.env.VITE_API_URL;
const local = import.meta.env.VITE_SONIFICATION_BACKEND_URL ?? 'http://localhost:8000';
const dev = 'http://127.0.0.1:8000'

export const apiUrl = local
export const coreAPI = `${apiUrl}/core`

// V1 sonification types
export const lightCurvesAPI = `${apiUrl}/light-curves`
export const constellationsAPI = `${apiUrl}/constellations`
export const nightSkyAPI = `${apiUrl}/night-sky`
export const composerAPI = `${apiUrl}/data-composer`

/* The below comment serves as a marker for the template generator, so it can safely generate new routes and 
    add them to this file without overwriting any existing ones. Please do not move or remove it, unless you 
    are intentionally modifying the way the template generator works.
*/
// Generated sonification APIs - DO NOT REMOVE THIS COMMENT