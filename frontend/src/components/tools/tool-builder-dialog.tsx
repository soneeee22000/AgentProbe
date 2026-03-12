"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { createCustomTool } from "@/lib/api";

/**
 * Dialog for creating a new custom tool.
 * Supports HTTP and static tool types.
 */
export function ToolBuilderDialog() {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [toolType, setToolType] = useState<"static" | "http">("static");
  const [staticResponse, setStaticResponse] = useState("");
  const [httpUrl, setHttpUrl] = useState("");
  const [httpMethod, setHttpMethod] = useState("GET");
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: createCustomTool,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["custom-tools"] });
      setOpen(false);
      setName("");
      setDescription("");
      setStaticResponse("");
      setHttpUrl("");
    },
  });

  function handleSubmit() {
    const config =
      toolType === "static"
        ? { response: staticResponse }
        : { url: httpUrl, method: httpMethod };

    mutation.mutate({
      name,
      description,
      tool_type: toolType,
      config,
    });
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger render={<Button variant="outline" size="sm" />}>
        Create Tool
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Custom Tool</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">Name</label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="my_tool"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Description</label>
            <Input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What does this tool do?"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Type</label>
            <select
              value={toolType}
              onChange={(e) => setToolType(e.target.value as "static" | "http")}
              className="w-full rounded-md border border-border bg-secondary px-3 py-2 text-sm"
            >
              <option value="static">Static Response</option>
              <option value="http">HTTP Request</option>
            </select>
          </div>

          {toolType === "static" ? (
            <div>
              <label className="text-sm font-medium">Response</label>
              <textarea
                value={staticResponse}
                onChange={(e) => setStaticResponse(e.target.value)}
                placeholder="The response this tool will return"
                className="w-full rounded-md border border-border bg-secondary px-3 py-2 text-sm"
                rows={3}
              />
            </div>
          ) : (
            <>
              <div>
                <label className="text-sm font-medium">URL</label>
                <Input
                  value={httpUrl}
                  onChange={(e) => setHttpUrl(e.target.value)}
                  placeholder="https://api.example.com/endpoint"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Method</label>
                <select
                  value={httpMethod}
                  onChange={(e) => setHttpMethod(e.target.value)}
                  className="w-full rounded-md border border-border bg-secondary px-3 py-2 text-sm"
                >
                  <option value="GET">GET</option>
                  <option value="POST">POST</option>
                </select>
              </div>
            </>
          )}

          <Button
            onClick={handleSubmit}
            disabled={!name || !description || mutation.isPending}
            className="w-full"
          >
            {mutation.isPending ? "Creating..." : "Create Tool"}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
