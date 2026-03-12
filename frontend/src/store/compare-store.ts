import { create } from "zustand";
import type { AgentStep } from "@/lib/api";

type RunStatus = "idle" | "running" | "complete" | "failed";

interface CompareStore {
  /** Left panel model identifier. */
  leftModel: string;
  /** Right panel model identifier. */
  rightModel: string;
  /** Left panel provider name. */
  leftProvider: string;
  /** Right panel provider name. */
  rightProvider: string;
  /** Shared query string for both runs. */
  query: string;
  /** Accumulated steps for the left model run. */
  leftSteps: AgentStep[];
  /** Accumulated steps for the right model run. */
  rightSteps: AgentStep[];
  /** Execution status of the left model run. */
  leftStatus: RunStatus;
  /** Execution status of the right model run. */
  rightStatus: RunStatus;

  /** Set the left panel model. */
  setLeftModel: (model: string) => void;
  /** Set the right panel model. */
  setRightModel: (model: string) => void;
  /** Set the left panel provider. */
  setLeftProvider: (provider: string) => void;
  /** Set the right panel provider. */
  setRightProvider: (provider: string) => void;
  /** Set the shared query. */
  setQuery: (query: string) => void;
  /** Append a step to the left run trace. */
  addLeftStep: (step: AgentStep) => void;
  /** Append a step to the right run trace. */
  addRightStep: (step: AgentStep) => void;
  /** Update the left run status. */
  setLeftStatus: (status: RunStatus) => void;
  /** Update the right run status. */
  setRightStatus: (status: RunStatus) => void;
  /** Reset both runs to initial state. */
  reset: () => void;
}

export const useCompareStore = create<CompareStore>((set) => ({
  leftModel: "llama-3.1-8b-instant",
  rightModel: "llama3-70b-8192",
  leftProvider: "groq",
  rightProvider: "groq",
  query: "",
  leftSteps: [],
  rightSteps: [],
  leftStatus: "idle",
  rightStatus: "idle",

  setLeftModel: (model) => set({ leftModel: model }),
  setRightModel: (model) => set({ rightModel: model }),
  setLeftProvider: (provider) => set({ leftProvider: provider }),
  setRightProvider: (provider) => set({ rightProvider: provider }),
  setQuery: (query) => set({ query }),

  addLeftStep: (step) =>
    set((state) => ({ leftSteps: [...state.leftSteps, step] })),

  addRightStep: (step) =>
    set((state) => ({ rightSteps: [...state.rightSteps, step] })),

  setLeftStatus: (status) => set({ leftStatus: status }),
  setRightStatus: (status) => set({ rightStatus: status }),

  reset: () =>
    set({
      leftSteps: [],
      rightSteps: [],
      leftStatus: "idle",
      rightStatus: "idle",
    }),
}));
