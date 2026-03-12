"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { fetchCustomTools, deleteCustomTool } from "@/lib/api";

/**
 * Displays a list of user-created custom tools with delete buttons.
 */
export function CustomToolList() {
  const queryClient = useQueryClient();
  const { data: tools = [] } = useQuery({
    queryKey: ["custom-tools"],
    queryFn: fetchCustomTools,
  });

  const deleteMutation = useMutation({
    mutationFn: deleteCustomTool,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["custom-tools"] });
    },
  });

  if (tools.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No custom tools yet.</p>
    );
  }

  return (
    <div className="space-y-2">
      {tools.map((tool) => (
        <div
          key={tool.id}
          className="flex items-center justify-between rounded-md border border-border p-3"
        >
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">{tool.name}</span>
              <Badge variant="outline" className="text-xs">
                {tool.tool_type}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground">{tool.description}</p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => deleteMutation.mutate(tool.id)}
            disabled={deleteMutation.isPending}
          >
            Delete
          </Button>
        </div>
      ))}
    </div>
  );
}
