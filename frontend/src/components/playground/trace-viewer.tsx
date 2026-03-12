"use client";

import { useEffect, useRef } from "react";
import { useRunStore } from "@/store/run-store";
import { ScrollArea } from "@/components/ui/scroll-area";
import { StepCard } from "@/components/playground/step-card";

/**
 * Centre panel that displays the stream of agent trace steps.
 * Auto-scrolls to the bottom as new steps arrive.
 * Filters out system summary steps (JSON payloads parsed by the store).
 */
export function TraceViewer() {
  const steps = useRunStore((s) => s.steps);
  const bottomRef = useRef<HTMLDivElement>(null);

  /** Scroll to the latest step whenever the list grows. */
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [steps.length]);

  /** Hide system steps whose content is a JSON summary blob. */
  const visibleSteps = steps.filter(
    (s) => !(s.step_type === "system" && s.content.startsWith("{")),
  );

  if (visibleSteps.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center text-sm text-muted-foreground">
        Run a query to see the agent trace here.
      </div>
    );
  }

  return (
    <ScrollArea className="flex-1">
      <div className="flex flex-col gap-2 p-4">
        {visibleSteps.map((step) => (
          <StepCard key={`${step.step_index}-${step.step_type}`} step={step} />
        ))}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
