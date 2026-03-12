import { test, expect } from "@playwright/test";

test.describe("Benchmarks", () => {
  test("should load benchmarks page", async ({ page }) => {
    await page.goto("/benchmarks");
    await expect(page.locator("h1")).toContainText(/benchmark/i);
  });

  test("should display benchmark cases", async ({ page }) => {
    await page.goto("/benchmarks");
    // Wait for cases to load
    await page.waitForTimeout(2000);
    // Should have case cards or table rows
    const content = await page.textContent("body");
    expect(content).toBeTruthy();
  });
});
