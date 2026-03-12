"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

interface NavItem {
  label: string;
  href: string;
  icon: string;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Playground", href: "/", icon: "\u25B6" },
  { label: "Runs", href: "/runs", icon: "\u25F7" },
  { label: "Benchmarks", href: "/benchmarks", icon: "\u25C8" },
  { label: "Analytics", href: "/analytics", icon: "\u25C6" },
  { label: "Compare", href: "/compare", icon: "\u27FA" },
  { label: "Prompts", href: "/prompts", icon: "\u270E" },
];

/**
 * Returns true if the given href matches the current pathname.
 * Exact match for root, prefix match for other routes.
 */
function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname.startsWith(href);
}

/**
 * Application sidebar with navigation links and the AgentProbe logo.
 * Highlights the active route using pathname matching.
 */
export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex h-screen w-56 flex-col border-r border-border bg-card">
      {/* Logo */}
      <div className="flex items-center gap-1 px-5 py-6">
        <span className="text-lg font-semibold tracking-tight text-foreground">
          Agent
        </span>
        <span className="text-lg font-semibold tracking-tight text-[#4fc3f7]">
          Probe
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex flex-1 flex-col gap-1 px-3">
        {NAV_ITEMS.map((item) => {
          const active = isActive(pathname, item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                active
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-border px-5 py-4">
        <p className="text-xs text-muted-foreground">ReAct Observatory</p>
      </div>
    </aside>
  );
}
