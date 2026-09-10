import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const DIR_OUT = path.resolve(__dirname, "../out");

function createStaticGzipServer(rootDirectory) {
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

async function main() {
  const server = createStaticGzipServer(DIR_OUT);
  await new Promise((res) => server.listen(4005, "127.0.0.1", res));
  console.log("Static server running on http://127.0.0.1:4005");

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  const networkRequests = [];
  page.on("response", async (response) => {
    try {
      const url = response.url();
      const status = response.status();
      const headers = response.headers();
      const buffer = await response.body();
      networkRequests.push({
        url,
        status,
        contentEncoding: headers["content-encoding"],
        contentType: headers["content-type"],
        transferredBytes: buffer.length,
      });
    } catch (e) {
      // ignore closed
    }
  });

  await page.goto("http://127.0.0.1:4005/", { waitUntil: "networkidle" });

  let appJsGzip = 0;
  let polyfillJsGzip = 0;
  let totalJsGzip = 0;

  console.log("\n=== REAL BROWSER JS NETWORK REQUESTS ===");
  for (const item of networkRequests) {
    if (item.url.endsWith(".js") || (item.contentType && item.contentType.includes("javascript"))) {
      const filename = item.url.split("/").pop();
      const isPolyfill = filename.includes("polyfill");
      const kb = (item.transferredBytes / 1024).toFixed(1);
      console.log(`- ${filename}: ${kb} KB (encoding: ${item.contentEncoding || 'none'}, polyfill: ${isPolyfill})`);
      if (isPolyfill) {
        polyfillJsGzip += item.transferredBytes;
      } else {
        appJsGzip += item.transferredBytes;
      }
      totalJsGzip += item.transferredBytes;
    }
  }

  const appKb = (appJsGzip / 1024).toFixed(1);
  const polyKb = (polyfillJsGzip / 1024).toFixed(1);
  const totalKb = (totalJsGzip / 1024).toFixed(1);

  console.log("\n=== SUMMARY OF ACTUAL JS TRANSFERRED TO BROWSER ===");
  console.log(`APP_JS_GZIP: ${appKb} KB`);
  console.log(`POLYFILL_JS_GZIP: ${polyKb} KB`);
  console.log(`TOTAL_JS_GZIP_ACTUALLY_TRANSFERRED: ${totalKb} KB`);

  await browser.close();
  await new Promise((res) => server.close(res));
}

main().catch(console.error);
