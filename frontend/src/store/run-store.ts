import { create } from "zustand";
import type { AgentStep } from "@/lib/api";

interface StepCounts {
  thought: number;
  action: number;
  observation: number;
  error: number;
}

interface RunSummary {
  run_id: string;
  succeeded: boolean;
  step_count: number;
  total_tokens: number;
  duration_ms?: number;
  failures: string[];
}

interface RunStore {
  // State
  isRunning: boolean;
  steps: AgentStep[];
  stepCounts: StepCounts;
  failures: string[];
  summary: RunSummary | null;
  activeToolName: string | null;
  query: string;
  model: string;
  provider: string;

  // Actions
  setQuery: (query: string) => void;
  setModel: (model: string) => void;
  setProvider: (provider: string) => void;
  startRun: () => void;
  addStep: (step: AgentStep) => void;
  setSummary: (summary: RunSummary) => void;
  endRun: () => void;
  reset: () => void;
}

const initialStepCounts: StepCounts = {
  thought: 0,
  action: 0,
  observation: 0,
  error: 0,
};

export const useRunStore = create<RunStore>((set) => ({
  isRunning: false,
  steps: [],
  stepCounts: { ...initialStepCounts },
  failures: [],
  summary: null,
  activeToolName: null,
  query: "",
  model: "llama-3.1-8b-instant",
  provider: "groq",

  setQuery: (query) => set({ query }),
  setModel: (model) => set({ model }),
  setProvider: (provider) => set({ provider }),

  startRun: () =>
    set({
      isRunning: true,
      steps: [],
      stepCounts: { ...initialStepCounts },
      failures: [],
      summary: null,
      activeToolName: null,
    }),

  addStep: (step) =>
    set((state) => {
      const newSteps = [...state.steps, step];
      const newCounts = { ...state.stepCounts };
      const newFailures = [...state.failures];
      let activeToolName = state.activeToolName;

      if (step.step_type === "thought") newCounts.thought++;
      if (step.step_type === "action") {
        newCounts.action++;
        activeToolName = step.tool_name || null;
      }
      if (step.step_type === "observation") newCounts.observation++;
      if (step.step_type === "error") newCounts.error++;

      if (step.failure_type && step.failure_type !== "none") {
        newFailures.push(step.failure_type);
      }

      // Parse system summary
      if (step.step_type === "system" && step.content.startsWith("{")) {
        try {
          const summary = JSON.parse(step.content);
          return {
            steps: newSteps,
            stepCounts: newCounts,
            failures: newFailures,
            activeToolName,
            summary,
          };
        } catch {
          // Ignore malformed JSON
        }
      }

      return {
        steps: newSteps,
        stepCounts: newCounts,
        failures: newFailures,
        activeToolName,
      };
    }),

  setSummary: (summary) => set({ summary }),
  endRun: () => set({ isRunning: false }),
  reset: () =>
    set({
      isRunning: false,
      steps: [],
      stepCounts: { ...initialStepCounts },
      failures: [],
      summary: null,
      activeToolName: null,
    }),
}));
