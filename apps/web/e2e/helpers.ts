import { Page, expect } from "@playwright/test";

export async function actAs(page: Page, role: "data_scientist" | "reviewer" | "risk_leader") {
  await page.getByTestId("role-switcher").selectOption(role);
  await expect(page.getByTestId("role-switcher")).toHaveValue(role);
}

export const RAW_ROW = /\bln_[0-9a-f]{12}\b/;
