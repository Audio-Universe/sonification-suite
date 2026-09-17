import { useNavigate } from "react-router-dom";
import PageContainer from "../ui/PageContainer";
import { nightSkyAPI } from "../../apiConfig";
import { apiRequest } from "../../utils/requests";
import { Box, Card, Heading, HStack, Link, Text, VStack, Alert } from "@chakra-ui/react";
import ObserverSetup, { ObserverValues } from "../utils/ObserverSetup";
import { NavigationState } from "../../types/navigation";
import { DataImport, ImportResult } from "../utils/DataImport";
import { useState } from "react";
import ErrorMsg from "../ui/ErrorMsg";
import { LuFilm } from "react-icons/lu";

export default function NightSky() {
  const soniType = "night_sky";
  const navigate = useNavigate();

  const [importErrorMessage, setImportErrorMessage] = useState("")

  const handleSubmit = async ({
    latitude,
    longitude,
    locationName,
    orientation,
    dateTime,
  }: ObserverValues) => {
    const response = await apiRequest(
      `${nightSkyAPI}/get-stars/`,
      {
        latitude,
        longitude,
        facing: orientation,
        date_time: dateTime,
      },
      "POST",
    );

    const state: NavigationState = {
      dataName: locationName,
      sourceDataRef: response.file_ref,
      soniType
    };
    navigate("../refine", { state });
  };

  const handleImportSuccess = (result: ImportResult) => {
      const state: NavigationState = {
        dataName: result.import_info.data_name as string,
        sourceDataRef: result.file_ref,
        soniType,
        importedMaxMag: result.import_info.max_magnitude as number,
      };
      navigate("../refine", { state });
    }

  return (
    <PageContainer>
      <Heading as="h1">Night Sky</Heading>
      <br />
      <HStack gap={0}>
        <Text>Select a location and time to get local stars, or</Text>
        <DataImport
          soniType={soniType}
          onImportSuccess={handleImportSuccess}
          onImportError={setImportErrorMessage}
        />
      </HStack>
      <br />
      <Alert.Root
        colorPalette="teal"
        size="sm"
        width="fit-content"
        mb={6}
        mx="auto"
        animation="fade-in 300ms ease-out"
      >
        <Alert.Indicator>
          <LuFilm />
        </Alert.Indicator>
        <Alert.Content color="fg">
          <Alert.Title>
            <Link
              href="https://colab.research.google.com/github/Audio-Universe/sonified-night-sky/blob/main/StarsAppearingColab.ipynb"
              target="_blank"
              rel="noopener noreferrer"
            >
              Try our Google Colab tool to create an audio-visual Night Sky →
            </Link>
          </Alert.Title>
        </Alert.Content>
      </Alert.Root>
      {importErrorMessage && (
        <Box width="fit-content" maxW="100%" mx="auto" mb={6}>
          <ErrorMsg
            message={importErrorMessage}
            onClose={() => setImportErrorMessage("")}
          />
        </Box>
      )}
      <Box display="flex" justifyContent="center">
        <ObserverSetup onSubmit={handleSubmit} />
      </Box>
    </PageContainer>
  );
}
