"use client";

import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const MODELS = [
  { value: "all", label: "All Models" },
  { value: "llama-3.1-8b-instant", label: "Llama 3.1 8B" },
  { value: "llama-3.1-70b-versatile", label: "Llama 3.1 70B" },
  { value: "mixtral-8x7b-32768", label: "Mixtral 8x7B" },
  { value: "gemma2-9b-it", label: "Gemma 2 9B" },
];

const STATUSES = [
  { value: "all", label: "All Statuses" },
  { value: "success", label: "Success" },
  { value: "failed", label: "Failed" },
];

interface RunFiltersProps {
  /** Currently selected model filter. */
  model: string;
  /** Currently selected status filter. */
  status: string;
  /** Search query text. */
  search: string;
  /** Callback when model filter changes. */
  onModelChange: (model: string) => void;
  /** Callback when status filter changes. */
  onStatusChange: (status: string) => void;
  /** Callback when search text changes. */
  onSearchChange: (search: string) => void;
}

/**
 * Filter controls for the run history table.
 * Provides model dropdown, status dropdown, and text search.
 */
export function RunFilters({
  model,
  status,
  search,
  onModelChange,
  onStatusChange,
  onSearchChange,
}: RunFiltersProps) {
  return (
    <div className="flex items-center gap-3">
      <Input
        placeholder="Search queries..."
        value={search}
        onChange={(e) => onSearchChange(e.target.value)}
        className="w-64 text-sm"
      />

      <Select value={model} onValueChange={(v) => v && onModelChange(v)}>
        <SelectTrigger size="sm" className="w-44 text-xs">
          <SelectValue placeholder="Model" />
        </SelectTrigger>
        <SelectContent>
          <SelectGroup>
            <SelectLabel>Model</SelectLabel>
            {MODELS.map((m) => (
              <SelectItem key={m.value} value={m.value}>
                {m.label}
              </SelectItem>
            ))}
          </SelectGroup>
        </SelectContent>
      </Select>

      <Select value={status} onValueChange={(v) => v && onStatusChange(v)}>
        <SelectTrigger size="sm" className="w-36 text-xs">
          <SelectValue placeholder="Status" />
        </SelectTrigger>
        <SelectContent>
          <SelectGroup>
            <SelectLabel>Status</SelectLabel>
            {STATUSES.map((s) => (
              <SelectItem key={s.value} value={s.value}>
                {s.label}
              </SelectItem>
            ))}
          </SelectGroup>
        </SelectContent>
      </Select>
    </div>
  );
}
