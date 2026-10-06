import {
  Box,
  Button,
  CheckboxCard,
  Field,
  Image,
  Icon,
  Link,
  Text,
  Flex,
  NumberInput,
  VStack,
  Stack,
  RadioCard,
  HStack,
} from "@chakra-ui/react";

import { RefineMenuProps } from "../../types/refine_menu";
import { useState, useEffect } from "react";
import LoadingMessage from "../ui/LoadingMessage";
import ErrorMsg from "../ui/ErrorMsg";
import { constellationsAPI } from "../../apiConfig";
import { apiRequest } from "../../utils/requests";
import { InfoTip } from "../ui/ToggleTip";
import { Tooltip } from "../ui/Tooltip";
import {
  LuSquareDashed,
  LuWaypoints,
  LuArrowRight,
  LuRotateCcw,
} from "react-icons/lu";
import { ClickableConstellation, Star } from "../ui/ClickableConstellation";

export default function Constellations({
  dataRef,
  dataName,
  constellationType,
  importedNStars,
  importedOrder,
  onApply,
}: RefineMenuProps) {

  if (!constellationType) {
    throw new Error("Constellations requires constellationType");
  }

  const isImported = ["importedStickFigure", "importedBoundaries"].includes(
    constellationType,
  );

  // Helper to use when plotting - we either use a file ref (for imported data) or the pattern name (for constellations from within the Suite)
  const buildIdentifierPayload = () => {
    if (isImported) {
      if (dataRef === undefined) {
        console.error(
          "Plot requested for imported data but dataRef is undefined",
        );
        return null;
      }
      return { file_ref: dataRef };
    }
    return { name: dataName };
  };

  // const [imageSrc, setImageSrc] = useState<string | null>(null);
  const [stickFigureImage, setStickFigureImage] = useState<string | null>(null);
  const [stickFigureLoading, setStickFigureLoading] = useState(true);

  const [boundariesImage, setBoundariesImage] = useState<string | null>(null);
  const [boundariesLoading, setBoundariesLoading] = useState(true);

  // number of stars
  const [nStars, setNStars] = useState(() =>
  // If using an imported boundaries data set, set the default nStars to the number of stars in the data, or 100 (whichever is less)
    constellationType === "importedBoundaries" &&
    importedNStars &&
    importedNStars < 100
      ? String(importedNStars)
      : "100",
  );

  const maxStars =
  // Similarly, set the maximum number of stars to the number of stars in imported dataset (if using)
    constellationType === "importedBoundaries" && importedNStars
      ? importedNStars
      : 300;

  const [applyLoading, setApplyLoading] = useState(false);
  const [filterType, setFilterType] = useState(
    constellationType === "importedBoundaries" ? "boundaries" : "stickFigure",
  );

  // Interactive plot - default 'on' if using an imported dataset with custom order
  const [customOrderOn, setCustomOrderOn] = useState(!!importedOrder && importedOrder.length > 0);

  const [order, setOrder] = useState<number[]>(importedOrder ?? []);
  const [stars, setStars] = useState<Star[]>([]);
  const [lines, setLines] = useState<[number, number][]>([]);
  const [interactiveLoading, setInteractiveLoading] = useState(false);

  const fetchStickFigure = async () => {
    const identifier = buildIdentifierPayload();
    if (!identifier) {
      setStickFigureLoading(false);
      return;
    }
    try {
      const response = await apiRequest(`${constellationsAPI}/get-and-plot/`, {
        ...identifier,
        n_stars: nStars,
        stick_figure: true,
      });
      setStickFigureImage(`data:image/svg+xml;base64,${response.image}`);
    } catch (error) {
      console.error("Failed to fetch stick figure plot:", error);
    } finally {
      setStickFigureLoading(false);
    }
  };

  const fetchBoundaries = async () => {
    const identifier = buildIdentifierPayload();
    if (!identifier) {
      setBoundariesLoading(false);
      return;
    }
    try {
      const response = await apiRequest(`${constellationsAPI}/get-and-plot/`, {
        ...identifier,
        n_stars: nStars,
        stick_figure: false,
      });
      setBoundariesImage(`data:image/svg+xml;base64,${response.image}`);
    } catch (error) {
      console.error("Failed to fetch boundaries plot:", error);
    } finally {
      setBoundariesLoading(false);
    }
  };

  // Fetch stick figure on mount if needed
  useEffect(() => {
    if (
      ["constellation", "asterism", "importedStickFigure"].includes(
        constellationType,
      )
    ) {
      fetchStickFigure();
    }
  }, []);

  // Fetch boundaries plot on mount if needed, and re-fetch whenever nStars changes
  useEffect(() => {

    if (["asterism", "importedStickFigure"].includes(constellationType))
      // Don't fetch boundaries if this is asterism or imported stick figure
      return;

    const num = Number(nStars);
    if (isNaN(num) || num < 1 || num > maxStars || !Number.isInteger(num)) {
      return; // don't plot if input is invalid
    }
    fetchBoundaries();
  }, [nStars]);

  useEffect(() => {
    if (!customOrderOn) return;
    if (lines.length > 0 && stars.length > 0) return;
    plotInteractive();
  }, [customOrderOn]);

  const plotInteractive = async () => {
    setInteractiveLoading(true);

    const endpoint = `${constellationsAPI}/get-plotting-data/`;
    const payload =
      constellationType === "importedStickFigure"
        ? {
            file_ref: dataRef,
          }
        : {
            name: dataName,
          };

    const result = await apiRequest(endpoint, payload);

    setLines(result.lines);
    setStars(result.stars);
    setInteractiveLoading(false);
  };

  const handleClickApply = async () => {
    setApplyLoading(true);

    const endpoint = `${constellationsAPI}/save-refined/`;
    const payload = {
      ...(["importedStickFigure", "importedBoundaries"].includes(
        constellationType,
      )
        ? { file_ref: dataRef }
        : { name: dataName }),
      stick_figure: filterType === "stickFigure",
      n_stars: nStars,
      ...(filterType === "stickFigure" && customOrderOn && { order }),
    };

    const result = await apiRequest(endpoint, payload);

    if (onApply) {
      onApply({
        newRef: result.file_ref,
        newRa: result.ra,
        newDec: result.dec,
        nStars: filterType === "boundaries" ? Number(nStars) : undefined,
        customOrder: customOrderOn
      });
    }
    setApplyLoading(false);
  };

  const cards = [
    {
      value: "stickFigure",
      title: "Stick Figure",
      description: `Sonify the stars that make up the classic shape of ${dataName}`,
      icon: <LuWaypoints />,
      disabled: constellationType === "importedBoundaries",
      disabledTip:
        "Stick figure not available for an imported constellation which used boundaries",
    },
    {
      value: "boundaries",
      title: "Boundaries",
      description: (
        <>
          Sonify the brightest stars within the{" "}
          <Link
            href="https://en.wikipedia.org/wiki/IAU_designated_constellations"
            color="teal.500"
            textDecoration="underline"
            target="_blank"
            rel="noopener noreferrer"
          >
            constellation boundaries
          </Link>
        </>
      ),
      icon: <LuSquareDashed />,
      disabled: ["asterism", "importedStickFigure"].includes(
        constellationType,
      ),
      disabledTip: `Boundaries not available for 
      ${
        constellationType === "asterism"
          ? "asterisms (some span multiple constellation boundaries!)"
          : "an imported constellation which used stick figure previously"
      }`,
    },
  ];

  // Track whether or not to disable the continue button
  const invalidNStars =
    (filterType === "boundaries" &&
      (Number(nStars) > maxStars ||
        !Number.isInteger(Number(nStars)) ||
        Number(nStars) < 1)) ||
    nStars.length === 0;

  // whether a user has clicked on all of the stars yet (if picking custom order)
  const unselectedStars =
    filterType === "stickFigure" &&
    customOrderOn &&
    order.length !== stars.length;

  return (
    <Stack
      gap="10"
      align="start"
      justify="center"
      direction={{ base: "column", md: "row" }}
    >
      <Box flex="1">
        <VStack align="center" justify="center" gap={{ md: "10" }} w="auto">
          <RadioCard.Root
            value={filterType}
            colorPalette="teal"
            onValueChange={(e) => setFilterType(e.value!)}
          >
            <Stack align="stretch" direction={{ base: "column", md: "row" }}>
              {cards.map((card) => (
                <Tooltip disabled={!card.disabled} content={card.disabledTip}>
                  <RadioCard.Item
                    key={card.value}
                    value={card.value}
                    disabled={card.disabled}
                    cursor={card.disabled ? 'disabled' : 'default'}
                  >
                    <RadioCard.ItemHiddenInput />
                    <RadioCard.ItemControl>
                      <RadioCard.ItemContent>
                        <Icon size="xl" color="fg.muted" mb="2">
                          {card.icon}
                        </Icon>
                        <RadioCard.ItemText textStyle="md">
                          {card.title}
                        </RadioCard.ItemText>
                        <RadioCard.ItemDescription>
                          {card.description}
                        </RadioCard.ItemDescription>
                      </RadioCard.ItemContent>
                      <RadioCard.ItemIndicator />
                    </RadioCard.ItemControl>
                  </RadioCard.Item>
                </Tooltip>
              ))}
            </Stack>
          </RadioCard.Root>
          {filterType === "stickFigure" && (
            <HStack>
              <CheckboxCard.Root
                colorPalette="teal"
                checked={customOrderOn}
                onCheckedChange={(e) => setCustomOrderOn(!!e.checked)}
              >
                <CheckboxCard.HiddenInput />
                <CheckboxCard.Control>
                  <CheckboxCard.Content>
                    <CheckboxCard.Label>Choose custom order</CheckboxCard.Label>
                  </CheckboxCard.Content>
                  <CheckboxCard.Indicator />
                </CheckboxCard.Control>
              </CheckboxCard.Root>
              <InfoTip
                positioning={{ placement: "right" }}
                contentProps={{ maxW: "300px" }}
                content="Use this if you want the stars to play in a specific order. In the next step, your chosen order will automatically be mapped to Time."
              />
            </HStack>
          )}
          {filterType === "boundaries" && (
            <HStack gap={10} pt={{ base: 6, md: 0 }}>
              <Field.Root width="auto" invalid={invalidNStars}>
                <HStack>
                  <Field.Label>Number of stars</Field.Label>
                  <InfoTip
                    content="Selects the brightest stars up to the number specified."
                    positioning={{ placement: "right" }}
                  />
                </HStack>
                <NumberInput.Root
                  min={1}
                  max={maxStars}
                  step={1}
                  value={nStars}
                  onValueChange={(e) => {
                    setNStars(e.value);
                  }}
                  inputMode="numeric"
                >
                  <NumberInput.Input aria-valuetext={`${nStars} stars`} />
                </NumberInput.Root>
                {Number(nStars) > maxStars && (
                  <Field.ErrorText>Maximum {maxStars}</Field.ErrorText>
                )}
              </Field.Root>
            </HStack>
          )}
          <Box display={{ base: "none", md: "flex" }}>
            <Tooltip
              content={
                unselectedStars
                  ? "Select all stars to continue"
                  : "Invalid number of stars"
              }
              disabled={!unselectedStars && !invalidNStars}
            >
              <Button
                w="auto"
                disabled={unselectedStars || invalidNStars}
                onClick={handleClickApply}
                colorPalette="teal"
                loading={applyLoading}
                loadingText="Saving..."
              >
                Apply & Continue <LuArrowRight />
              </Button>
            </Tooltip>
          </Box>
        </VStack>
      </Box>
      <Box flex="1">
        <Box flex="1" borderWidth="1px" borderRadius="md">
          {filterType === "stickFigure" &&
            (customOrderOn ? (
              interactiveLoading ? (
                <LoadingMessage msg="" icon="pulsar" />
              ) : (
                <>
                  <Flex direction="column" gap={3} p={4}>
                    <HStack minH="8" gap={5}>
                      <Text fontSize="sm" color="fg.muted">
                        {order.length === 0
                          ? "Click the stars in the order you'd like them to play."
                          : `${order.length} of ${stars.length} stars selected`}
                      </Text>
                      {order.length > 1 && (
                        <Button
                          animation="fade-in 300ms ease-out"
                          colorPalette="teal"
                          size="xs"
                          variant="surface"
                          onClick={() => setOrder([])}
                        >
                          <LuRotateCcw />
                          Reset
                        </Button>
                      )}
                    </HStack>

                    <ClickableConstellation
                      stars={stars}
                      lines={lines}
                      order={order}
                      onOrderChange={setOrder}
                    />
                  </Flex>
                </>
              )
            ) : stickFigureLoading ? (
              <LoadingMessage msg="" icon="pulsar" />
            ) : stickFigureImage ? (
              <Image
                src={stickFigureImage}
                alt={`The stick figure shape of ${dataName}.`}
                animation="fade-in 300ms ease-out"
                rounded="md"
              />
            ) : (
              <ErrorMsg message="Unable to plot data." />
            ))}
          {filterType === "boundaries" &&
            (boundariesLoading ? (
              <LoadingMessage msg="" icon="pulsar" />
            ) : boundariesImage ? (
              <Image
                src={boundariesImage}
                alt={`A plot of the brightest ${nStars} in ${dataName}.`}
                animation="fade-in 300ms ease-out"
                rounded="md"
              />
            ) : (
              <ErrorMsg message="Unable to plot data." />
            ))}
        </Box>
        <Text textAlign="center" fontSize="xs" color="fg.muted" mt={4}>
          <Link
            href="https://github.com/Stellarium/stellarium-skycultures/tree/master/western"
            color="gray.400"
            target="_blank"
            rel="noopener noreferrer"
          >
            Western Skyculture
          </Link>{" "}
          lines by Stellarium's team{" "}
          <Link
            href="https://creativecommons.org/licenses/by-sa/4.0/"
            color="gray.400"
            target="_blank"
            rel="noopener noreferrer"
          >
            (CC BY-SA)
          </Link>
        </Text>
      </Box>

      <Box w="100%" display={{ base: "block", md: "none" }}>
        <Tooltip
          content={
            unselectedStars
              ? "Select all stars to continue"
              : "Invalid number of stars"
          }
          disabled={!unselectedStars && !invalidNStars}
        >
          <Button
            w="auto"
            disabled={unselectedStars || invalidNStars}
            onClick={handleClickApply}
            colorPalette="teal"
            loading={applyLoading}
            loadingText="Saving..."
          >
            Apply & Continue <LuArrowRight />
          </Button>
        </Tooltip>
      </Box>
    </Stack>
  );
}
