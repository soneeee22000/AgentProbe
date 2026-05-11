/**
 * One-shot Playwright capture script for the README portfolio assets.
 *
 * Captures 5 PNGs from the live Vercel/Railway deploy:
 *   1. decision-graph.png            — initial graph view of demo-fail-001
 *   2. side-panel-hallucinated-tool.png  — WEATHER_FORECAST node clicked
 *   3. side-panel-goal-drift.png     — DECISION node clicked
 *   4. list-view.png                 — flat chronological list view
 *   5. analytics.png                 — analytics dashboard with live data
 *
 * Run from repo root:
 *   npx playwright@latest install chromium  # first time only
 *   node scripts/capture-screenshots.mjs
 *
 * The script is idempotent — deletes prior PNGs at the target paths
 * before re-capturing so re-runs always produce a clean set.
 */
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, join, resolve } from "node:path";
import { rmSync, mkdirSync } from "node:fs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dirname, "..");
const OUT_DIR = join(REPO_ROOT, "docs", "screenshots");
const BASE_URL = "https://agent-probe-one.vercel.app";

const targets = [
  "decision-graph.png",
  "side-panel-hallucinated-tool.png",
  "side-panel-goal-drift.png",
  "list-view.png",
  "analytics.png",
];

async function main() {
  mkdirSync(OUT_DIR, { recursive: true });
  for (const f of targets) {
    try {
      rmSync(join(OUT_DIR, f));
    } catch {}
  }

  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1600, height: 900 },
    deviceScaleFactor: 2,
  });
  const page = await context.newPage();
  page.on("console", (m) => console.log(`  [browser:${m.type()}] ${m.text()}`));

  // 1. Decision Graph (initial view)
  await page.goto(`${BASE_URL}/runs/demo-fail-001`, { waitUntil: "networkidle" });
  await page.waitForSelector("text=demo-fail-001", { timeout: 15000 });
  await page.waitForTimeout(800); // allow graph svg paint
  await page.screenshot({
    path: join(OUT_DIR, "decision-graph.png"),
    type: "png",
  });
  console.log("captured decision-graph.png");

  // 2. WEATHER_FORECAST node clicked (hallucinated_tool side panel)
  // Click the graph node by its label text — stable across viewport sizes.
  await page.getByText("WEATHER_FORECAST").first().click();
  await page.waitForSelector("text=Tool: weather_forecast", { timeout: 10000 });
  await page.waitForTimeout(400);
  await page.screenshot({
    path: join(OUT_DIR, "side-panel-hallucinated-tool.png"),
    type: "png",
  });
  console.log("captured side-panel-hallucinated-tool.png");

  // 3. DECISION node clicked (goal_drift side panel)
  // The graph node text is the literal string "Decision" (mixed case)
  // declared in decision-graph.tsx:51 NODE_LABELS.final. CSS
  // `text-transform: uppercase` makes it *render* as "DECISION", but the
  // DOM text is still "Decision" — so case-insensitive matching is needed.
  // The SVG <text> element bbox is small; we filter for the smallest
  // matching element to skip parent <g>/<svg> wrappers.
  const decisionTarget = await page.evaluate(() => {
    const all = Array.from(document.querySelectorAll("*, svg *"));
    const candidates = all
      .filter((el) => /\bDecision\b/i.test(el.textContent ?? ""))
      .map((el) => {
        const r = el.getBoundingClientRect();
        return {
          tag: el.tagName,
          x: Math.round(r.x + r.width / 2),
          y: Math.round(r.y + r.height / 2),
          area: Math.round(r.width * r.height),
        };
      })
      .filter((c) => c.area > 0)
      .sort((a, b) => a.area - b.area);
    return candidates[0] ?? null;
  });
  if (!decisionTarget) throw new Error("could not find a Decision node on the page");
  console.log(`  Decision node found: ${JSON.stringify(decisionTarget)}`);
  await page.mouse.click(decisionTarget.x, decisionTarget.y);
  // Wait for the panel to swap to the DECISION/goal_drift state. The
  // body text is unique to step #6 so use it as the readiness signal.
  await page.waitForSelector("text=Lyon currently has mild weather", {
    timeout: 10000,
  });
  await page.waitForTimeout(400);
  await page.screenshot({
    path: join(OUT_DIR, "side-panel-goal-drift.png"),
    type: "png",
  });
  console.log("captured side-panel-goal-drift.png");

  // 4. List view toggle
  await page.getByRole("button", { name: "List" }).click();
  await page.waitForSelector("text=weather_forecast", { timeout: 10000 });
  await page.waitForTimeout(400);
  await page.screenshot({
    path: join(OUT_DIR, "list-view.png"),
    type: "png",
  });
  console.log("captured list-view.png");

  // 5. Analytics dashboard
  await page.goto(`${BASE_URL}/analytics`, { waitUntil: "networkidle" });
  await page.waitForSelector("text=TOTAL RUNS", { timeout: 15000 });
  await page.waitForTimeout(1500); // allow Recharts to render bars
  await page.screenshot({
    path: join(OUT_DIR, "analytics.png"),
    type: "png",
  });
  console.log("captured analytics.png");

  await browser.close();
  console.log(`\nAll 5 screenshots saved to: ${OUT_DIR}`);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
