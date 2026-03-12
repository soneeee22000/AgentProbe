"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { fetchPromptTemplates } from "@/lib/api";

interface PromptSelectorProps {
  /** Currently selected prompt template ID, or "default" for built-in. */
  value: string;
  /** Callback when selection changes. */
  onChange: (promptId: string) => void;
}

/**
 * Dropdown selector for choosing a system prompt template.
 * Shows built-in default plus user-created templates.
 */
export function PromptSelector({ value, onChange }: PromptSelectorProps) {
  const { data: templates = [] } = useQuery({
    queryKey: ["prompts"],
    queryFn: fetchPromptTemplates,
    staleTime: 30_000,
  });

  return (
    <Select value={value} onValueChange={(v) => v && onChange(v)}>
      <SelectTrigger size="sm" className="w-44 text-xs">
        <SelectValue placeholder="System Prompt" />
      </SelectTrigger>
      <SelectContent>
        <SelectGroup>
          <SelectLabel>Prompt Templates</SelectLabel>
          <SelectItem value="default">Default (Built-in)</SelectItem>
          {templates.map((t) => (
            <SelectItem key={t.id} value={t.id}>
              {t.name}
            </SelectItem>
          ))}
        </SelectGroup>
      </SelectContent>
    </Select>
  );
}
