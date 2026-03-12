"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { createPromptTemplate } from "@/lib/api";

/**
 * Editor form for creating new system prompt templates.
 */
export function PromptEditor() {
  const [name, setName] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: createPromptTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["prompts"] });
      setName("");
      setSystemPrompt("");
    },
  });

  return (
    <div className="space-y-4 rounded-lg border border-border p-4">
      <h3 className="text-sm font-medium">New Prompt Template</h3>
      <div>
        <label className="text-xs text-muted-foreground">Name</label>
        <Input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="My Custom Prompt"
        />
      </div>
      <div>
        <label className="text-xs text-muted-foreground">System Prompt</label>
        <textarea
          value={systemPrompt}
          onChange={(e) => setSystemPrompt(e.target.value)}
          placeholder="You are a helpful assistant that..."
          className="w-full rounded-md border border-border bg-secondary px-3 py-2 text-sm font-mono"
          rows={8}
        />
      </div>
      <Button
        onClick={() => mutation.mutate({ name, system_prompt: systemPrompt })}
        disabled={!name || !systemPrompt || mutation.isPending}
      >
        {mutation.isPending ? "Saving..." : "Save Template"}
      </Button>
    </div>
  );
}
