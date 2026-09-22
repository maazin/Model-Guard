// Measure API latency and dashboard load time on the local seeded demo; save screenshots.
// Usage: cd apps/web && node e2e/measure_demo.mjs [apiBase] [webBase]
import { chromium } from "@playwright/test";
import { writeFileSync } from "node:fs";

const api = process.argv[2] ?? "http://localhost:8000";
const web = process.argv[3] ?? "http://localhost:5173";
const H = { "X-Demo-User": "reviewer", "Content-Type": "application/json" };
const endpoints = [
  ["GET", "/api/v1/portfolio"],
  ["GET", "/api/v1/model-versions/pd-credit-v1.0.0"],
  ["GET", "/api/v1/model-versions/pd-credit-v1.0.0/monitoring"],
  ["GET", "/api/v1/executive-summary/pd-credit-v1.0.0"],
  ["POST", "/api/v1/model-versions/pd-credit-v1.2.0/copilot/query", { question: "What evidence is missing before approval?" }],
];
const latency = {};
for (const [method, path, body] of endpoints) {
  const times = [];
  for (let i = 0; i < 15; i++) {
    const t = performance.now();
    const r = await fetch(api + path, { method, headers: H, body: body ? JSON.stringify(body) : undefined });
    await r.json();
    times.push(performance.now() - t);
  }
  times.sort((a, b) => a - b);
  latency[`${method} ${path}`] = { p50_ms: +times[7].toFixed(1), p95_ms: +times[14].toFixed(1) };
}
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 800 }, colorScheme: "light" });
const loads = {};
const shots = [["/", "overview"], ["/versions/pd-credit-v1.0.0", "version"], ["/versions/pd-credit-v1.0.0/validation", "validation"], ["/versions/pd-credit-v1.0.0/monitoring", "monitoring"], ["/versions/pd-credit-v1.2.0/governance", "governance"], ["/versions/pd-credit-v1.0.0/executive", "executive"]];
for (const [path, name] of shots) {
  const t = performance.now();
  await page.goto(web + path, { waitUntil: "networkidle" });
  await page.locator("main h1").first().waitFor();
  loads[path] = +(performance.now() - t).toFixed(0);
  await page.screenshot({ path: `../../docs/screenshots/${name}.png`, fullPage: name !== "monitoring" });
}
await browser.close();
const out = { measured_at: new Date().toISOString(), api_latency: latency, dashboard_load_ms: loads };
writeFileSync("../../docs/executive/measured-demo-metrics.json", JSON.stringify(out, null, 2));
console.log(JSON.stringify(out, null, 2));
