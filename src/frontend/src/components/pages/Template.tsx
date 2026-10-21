/*

This file is the template page of a sonification type that might be added to the Planetaria
module in the future, e.g. Exoplanets, Black Holes, Nebulae, etc.

It is based off of the Constellations data type, which fetches the available options from the
backend and renders them in a Combobox (a dropdown menu with search function). Depending on the
data type you want to add, you may want something closer to Lightcurves.tsx, which allows users
to enter a search query which is sent to the backend to connect to a 3rd party data source (in 
the case of light curves, using the lightkurve package). Either way, this template contains most
of the skeleton of a sonification type (you just need to add the specific organs you want!).

To use this, 

*/

import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { LuFilm, LuTelescope } from "react-icons/lu";
import PageContainer from "../ui/PageContainer";
import { getImage, randomRange } from "../../utils/assets";
import { coreAPI, templateAPI } from "../../apiConfig";
import { SuggestedData } from "./Lightcurves";

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
  const soniType = "template";

  const navigate = useNavigate();

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
        setSuggested(data);
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
    const url = `${templateAPI}/select-item/`
    const payload = {
      item: item.value
    }

    // apiRequest is a function I made to reduce repetitive boilerplate code for each API request
    const response = await apiRequest(url, payload)

    const state: NavigationState = {
      dataRef: response.file_ref,
      dataName: item.label,
      soniType, // shorthand for soniType: soniType
    };

    navigate("../refine", { state });
  };

  const handleSelectSuggested = (item: SuggestedData) => {};

  const handleImportSuccess = (result: ImportResult) => {
    const state: NavigationState = {
      dataName: result.import_info.data_name as string,
      sourceDataRef: result.file_ref,
      soniType,
      constellationType: result.import_info.stick_figure
        ? "importedStickFigure"
        : "importedBoundaries",
      importedNStars: result.import_info.star_count as number,
      importedOrder: result.import_info.custom_order as number[],
    };
    navigate("../refine", { state });
  };

  // Needed to use ComboBox search/filter
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

  return (
    <PageContainer>
      <Heading as="h1" wordBreak="normal" overflowWrap="normal">
        Constellations
      </Heading>
      <br />
      <HStack gap={0}>
        <Text>Search for a star pattern, pick a suggestion, or</Text>
        <DataImport
          soniType={soniType}
          onImportSuccess={handleImportSuccess}
          onImportError={setImportErrorMessage}
        />
      </HStack>
      <br />
      <br />
      <Box display="flex" justifyContent="center">
        <Combobox.Root
          aria-label="Search constellations and asterisms"
          collection={collection}
          onInputValueChange={(e) => setSearchValue(e.inputValue)}
          onValueChange={(details) => {
            if (details.value.length > 0) {
              const selectedItem = patternItems.find(
                (item) => item.value === details.value[0],
              );

              if (selectedItem) {
                setTimeout(() => {
                  handleSelectPattern(selectedItem);
                }, 20);
              }
            }
          }}
          width={{ base: "100%", md: "50%" }}
          maxWidth="600px"
        >
          <Combobox.Control>
            <InputGroup startElement={<LuTelescope size="1.1rem" />}>
              <Combobox.Input placeholder="Search for a constellation or asterism" />
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
                {(["Constellations", "Asterisms"] as const).map((category) => {
                  const itemsInCategory = collection.items.filter(
                    (item) => item.category === category,
                  );
                  if (itemsInCategory.length === 0) return null;
                  return (
                    <Combobox.ItemGroup key={category}>
                      <Combobox.ItemGroupLabel
                        fontWeight="bold"
                        fontSize="xs"
                        color="teal.500"
                        textTransform="uppercase"
                        letterSpacing="widest"
                        pt={2}
                        pb={1}
                      >
                        {category}
                      </Combobox.ItemGroupLabel>
                      {itemsInCategory.map((item) => (
                        <Combobox.Item item={item} key={item.value}>
                          {item.label}
                          <Combobox.ItemIndicator />
                        </Combobox.Item>
                      ))}
                    </Combobox.ItemGroup>
                  );
                })}
              </Combobox.Content>
            </Combobox.Positioner>
          </Portal>
        </Combobox.Root>
      </Box>
      <br />
      {importErrorMessage && (
        <Box width="fit-content" maxW="100%" mx="auto" mt={3}>
          <ErrorMsg
            message={importErrorMessage}
            onClose={() => setImportErrorMessage("")}
          />
        </Box>
      )}
      <Alert.Root
        colorPalette="teal"
        size="sm"
        width="fit-content"
        mb={2}
        mx="auto"
        animation="fade-in 300ms ease-out"
      >
        <Alert.Indicator>
          <LuFilm />
        </Alert.Indicator>
        <Alert.Content color="fg">
          <Alert.Title>
            <Link
              href="https://colab.research.google.com/github/Audio-Universe/sonified-night-sky/blob/main/StarsAppearingConstellationColab.ipynb"
              target="_blank"
              rel="noopener noreferrer"
            >
              Try our Google Colab tool to create an audio-visual Constellation
              →
            </Link>
          </Alert.Title>
        </Alert.Content>
      </Alert.Root>
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
          justify={{ base: "center", md: "flex-start" }}
          animation="fade-in 300ms ease-out"
        >
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
              onClick={() =>
                handleSelectPattern({
                  label: suggestion.name,
                  value: suggestion.name,
                  category: suggestion.category,
                })
              }
            >
              <Box
                position="relative"
                bg="black"
                borderRadius="8px"
                overflow="hidden"
              >
                <img
                  src={getImage(suggestion.name, ".svg")}
                  alt={`Outline of the ${suggestion.name} constellation, overlaid with its associated mythological figure.`}
                  style={{
                    width: "100%",
                    display: "block",
                    borderRadius: "8px",
                    animation: `twinkle ${randomRange(2, 3)}s infinite alternate`,
                  }}
                />
              </Box>
              <Card.Body>
                <Card.Title mb="2">{suggestion.name}</Card.Title>
                <Card.Description>{suggestion.description}</Card.Description>
              </Card.Body>
            </Card.Root>
          ))}
        </Stack>
        <br />
      </Box>
      <Text textAlign="center" fontSize="sm" color="fg.muted" mt={4}>
        Image credit:{" "}
        <Link
          href="https://noirlab.edu"
          color="gray.400"
          target="_blank"
          rel="noopener noreferrer"
        >
          NSF NOIRLab
        </Link>{" "}
        (CC BY 4.0)
      </Text>
    </PageContainer>
  );
}
