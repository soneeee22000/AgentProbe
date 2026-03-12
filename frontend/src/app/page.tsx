import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { PlaygroundView } from "@/components/playground/playground-view";

/**
 * Playground page — the main entry point for AgentProbe.
 * Renders the sidebar, header, and playground view in a grid layout.
 */
export default function PlaygroundPage() {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-auto">
          <PlaygroundView />
        </main>
      </div>
    </div>
  );
}
