export type Arm = {
  id: string;
  label: string;
  unfiltered: boolean;
  n: number;
  states: number;
  success: number;
  successRate: number;
  wilson95: [number, number];
  warmP50Ms: number | null;
  warmP95Ms: number | null;
  dangerous: number;
  abstained: number;
  invalid: number;
  repDisagreeStates: number;
  meanConfidence: number;
};

export type Run = {
  correct: boolean;
  abstained: boolean;
  invalid: boolean;
  dangerous: boolean;
  decisionMs: number | null;
  confidence: number | null;
  entropy: number | null;
  margin: number | null;
  selected: string | null;
  goldAction: string | null;
  expectAbstain: boolean | null;
  repetition: number | null;
  coldOrWarm: string | null;
  tokensIn: number | null;
  tokensOut: number | null;
  costUsd: number | null;
};

export type StateArm = {
  runs: Run[];
  n: number;
  successRate: number | null;
  p50Ms: number | null;
  unanimous: boolean;
};

export type State = {
  id: string;
  family: string;
  legalCount: number;
  deterministicSolution: string | null;
  arms: Record<string, StateArm>;
};

export type Family = {
  name: string;
  states: number;
  runs: number;
  correct: number;
  abstained: number;
  invalid: number;
  dangerous: number;
};

export type Matrix = {
  runId: string;
  arms: Arm[];
  states: State[];
  families: Family[];
  armOrder: string[];
};
