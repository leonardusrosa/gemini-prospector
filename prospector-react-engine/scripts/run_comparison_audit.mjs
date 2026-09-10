import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import * as chromeLauncher from "chrome-launcher";
import lighthouse from "lighthouse";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DIR_ENGINE_A = path.resolve(
  __dirname,
  "../../../prospector-sites/clientes/dallas-detailing-and-buffing"
);
const DIR_ENGINE_B = path.resolve(__dirname, "../out");

import zlib from "node:zlib";

function createStaticServer(rootDirectory) {
  return http.createServer((req, res) => {
    let reqUrl = req.url.split("?")[0];
    if (reqUrl === "/") reqUrl = "/index.html";
    const filePath = path.join(rootDirectory, reqUrl);

    if (!fs.existsSync(filePath)) {
      res.writeHead(404, { "Content-Type": "text/plain" });
      res.end("Not Found");
      return;
    }

    const ext = path.extname(filePath).toLowerCase();
    const mimeTypes = {
      ".html": "text/html",
      ".css": "text/css",
      ".js": "application/javascript",
      ".json": "application/json",
      ".png": "image/png",
      ".jpg": "image/jpeg",
      ".jpeg": "image/jpeg",
      ".webp": "image/webp",
      ".mp4": "video/mp4",
      ".webm": "video/webm",
      ".svg": "image/svg+xml",
      ".woff2": "font/woff2",
      ".woff": "font/woff",
    };

    const contentType = mimeTypes[ext] || "application/octet-stream";
    const acceptEncoding = req.headers["accept-encoding"] || "";
    const isCompressible = /^(text\/|application\/javascript|application\/json|image\/svg\+xml)/.test(contentType);

    if (isCompressible && acceptEncoding.includes("gzip")) {
      res.writeHead(200, {
        "Content-Type": contentType,
        "Content-Encoding": "gzip",
      });
      fs.createReadStream(filePath).pipe(zlib.createGzip()).pipe(res);
    } else {
      res.writeHead(200, { "Content-Type": contentType });
      fs.createReadStream(filePath).pipe(res);
    }
  });
}

async function runLighthouseAudit(url, port) {
  const options = {
    logLevel: "error",
    output: "json",
    onlyCategories: ["performance", "accessibility", "best-practices", "seo"],
    port: port,
  };

  const runnerResult = await lighthouse(url, options);
  const lhr = runnerResult.lhr;

  const getMetric = (id) => lhr.audits[id]?.numericValue ?? 0;
  const getDisplay = (id) => lhr.audits[id]?.displayValue ?? "N/A";

  const networkItems = lhr.audits["network-requests"]?.details?.items || [];
  let htmlBytes = 0;
  let cssBytes = 0;
  let jsBytes = 0;
  let mediaBytes = 0;
  let totalBytes = 0;

  for (const item of networkItems) {
    const size = item.transferSize || item.resourceSize || 0;
    totalBytes += size;
    const type = item.resourceType?.toLowerCase() || "";
    if (type === "document") htmlBytes += size;
    else if (type === "stylesheet") cssBytes += size;
    else if (type === "script") jsBytes += size;
    else if (type === "media" || type === "image") mediaBytes += size;
  }

  return {
    categories: {
      performance: Math.round((lhr.categories.performance?.score || 0) * 100),
      accessibility: Math.round((lhr.categories.accessibility?.score || 0) * 100),
      bestPractices: Math.round((lhr.categories["best-practices"]?.score || 0) * 100),
      seo: Math.round((lhr.categories.seo?.score || 0) * 100),
    },
    metrics: {
      fcpMs: Math.round(getMetric("first-contentful-paint")),
      fcpDisplay: getDisplay("first-contentful-paint"),
      lcpMs: Math.round(getMetric("largest-contentful-paint")),
      lcpDisplay: getDisplay("largest-contentful-paint"),
      cls: parseFloat(getMetric("cumulative-layout-shift").toFixed(4)),
      clsDisplay: getDisplay("cumulative-layout-shift"),
      tbtMs: Math.round(getMetric("total-blocking-time")),
      tbtDisplay: getDisplay("total-blocking-time"),
      speedIndexMs: Math.round(getMetric("speed-index")),
      speedIndexDisplay: getDisplay("speed-index"),
    },
    network: {
      requestCount: networkItems.length,
      totalTransferKB: parseFloat((totalBytes / 1024).toFixed(1)),
      htmlTransferKB: parseFloat((htmlBytes / 1024).toFixed(1)),
      cssTransferKB: parseFloat((cssBytes / 1024).toFixed(1)),
      jsTransferKB: parseFloat((jsBytes / 1024).toFixed(1)),
      mediaTransferKB: parseFloat((mediaBytes / 1024).toFixed(1)),
    },
  };
}

async function main() {
  console.log("=== Starting Automated Lighthouse A/B Comparison ===");
  console.log(`Engine A directory: ${DIR_ENGINE_A}`);
  console.log(`Engine B directory: ${DIR_ENGINE_B}`);

  const serverA = createStaticServer(DIR_ENGINE_A);
  const serverB = createStaticServer(DIR_ENGINE_B);

  await new Promise((res) => serverA.listen(4001, "127.0.0.1", res));
  await new Promise((res) => serverB.listen(4002, "127.0.0.1", res));
  console.log("Servers listening on ports 4001 (A) and 4002 (B)...");

  console.log("Launching headless Chrome...");
  const chrome = await chromeLauncher.launch({
    chromeFlags: ["--headless", "--disable-gpu", "--no-sandbox"],
  });
  console.log(`Chrome launched on debug port ${chrome.port}`);

  try {
    console.log("Auditing Engine A (Vanilla production)...");
    const resultA = await runLighthouseAudit("http://127.0.0.1:4001/", chrome.port);
    console.log("Engine A audit complete.");

    console.log("Auditing Engine B2 (Round 2 Distinctive React)...");
    const resultB = await runLighthouseAudit("http://127.0.0.1:4002/", chrome.port);
    console.log("Engine B2 audit complete.");

    const comparison = {
      engineA: resultA,
      engineB: resultB,
      timestamp: new Date().toISOString(),
    };

    const outPath = path.join(__dirname, "lighthouse_comparison.json");
    fs.writeFileSync(outPath, JSON.stringify(comparison, null, 2), "utf-8");
    console.log(`Saved comparison data to ${outPath}`);

    console.log("\n=== LIGHTHOUSE COMPARISON TABLE ===");
    console.log("| Metric | Engine A (Vanilla) | Engine B2 (Round 2) |");
    console.log("|---|---|---|");
    console.log(`| Performance | ${resultA.categories.performance} | ${resultB.categories.performance} |`);
    console.log(`| Accessibility | ${resultA.categories.accessibility} | ${resultB.categories.accessibility} |`);
    console.log(`| Best Practices | ${resultA.categories.bestPractices} | ${resultB.categories.bestPractices} |`);
    console.log(`| SEO | ${resultA.categories.seo} | ${resultB.categories.seo} |`);
    console.log(`| LCP | ${resultA.metrics.lcpDisplay} | ${resultB.metrics.lcpDisplay} |`);
    console.log(`| CLS | ${resultA.metrics.clsDisplay} | ${resultB.metrics.clsDisplay} |`);
    console.log(`| FCP | ${resultA.metrics.fcpDisplay} | ${resultB.metrics.fcpDisplay} |`);
    console.log(`| TBT | ${resultA.metrics.tbtDisplay} | ${resultB.metrics.tbtDisplay} |`);
    console.log(`| Speed Index | ${resultA.metrics.speedIndexDisplay} | ${resultB.metrics.speedIndexDisplay} |`);
    console.log(`| Requests | ${resultA.network.requestCount} | ${resultB.network.requestCount} |`);
    console.log(`| Total Transfer | ${resultA.network.totalTransferKB} KB | ${resultB.network.totalTransferKB} KB |`);
    console.log(`| JS Transfer | ${resultA.network.jsTransferKB} KB | ${resultB.network.jsTransferKB} KB |`);
    console.log(`| CSS Transfer | ${resultA.network.cssTransferKB} KB | ${resultB.network.cssTransferKB} KB |`);
    console.log(`| HTML Transfer | ${resultA.network.htmlTransferKB} KB | ${resultB.network.htmlTransferKB} KB |`);

  } finally {
    console.log("Shutting down Chrome and servers...");
    try {
      await chrome.kill();
    } catch (e) {
      // Chrome temp directory cleanup on Windows
    }
    await new Promise((res) => serverA.close(res));
    await new Promise((res) => serverB.close(res));
    console.log("Cleanup complete.");
  }
}

main().catch((err) => {
  console.error("Error in comparison audit:", err);
  process.exit(1);
});
