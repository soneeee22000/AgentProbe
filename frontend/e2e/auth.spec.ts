import { test, expect } from "@playwright/test";

test.describe("Navigation", () => {
  test("should navigate to all main pages", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("text=AgentProbe")).toBeVisible();

    // Navigate to Runs
    await page.click("text=Runs");
    await expect(page).toHaveURL(/\/runs/);

    // Navigate to Benchmarks
    await page.click("text=Benchmarks");
    await expect(page).toHaveURL(/\/benchmarks/);

    // Navigate to Analytics
    await page.click("text=Analytics");
    await expect(page).toHaveURL(/\/analytics/);

    // Navigate to Compare
    await page.click("text=Compare");
    await expect(page).toHaveURL(/\/compare/);

    // Navigate to Prompts
    await page.click("text=Prompts");
    await expect(page).toHaveURL(/\/prompts/);
  });

  test("prompts page should load", async ({ page }) => {
    await page.goto("/prompts");
    await expect(page.locator("h1")).toContainText(/prompt/i);
  });
});
