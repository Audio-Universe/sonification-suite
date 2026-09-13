export interface ApplyResult {
  newRef: string;
  idColumn?: string | null;
  newRa?: number;
  newDec?: number;
  nStars?: number;
}

export interface RefineMenuProps {
  dataRef: string;
  dataName?: string;
  constellationType?: 'constellation' | 'asterism' | 'importedStickFigure' | 'importedBoundaries'
  idColumn?: string | null;
  onApply?: (result: ApplyResult) => void;
}