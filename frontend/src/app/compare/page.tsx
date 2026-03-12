"use client";

import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { CompareControls } from "@/components/compare/compare-controls";
import { CompareTraceLane } from "@/components/compare/compare-trace-lane";
import { CompareStatsBar } from "@/components/compare/compare-stats-bar";
import { useCompareStore } from "@/store/compare-store";

/**
 * Model comparison page. Allows running two models side-by-side on the
 * same query and comparing their step traces and performance metrics.
 */
export default function ComparePage() {
  const leftSteps = useCompareStore((s) => s.leftSteps);
  const rightSteps = useCompareStore((s) => s.rightSteps);
  const leftStatus = useCompareStore((s) => s.leftStatus);
  const rightStatus = useCompareStore((s) => s.rightStatus);
  const leftModel = useCompareStore((s) => s.leftModel);
  const rightModel = useCompareStore((s) => s.rightModel);
  const leftProvider = useCompareStore((s) => s.leftProvider);
  const rightProvider = useCompareStore((s) => s.rightProvider);

  const leftLabel = `${leftModel} (${leftProvider})`;
  const rightLabel = `${rightModel} (${rightProvider})`;

  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <CompareControls />

        {/* Side-by-side trace lanes */}
        <main className="grid flex-1 grid-cols-2 gap-4 overflow-auto p-4">
          <CompareTraceLane
            steps={leftSteps}
            status={leftStatus}
            label={leftLabel}
          />
          <CompareTraceLane
            steps={rightSteps}
            status={rightStatus}
            label={rightLabel}
          />
        </main>

        {/* Bottom stats bar — visible after both runs complete */}
        <CompareStatsBar
          leftSteps={leftSteps}
          rightSteps={rightSteps}
          leftStatus={leftStatus}
          rightStatus={rightStatus}
          leftLabel={leftLabel}
          rightLabel={rightLabel}
        />
      </div>
    </div>
  );
}
