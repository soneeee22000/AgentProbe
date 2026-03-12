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
import { fetchProviders, type ProviderInfo } from "@/lib/api";

/** Fallback models when providers endpoint is unavailable. */
const FALLBACK_PROVIDERS: ProviderInfo[] = [
  {
    name: "groq",
    display_name: "Groq",
    available: true,
    models: [
      { id: "llama-3.1-8b-instant", name: "Llama 3.1 8B Instant" },
      { id: "llama-3.1-70b-versatile", name: "Llama 3.1 70B Versatile" },
      { id: "mixtral-8x7b-32768", name: "Mixtral 8x7B" },
      { id: "gemma2-9b-it", name: "Gemma 2 9B IT" },
    ],
  },
  {
    name: "ollama",
    display_name: "Ollama (Local)",
    available: true,
    models: [{ id: "llama3.1:8b", name: "Llama 3.1 8B" }],
  },
];

interface ModelSelectorProps {
  /** Currently selected model identifier. */
  model: string;
  /** Currently selected provider identifier. */
  provider: string;
  /** Callback when the model changes. */
  onModelChange: (model: string) => void;
  /** Callback when the provider changes. */
  onProviderChange: (provider: string) => void;
}

/**
 * Combined model and provider selector with dynamic provider discovery.
 * Fetches available providers from the backend and shows availability indicators.
 */
export function ModelSelector({
  model,
  provider,
  onModelChange,
  onProviderChange,
}: ModelSelectorProps) {
  const { data: providers = FALLBACK_PROVIDERS } = useQuery({
    queryKey: ["providers"],
    queryFn: fetchProviders,
    staleTime: 60_000,
  });

  const activeProvider = providers.find((p) => p.name === provider);
  const models = activeProvider?.models ?? [];

  return (
    <div className="flex items-center gap-2">
      {/* Provider select */}
      <Select
        value={provider}
        onValueChange={(v) => {
          if (!v) return;
          onProviderChange(v);
          const newProvider = providers.find((p) => p.name === v);
          if (
            newProvider?.models.length &&
            !newProvider.models.some((m) => m.id === model)
          ) {
            onModelChange(newProvider.models[0].id);
          }
        }}
      >
        <SelectTrigger size="sm" className="w-36 text-xs">
          <SelectValue placeholder="Provider" />
        </SelectTrigger>
        <SelectContent>
          <SelectGroup>
            <SelectLabel>Provider</SelectLabel>
            {providers.map((p) => (
              <SelectItem key={p.name} value={p.name}>
                <span className="flex items-center gap-2">
                  <span
                    className={`inline-block h-2 w-2 rounded-full ${
                      p.available ? "bg-green-500" : "bg-gray-400"
                    }`}
                  />
                  {p.display_name}
                </span>
              </SelectItem>
            ))}
          </SelectGroup>
        </SelectContent>
      </Select>

      {/* Model select */}
      <Select value={model} onValueChange={(v) => v && onModelChange(v)}>
        <SelectTrigger size="sm" className="w-52 text-xs">
          <SelectValue placeholder="Model" />
        </SelectTrigger>
        <SelectContent>
          <SelectGroup>
            <SelectLabel>
              {activeProvider?.display_name ?? provider.toUpperCase()} Models
            </SelectLabel>
            {models.map((m) => (
              <SelectItem key={m.id} value={m.id}>
                {m.name}
              </SelectItem>
            ))}
          </SelectGroup>
        </SelectContent>
      </Select>
    </div>
  );
}
