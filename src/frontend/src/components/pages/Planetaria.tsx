import { useNavigate } from "react-router-dom";
import PageContainer from "../ui/PageContainer";
import { getImage, randomRange } from "../../utils/assets";
import {
  LuExternalLink,
  LuFilm,
  LuLayers3,
  LuLightbulb,
  LuStar,
} from "react-icons/lu";

import {
  Box,
  Card,
  LinkOverlay,
  Link,
  Icon,
  Stack,
  Heading,
  Text,
  HStack,
  Badge,
} from "@chakra-ui/react";
import { SoniType, astroTypes } from "../../types/soniTypes";

export default function Planetaria() {
  const navigate = useNavigate();

  return (
    <PageContainer>
      <Heading as="h1">Planetaria</Heading>
      <br />
      <HStack flexWrap="nowrap">
        <Text>Select a data source to sonify</Text>
      </HStack>
      <br />
      <br />
      <Stack
        gap="4"
        direction="row"
        wrap="wrap"
        justify={{ base: "center", md: "flex-start" }}
        animation="fade-in 300ms ease-out"
      >
        {astroTypes.map((astroType) => {
          return (
            <Card.Root
              width="200px"
              key={astroType.key}
              _hover={{ transform: "scale(1.05)" }}
              transition="transform 0.2s ease"
              variant="elevated"
            >
              <LinkOverlay
                as={Link}
                onClick={() => navigate(astroType.page!)}
                cursor="pointer"
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    navigate(astroType.page!);
                  }
                }}
              >
                {astroType.icon ? (
                  <Box
                    bg="black"
                    height="200px"
                    width="100%"
                    display="flex"
                    alignItems="center"
                    justifyContent="center"
                    borderRadius="8px"
                  >
                    <Icon
                      boxSize="80px"
                      color="white"
                      strokeWidth={1}
                      style={{
                        animation: `twinkle ${randomRange(2, 3)}s infinite alternate`,
                      }}
                    >
                      <astroType.icon />
                    </Icon>
                  </Box>
                ) : (
                  <img
                    src={getImage(astroType.label)}
                    alt={astroType.label}
                    style={{
                      width: "100%",
                      height: "200px",
                      objectFit: "cover",
                      borderRadius: "8px",
                    }}
                  />
                )}
              </LinkOverlay>

              <Card.Body>
                <Card.Title mb="2">{astroType.label}</Card.Title>
                {astroType.label === "Constellations" && (
                  <Badge
                    animation="scale-in 500ms ease-out"
                    colorPalette="teal"
                    width="fit-content"
                    alignSelf="center"
                    mb="2"
                  >
                    <LuStar />
                    Now with Asterisms!
                  </Badge>
                )}
                <Card.Description>{astroType.description}</Card.Description>
              </Card.Body>
            </Card.Root>
          );
        })}
        <Card.Root
          width="200px"
          key="suggestions"
          _hover={{ transform: "scale(1.05)" }}
          transition="transform 0.2s ease"
          variant="subtle"
        >
          <Link
            href="https://www.audiouniverse.org/sonification-suite/suggestions-and-example-bank"
            target="_blank"
            rel="noopener noreferrer"
            cursor="pointer"
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();

                window.open(
                  "https://www.audiouniverse.org/sonification-suite/suggestions-and-example-bank",
                  "_blank",
                  "noopener,noreferrer",
                );
              }
            }}
          >
            <Box
              bg="black"
              height="200px"
              width="100%"
              display="flex"
              alignItems="center"
              justifyContent="center"
              borderRadius="8px"
            >
              <Icon
                boxSize="80px"
                color="white"
                strokeWidth={1}
                style={{
                  animation: `twinkle ${randomRange(2, 3)}s infinite alternate`,
                }}
              >
                <LuLightbulb />
              </Icon>
            </Box>
          </Link>

          <Card.Body>
            <Card.Title mb="2">
              Suggestions & Examples
              <Icon ml="3" mb="1" boxSize="4" color="gray.500">
                <LuExternalLink />
              </Icon>
            </Card.Title>
            <Card.Description>
              Pre-made examples and suggestions for using the Suite.
            </Card.Description>
          </Card.Body>
        </Card.Root>
      </Stack>
    </PageContainer>
  );
}
