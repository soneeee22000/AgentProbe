import { test, expect } from "@playwright/test";

test.describe("Compare", () => {
  test("should load compare page", async ({ page }) => {
    await page.goto("/compare");
    await expect(page.locator("text=Run Both")).toBeVisible();
  });

  test("should have left and right selectors", async ({ page }) => {
    await page.goto("/compare");
    await expect(page.locator("text=Left")).toBeVisible();
    await expect(page.locator("text=Right")).toBeVisible();
  });

  test("should have query input", async ({ page }) => {
    await page.goto("/compare");
    const input = page.getByPlaceholder(/compare/i);
    await expect(input).toBeVisible();
  });
});
