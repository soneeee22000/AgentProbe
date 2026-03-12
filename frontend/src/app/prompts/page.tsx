"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { PromptEditor } from "@/components/prompts/prompt-editor";
import { fetchPromptTemplates, deletePromptTemplate } from "@/lib/api";

/**
 * Prompt management page — create, view, and delete system prompt templates.
 */
export default function PromptsPage() {
  const queryClient = useQueryClient();
  const { data: templates = [], isLoading } = useQuery({
    queryKey: ["prompts"],
    queryFn: fetchPromptTemplates,
  });

  const deleteMutation = useMutation({
    mutationFn: deletePromptTemplate,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["prompts"] });
    },
  });

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-bold">Prompt Templates</h1>
        <p className="text-sm text-muted-foreground">
          Create custom system prompts to modify agent behavior.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <PromptEditor />

        <div className="space-y-4">
          <h3 className="text-sm font-medium">Saved Templates</h3>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : templates.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No templates yet. Create one to get started.
            </p>
          ) : (
            <div className="space-y-3">
              {templates.map((t) => (
                <div
                  key={t.id}
                  className="rounded-lg border border-border p-4 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{t.name}</span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => deleteMutation.mutate(t.id)}
                    >
                      Delete
                    </Button>
                  </div>
                  <pre className="text-xs text-muted-foreground whitespace-pre-wrap font-mono max-h-32 overflow-auto">
                    {t.system_prompt}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
