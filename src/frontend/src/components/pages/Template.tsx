/*

This file is the template page of a sonification type that might be added to the Planetaria
module in the future, e.g. Exoplanets, Black Holes, Nebulae, etc.

It is based off of the Constellations data type, which fetches the available options from the
backend and renders them in a Combobox (a dropdown menu with search function). Depending on the
data type you want to add, you may want something closer to Lightcurves.tsx, which allows users
to enter a search query which is sent to the backend to connect to a 3rd party data source (in 
the case of light curves, using the lightkurve package). Either way, this template contains most
of the skeleton of a sonification type (you just need to add the specific organs you want!).

Places to update 'template':
Frontend:
  Template.tsx
  App.tsx
  Planetaria.tsx
  template.tsx (in /refine_menus)
  apiConfig.ts

Backend:
  template.py
  main.py (where you import/include the router)
  /suggested_data

*/

import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { LuTelescope } from "react-icons/lu";
import PageContainer from "../ui/PageContainer";
import { getImage, randomRange } from "../../utils/assets";
import { coreAPI, templateAPI } from "../../apiConfig";
import { SuggestedData } from "../../types/suggestedData";

import {
  Box,
  Alert,
  Card,
  Link,
  InputGroup,
  Stack,
  Heading,
  Text,
  HStack,
  Combobox,
  createListCollection,
  useFilter,
  Portal,
} from "@chakra-ui/react";
import { NavigationState } from "../../types/navigation";
import ErrorMsg from "../ui/ErrorMsg";
import { DataImport, ImportResult } from "../utils/DataImport";
import { apiRequest } from "../../utils/requests";

// ChakraUI dropdowns tend to like items in this format
interface ListItem {
  label: string; // This is the (nicely formatted) text that is displayed to the user
  value: string; // This is the underlying value which may get passed to/from the backend
}

export default function Template() {
  /*
    The soniType is the name of the sonification/data type, and is used throughout the app 
    to customise the workflow to that specific type.
    
    For instance, if the soniType is 'constellations' or 'night_sky', we enforce Discrete data mode 
    in the custom style menu. On the Sonify page, the place on dome feature only appears if the soniType 
    is 'light_curves' or 'constellations' etc.

    The current list of soniTypes is as follows (and these are consistent with the SONI_TYPE constants 
    used in the backend): 'light_curves', 'constellations', 'night_sky', 'data_composer'.

    Here we use 'template', but you should swap this out for 'exoplanets', 'black_holes', etc.
   */
  const soniType = "template";

  // Navigate function - this must be instatiated in order to navigate to different pages/components
  const navigate = useNavigate();

  /*************** States ***************/
  /*
    State is a core concept in React. It is what makes it 'reactive'. States are used to 
    store dynamic data that can change over time based on user interactions, API responses, 
    or system events. When a state variable changes, React automatically re-renders the 
    component to update the user interface. It's like a local variable, but one that tells 
    the browser to instantly refresh what is on the screen whenever it changes.

    We don't use many states in this component, but a quick look at e.g. LightCurves.tsx will 
    show you the extent of things they can be used for. For example, it is often handy to create 
    loading states with booleans: user clicks 'Save' -> handleClickSave() function is called -> 
    the function starts with setLoading(true) -> this renders a loading spinner -> the handler 
    function then proceeds to call the API/save the data etc before ending with setLoading(false), 
    which stops the loading spinner.

    To create a state, use a hook called useState (import this from react).
    It breaks down into three parts:
    
    1. The Variable (e.g. loading): Holds the current value.
    2. The Setter (e.g. setLoading): The function to change the value.
    3. The Initial Value (e.g. false): The starting value passed into useState().

    e.g. const [loading, setLoading] = useState(false)

    You will sometimes see the type passed in the <> brackets, this is needed when the type can't 
    be inferred from the initial value. Like below, we have a state for the list of suggested data 
    items. We initialise it with an empty array, but we make it explicit with the <> that this is 
    an array of SuggestedData.
*/
  const [suggested, setSuggested] = useState<SuggestedData[]>([]);
  const [listItems, setListItems] = useState<ListItem[]>([]);
  const [importErrorMessage, setImportErrorMessage] = useState("");

  /*************** UseEffects ***************/
  /* 
    These are functions that 'watch' a value and are triggered everytime the value changes.
    The value to be watched goes inside the array at the end of the function (called the dependency array).
    
    Here, we leave the dependency arrays empty on both our UseEffects. This means that the functions will 
    both run once when the page/component initially loads.
  */

  // Fetch suggested data on load
  useEffect(() => {
    fetch(`${coreAPI}/suggested-data/${soniType}/`)
      .then((res) => res.json())
      .then((data) => {
        const mapped: SuggestedData[] = data.map((item: any) => ({
          name: item.name,
          description: item.description,
          fileRef: item.file_ref,
        }));

        setSuggested(mapped);
      })
      .catch((err) => {
        console.error("Failed to fetch suggested data:", err);
      });
  }, []); // <-- empty dependency array

  // Fetch the full list of available data on load
  useEffect(() => {
    fetch(`${templateAPI}/list/`)
      .then((res) => res.json())
      .then((data) => {
        // Here we just use the same value for label & value, but you might want something different
        const formattedList = data.map((item: string) => ({
          label: item,
          value: item,
        }));

        setListItems(formattedList);
      })
      .catch((err) => {
        console.error("Failed to fetch data list:", err);
      });
  }, []); // <-- empty dependency array

  /*************** Handlers ***************/
  /* 
    Unlike UseEffects, which are special functions (hooks) unique to React,
    handlers are just normal functions, but it is common practice to create a 
    handler for each interaction a user might have in the app.

    In this case, we have a handler for when a user selects an item from the ComboBox, 
    and for when a user clicks one of the suggested data items.
  */

  const handleSelectListItem = async (item: ListItem) => {
    // Here we imagine that this api request downloads the chosen data in the backend and returns the file ref
    const url = `${templateAPI}/select-item/`;
    const payload = {
      item_name: item.value,
    };

    // apiRequest is a function I made to reduce repetitive boilerplate code for each API call
    const response = await apiRequest(url, payload);

    // This NavigationState object is what gets passed between each frontend component when we navigate.
    // In other words, this is what gets 'remembered' between pages (very important!).
    const state: NavigationState = {
      sourceDataRef: response.file_ref, // The returned file reference in the backend
      /**
       * Note that here we pass 'sourceDataRef', but from the Refine page onwards, we use 'dataRef'.
       * This is so that when navigating to Refine, we always load the original (unrefined) dataset.
       * After clicking 'apply' on the Refine page, dataRef is updated with the reference to the refined
       * dataset, so if we just pass dataRef: response.file_ref here, a user navigating back to refine will
       * always see their refined dataset (and won't be able to 'unrefine' it).
       */

      dataName: item.label, // The nicely formatted name of the data to be displayed throughout the frontend
      soniType, // shorthand for soniType: soniType
    };

    // Navigate to the /refine route, which is configured in App.tsx to render the Refine.tsx component
    navigate("../refine", { state }); // includes the state object
  };

  const handleSelectSuggested = (item: SuggestedData) => {
    // Suggested data is already downloaded in the backend, so no need for the api call
    const state: NavigationState = {
      sourceDataRef: item.fileRef,
      dataName: item.name,
      soniType,
    };

    navigate("../refine", { state });
  };

  // This handler is called if/when a user successfully 'imports' a previously downloaded dataset of this soniType
  const handleImportSuccess = (result: ImportResult) => {
    /**
     * When importing data, the /upload-data/ endpoint returns a dictionary called import_info.
     * This contains the data name, and (for constellations and night sky) values needed to set up
     * the refine menu, e.g. number of stars, maximum magnitude, whether it is a custom-ordered
     * constellation, etc.
     *
     * You may want to return something unique to your soni type, depending on what is displayed in
     * your refine menu. You can do this by adding to the validate_import function in core.py (there is
     * a template elif branch there already).
     */

    const state: NavigationState = {
      dataName: result.import_info.data_name as string,
      sourceDataRef: result.file_ref,
      soniType,
      // importedValue: result.import_info.value, for example (you would need to add this to the NavigationState definition)
    };
    navigate("../refine", { state });
  };

  // The following are needed to use the ComboBox search/filter
  const { contains } = useFilter({ sensitivity: "base" });
  const [searchValue, setSearchValue] = useState("");

  const filteredItems = useMemo(
    () => listItems.filter((item) => contains(item.label, searchValue)),
    [listItems, searchValue, contains],
  );

  const collection = useMemo(
    () => createListCollection({ items: filteredItems }),
    [filteredItems],
  );

  /**
   * The following section is called the TSX (or JSX if using JavaScript).
   * This is what is visually rendered to the browser.
   *
   * Each item in a <> tag is called a component. The vast majority of the ones used in the app
   * come from the ChakraUI v3 library. You can also use raw HTML here (you can see we use <br />
   * as a line break to create some space). In fact, all of these components will be HTML elements
   * at their core (e.g. <div>, <p>, <h1>, etc.), but they have just been uniquely styled and abstracted
   * to these more simple components.
   *
   * Some of them are Suite-specific components, made to be reusable across the app. For instance,
   * PageContainer is the outer perimeter of the UI, which contains the header and footer etc.
   *
   * Each component can take parameters (called props in React) which can tweak how things are displayed.
   * You can also pass functions in as props (including the setter from the useState), like we do below in
   * the DataImport component. Passing in the function means we can call the function from inside the child
   * component.
   *
   */
  return (
    <PageContainer>
      <Heading as="h1" wordBreak="normal" overflowWrap="normal">
        Template
      </Heading>
      <br />
      <HStack gap={0}>
        {" "}
        {/* HStack is a horizontal stack - everything in a HStack will display in a row */}
        <Text>Search for an item, pick a suggestion, or</Text>
        <DataImport
          soniType={soniType}
          onImportSuccess={handleImportSuccess}
          onImportError={setImportErrorMessage}
        />
      </HStack>
      <br />
      <br />
      <Box display="flex" justifyContent="center">
        {/* This is the dropdown component. ChakraUI components often have multiple parts 
          like this, with the '.Root' being the parent.*/}
        <Combobox.Root
          aria-label="Search data items" // ARIA labels are important for accessibility - they are read out by screen readers
          collection={collection} // This is the collection of items (in this case they are filtered above)
          onInputValueChange={(e) => setSearchValue(e.inputValue)} // This runs when something changes in the input, e.g. a letter is typed
          onValueChange={(details) => {
            // This runs when a user clicks on an item in the list

            // Match the selected item to the one in our listItems array
            const selectedItem = listItems.find(
              (item) => item.value === details.value[0],
            );

            if (selectedItem) {
              handleSelectListItem(selectedItem); // Run the handler
            }
          }}
          width={{ base: "100%", md: "50%" }} // This syntax is used to apply a different option for each viewport size (base is mobile, md is medium screens like tablets/laptops and above)
          maxWidth="600px"
        >
          <Combobox.Control>
            <InputGroup startElement={<LuTelescope size="1.1rem" />}>
              <Combobox.Input placeholder="Search for an item" />
            </InputGroup>
            <Combobox.IndicatorGroup>
              <Combobox.ClearTrigger />
              <Combobox.Trigger />
            </Combobox.IndicatorGroup>
          </Combobox.Control>
          <Portal>
            <Combobox.Positioner>
              <Combobox.Content>
                <Combobox.Empty>No items found</Combobox.Empty>

                {collection.items.map(
                  (
                    item, // Here we map each item in our collection to a Combobox.Item, displaying the label
                  ) => (
                    <Combobox.Item item={item} key={item.value}>
                      {item.label}
                      <Combobox.ItemIndicator />
                    </Combobox.Item>
                  ),
                )}
              </Combobox.Content>
            </Combobox.Positioner>
          </Portal>
        </Combobox.Root>
      </Box>
      <br />
      {/* Below is an example of conditional rendering in React. We use the logical AND operator (&&)
       to check if the importErrorMessage is empty (defaults to "" when we created the state), and renders
       the error message if not. Strictly speaking, this is usually used to evaluate if the condition on the 
       left of the && is true (boolean), but because an empty string in javaScript is 'falsy', it works the same.
      */}
      {importErrorMessage && (
        <Box width="fit-content" maxW="100%" mx="auto" mt={3}>
          <ErrorMsg
            message={importErrorMessage}
            onClose={() => setImportErrorMessage("")}
          />
        </Box>
      )}
      <br />
      <Box animation="fade-in 300ms ease-out">
        <Heading size="2xl" as="h2">
          Suggested
        </Heading>
        <br />
        <Stack
          gap="4"
          direction="row"
          wrap="wrap"
          justify={{ base: "center", md: "flex-start" }} // More mobile display - on PC the cards are left-aligned, on mobile they are centered
          animation="fade-in 300ms ease-out" // Small fade-in animation
        >
          {/* Below are the suggested data items, each one in a card */}
          {suggested.map((suggestion) => (
            <Card.Root
              width="200px"
              key={suggestion.name}
              variant="elevated"
              _hover={{ transform: "scale(1.05)" }}
              transition="transform 0.2s ease"
              cursor="pointer"
              as="button"
              aria-label={`Sonify ${suggestion.name}`}
              onClick={() => handleSelectSuggested(suggestion)}
            >
              <Box
                position="relative"
                bg="black"
                borderRadius="8px"
                overflow="hidden"
              >
                <img
                  src={getImage(suggestion.name, ".svg")} // This is a custom function to grab the '{suggestion.name}.svg' image from our /assets directory
                  alt={`A template image for ${suggestion.name}`} // You should provide alt text for all images, as this is read out by screen readers
                  style={{
                    width: "100%",
                    display: "block",
                    borderRadius: "8px",
                    animation: `twinkle ${randomRange(2, 3)}s infinite alternate`, // This is the animation we use throughout to give each icon a uniquely timed twinkle effect
                  }}
                />
              </Box>

              {/* The card body contains the data name as a title, and the description, 
              which you should add in the backend /suggested_data/template/ yaml files */}
              <Card.Body>
                <Card.Title mb="2">{suggestion.name}</Card.Title>
                <Card.Description>{suggestion.description}</Card.Description>
              </Card.Body>
            </Card.Root>
          ))}
        </Stack>
        <br />
      </Box>
    </PageContainer>
  );
}
