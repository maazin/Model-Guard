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

test("the purpose page explains the project in plain language", async ({ page }) => {
  await page.goto("/about");
  await expect(page.getByRole("heading", { name: "Why this exists" })).toBeVisible();
  await expect(page.getByText("The problem")).toBeVisible();
  await expect(page.getByText("What it is not")).toBeVisible();
  await page.getByRole("link", { name: "all models", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Credit-risk models" })).toBeVisible();
});

test("the cut-off simulator recomputes when the slider moves", async ({ page }) => {
  await page.goto("/versions/pd-credit-v2.0.0/simulator");
  await expect(page.getByTestId("simulator")).toBeVisible();
  const before = await page.getByTestId("pnl").innerText();
  await page.getByTestId("cutoff").fill("0.9");
  await expect(page.getByTestId("pnl")).not.toHaveText(before);
  await expect(page.getByText("Approve everyone (no model)")).toBeVisible();
  expect(await page.locator("main").innerText()).not.toMatch(/\bln_[0-9a-f]{12}\b/);
});
