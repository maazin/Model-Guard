import { expect, test } from "@playwright/test";
import { RAW_ROW, actAs } from "./helpers";

test("incomplete version is blocked with named missing evidence", async ({ page }) => {
  await page.goto("/versions/pd-credit-v1.2.0/governance");
  await actAs(page, "data_scientist");
  await expect(page.getByTestId("missing-evidence").first()).toBeVisible();
  await page.getByTestId("submit-review").click();
  await expect(page.getByText("readiness gate blocked submission")).toBeVisible();
  await expect(page.getByTestId("readiness-list").getByText("at least 3 required")).toBeVisible();
});

test("reviewer rejects, data scientist corrects, reviewer approves; audit log records it", async ({ page }) => {
  await page.goto("/versions/pd-credit-v1.1.0/governance");
  await actAs(page, "risk_leader");
  await expect(page.getByText("read-only access")).toBeVisible();
  await actAs(page, "reviewer");
  await page.locator("#rationale").fill("Reject: please add the Q3 drift discussion to the change log.");
  await page.getByTestId("reject").click();
  await expect(page.locator("main h1").first().locator("..").getByText("Rejected")).toBeVisible();

  await actAs(page, "data_scientist");
  await page.getByRole("button", { name: "Reopen as draft" }).click();
  await page.getByRole("button", { name: "Run validation", exact: true }).click();
  await expect(page.locator("main h1").first().locator("..").getByText("Validated")).toBeVisible();
  await page.getByTestId("submit-review").click();
  await expect(page.locator("main h1").first().locator("..").getByText("Awaiting review")).toBeVisible();

  await actAs(page, "reviewer");
  await page.locator("#rationale").fill("Approve: change log updated, package complete.");
  await page.getByTestId("approve").click();
  await expect(page.locator("main h1").first().locator("..").getByText("Approved", { exact: true })).toBeVisible();

  await page.goto("/versions/pd-credit-v1.1.0");
  const audit = page.locator("table.data");
  await expect(audit.getByText("Rejected", { exact: true }).first()).toBeVisible();
  await expect(audit.getByText("Approved", { exact: true }).first()).toBeVisible();
});

test("copilot answers with citations and no raw dataset values", async ({ page }) => {
  await page.goto("/versions/pd-credit-v1.2.0/governance");
  await page.getByTestId("copilot-question").fill("What evidence is missing before this version can be approved? monitoring limitations");
  await page.getByTestId("copilot-ask").click();
  const answer = page.getByTestId("copilot-answer");
  await expect(answer).toBeVisible();
  await expect(answer.getByText("Citations:")).toBeVisible();
  await expect(answer.getByText("›").first()).toBeVisible();
  const text = await answer.innerText();
  expect(text).not.toMatch(RAW_ROW);
  expect(text).toContain("Not an approval authority");
});
