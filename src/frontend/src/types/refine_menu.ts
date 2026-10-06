export interface ApplyResult {
  newRef: string;
  idColumn?: string | null;
  newRa?: number;
  newDec?: number;
  nStars?: number;
  customOrder?: boolean;
}

export interface RefineMenuProps {
  dataRef: string;
  dataName?: string;
  constellationType?: ConstellationType;
  importedNStars?: number | null;
  importedOrder?: number[] | null;
  importedMaxMag?: number | null;
  idColumn?: string | null;
  onApply?: (result: ApplyResult) => void;
}

export type ConstellationType =
  | 'constellation'
  | 'asterism'
  | 'importedStickFigure'
  | 'importedBoundaries'
  | null;