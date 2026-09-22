import { expect, test } from "@playwright/test";
import { RAW_ROW } from "./helpers";

test("portfolio and every page render without borrower-level data", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Credit-risk models" })).toBeVisible();
  await expect(page.getByRole("link", { name: "pd-credit-v1.0.0" })).toBeVisible();
  for (const suffix of ["", "/validation", "/monitoring", "/governance", "/executive"]) {
    await page.goto(`/versions/pd-credit-v1.0.0${suffix}`);
    await expect(page.locator("main h1").first()).toBeVisible();
    const text = await page.locator("main").innerText();
    expect(text).not.toMatch(RAW_ROW);
  }
});

test("monitoring shows three batches, PSI alerts and lets a user resolve one", async ({ page }) => {
  await page.goto("/versions/pd-credit-v1.0.0/monitoring");
  const psi = page.getByTestId("psi-table");
  await expect(psi.locator("thead th")).toHaveCount(4); // feature + 3 batches
  await expect(psi.getByText("alert").first()).toBeVisible();
  const openRow = page.getByTestId("alert-row").filter({ hasText: "open" }).first();
  await openRow.getByRole("textbox").fill("Reviewed during e2e; benign shift.");
  await openRow.getByRole("button", { name: "Resolve" }).click();
  await expect(page.getByText("Resolution: Reviewed during e2e; benign shift.")).toBeVisible();
});
