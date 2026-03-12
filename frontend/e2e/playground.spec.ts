import { test, expect } from "@playwright/test";

test.describe("Playground", () => {
  test("should load the playground page", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("text=AgentProbe")).toBeVisible();
  });

  test("should have model and provider selectors", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("text=Provider")).toBeVisible();
  });

  test("should have a query input", async ({ page }) => {
    await page.goto("/");
    const input = page.getByPlaceholder(/query|question|ask/i);
    await expect(input).toBeVisible();
  });

  test("should show tool panel", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("text=calculator")).toBeVisible();
  });
});
