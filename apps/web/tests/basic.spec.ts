import { test, expect } from "@playwright/test";

test("load dataset and send a message", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("button", { name: "Iris" }).click();
  await expect(page.getByText("sepal_length")).toBeVisible();

  await page.getByPlaceholder("Ask for a visualization...").fill("Show a scatter plot of sepal length vs sepal width.");
  await page.getByRole("button", { name: "Send" }).click();

  await expect(page.getByText("Plot Output")).toBeVisible();
});
