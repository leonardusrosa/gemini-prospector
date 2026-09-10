import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const projectRoot = path.resolve(__dirname, "..");
const outDir = path.join(projectRoot, "out");
const indexPath = path.join(outDir, "index.html");

console.log("=== Validating Engine B Static Export ===");

// 1. out/ exists
if (!fs.existsSync(outDir) || !fs.statSync(outDir).isDirectory()) {
  console.error("[FAIL] out/ directory does not exist.");
  process.exit(1);
}
console.log("[PASS] out/ directory exists");

// 2. index.html exists
if (!fs.existsSync(indexPath) || !fs.statSync(indexPath).isFile()) {
  console.error("[FAIL] out/index.html does not exist.");
  process.exit(1);
}
console.log("[PASS] out/index.html exists");

const htmlContent = fs.readFileSync(indexPath, "utf-8");
const lowerHtml = htmlContent.toLowerCase();

// 3. No external fonts loaded at runtime
if (lowerHtml.includes("fonts.googleapis.com") || lowerHtml.includes("fonts.gstatic.com")) {
  console.error("[FAIL] External fonts detected at runtime.");
  process.exit(1);
}
console.log("[PASS] No external runtime fonts detected");

// 4. No missing local assets referenced in HTML
const assetRegex = /assets\/[a-zA-Z0-9_.-]+/g;
const matchedAssets = new Set(htmlContent.match(assetRegex) || []);

for (const assetRef of matchedAssets) {
  const assetPath = path.join(outDir, assetRef);
  if (!fs.existsSync(assetPath)) {
    console.error(`[FAIL] Referenced asset missing: ${assetRef}`);
    process.exit(1);
  }
}
console.log(`[PASS] All ${matchedAssets.size} referenced local assets verified on disk`);

// 5. Forbidden public prospecting labels
const FORBIDDEN_PROSPECTING_LABELS = [
  "private website concept",
  "website concept",
  "private preview",
  "demo site",
  "mockup",
  "prototype",
  "prepared for",
  "ai-generated concept",
];

for (const label of FORBIDDEN_PROSPECTING_LABELS) {
  if (lowerHtml.includes(label)) {
    console.error(`[FAIL] Forbidden prospecting label found in static export: "${label}"`);
    process.exit(1);
  }
}
console.log("[PASS] No forbidden prospecting labels found");

// 6. Source-neutral reviews
const FORBIDDEN_REVIEW_BRANDING = [
  "google rating",
  "google reviews",
  "google maps reviews",
  "facebook reviews",
  "yelp reviews",
];

for (const brand of FORBIDDEN_REVIEW_BRANDING) {
  if (lowerHtml.includes(brand)) {
    console.error(`[FAIL] Forbidden review branding found in static export: "${brand}"`);
    process.exit(1);
  }
}
console.log("[PASS] Review section is strictly source-neutral");

// 7. Claim granularity preserved (V3.2.2)
const FORBIDDEN_EXPANDED_CLAIMS = [
  "professional tools",
  "vehicle-safe formulas",
  "carpet extraction",
  "leather conditioning",
  "surface decontamination",
  "eliminate deep swirl marks",
  "eliminates deep swirl marks",
  "swirl elimination",
  "deep scratch removal",
  "show-car clear coats",
  "nighttime projection",
  "road visibility",
  "iron particle decontamination",
  "serviced on-site at our addison facility",
];

for (const claim of FORBIDDEN_EXPANDED_CLAIMS) {
  if (lowerHtml.includes(claim)) {
    console.error(`[FAIL] Unsupported claim expansion found: "${claim}"`);
    process.exit(1);
  }
}
console.log("[PASS] Claim granularity and conservative copy preserved");

// 8. Expected services present
const EXPECTED_SERVICES = [
  "Interior and exterior auto detailing.",
  "Paint correction and buffing services.",
  "Color sanding services for automotive paint surfaces.",
  "Headlight restoration services.",
  "Engine bay detailing.",
  "Wheel and brake caliper cleaning and detailing.",
];

for (const service of EXPECTED_SERVICES) {
  if (!htmlContent.includes(service)) {
    console.error(`[FAIL] Expected service description missing: "${service}"`);
    process.exit(1);
  }
}
console.log("[PASS] All 6 conservative service descriptions verified in static HTML");

console.log("\nALL STATIC EXPORT VALIDATION CHECKS PASSED (8/8)");
