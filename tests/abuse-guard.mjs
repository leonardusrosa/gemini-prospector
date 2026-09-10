/**
 * abuse-guard.mjs
 * Production-grade serverless abuse defense layer specification and adapter.
 * Supports distributed atomic stores (Upstash / Redis / Cloudflare KV / Shared KV).
 */

export class MemorySharedStore {
  // In-memory implementation of a shared distributed key-value store (e.g. simulating Redis/Upstash)
  constructor() {
    this.storage = new Map();
  }

  async incrWithTtl(key, ttlSeconds) {
    const now = Date.now();
    let record = this.storage.get(key);
    if (!record || now >= record.expiresAt) {
      record = { count: 1, expiresAt: now + ttlSeconds * 1000, ttlSeconds };
      this.storage.set(key, record);
      return { count: 1, ttlRemaining: ttlSeconds };
    }
    record.count += 1;
    const ttlRemaining = Math.max(1, Math.ceil((record.expiresAt - now) / 1000));
    return { count: record.count, ttlRemaining };
  }

  async get(key) {
    const now = Date.now();
    const record = this.storage.get(key);
    if (!record || now >= record.expiresAt) return null;
    return record;
  }

  async reset() {
    this.storage.clear();
  }
}

export class AssistantAbuseGuard {
  constructor(options = {}) {
    this.store = options.store;
    if (!this.store) {
      throw new Error("Durable store is required. In-memory unshared state is prohibited.");
    }
    this.burstWindowSec = options.burstWindowSec || 60;
    this.burstLimit = options.burstLimit || 10;
    this.hourlyWindowSec = options.hourlyWindowSec || 3600;
    this.hourlyLimit = options.hourlyLimit || 60;
    this.tenantHourlyLimit = options.tenantHourlyLimit || 200;
    this.maxBodyBytes = options.maxBodyBytes || 16384; // 16 KB
    this.maxUserChars = options.maxUserChars || 1200;
    this.maxHistoryMessages = options.maxHistoryMessages || 6;
    this.maxHistoryTotalChars = options.maxHistoryTotalChars || 4000;
  }

  validateRawBodySize(rawBody) {
    const bytes = typeof rawBody === "string" ? Buffer.byteLength(rawBody, "utf8") : 0;
    if (bytes > this.maxBodyBytes) {
      return { allowed: false, status: 413, error: "PAYLOAD_TOO_LARGE" };
    }
    return { allowed: true };
  }

  validateInputIntegrity(message, history) {
    if (!message || typeof message !== "string" || !message.trim()) {
      return { allowed: false, status: 400, error: "EMPTY_MESSAGE" };
    }
    if (message.length > this.maxUserChars) {
      return { allowed: false, status: 400, error: "MESSAGE_TOO_LONG" };
    }
    // Check for excessive repetitive character flooding (e.g. 40 identical characters)
    if (/(.)\1{40,}/.test(message)) {
      return { allowed: false, status: 400, error: "INPUT_FLOODING" };
    }

    // Check history constraints
    if (Array.isArray(history)) {
      if (history.length > this.maxHistoryMessages) {
        return { allowed: false, status: 400, error: "HISTORY_TOO_LONG" };
      }
      let totalChars = 0;
      for (const msg of history) {
        if (typeof msg?.content === "string") {
          totalChars += msg.content.length;
        }
      }
      if (totalChars > this.maxHistoryTotalChars) {
        return { allowed: false, status: 400, error: "HISTORY_OVERSIZED" };
      }
    }

    return { allowed: true };
  }

  async checkRateLimits(ip, tenant) {
    const cleanIp = (ip || "unknown").trim();
    const cleanTenant = (tenant || "unknown").trim();

    // 1. IP Burst Limit (e.g. 10 req / 60s)
    const burstKey = `rl:burst:${cleanIp}`;
    const burst = await this.store.incrWithTtl(burstKey, this.burstWindowSec);
    if (burst.count > this.burstLimit) {
      return {
        allowed: false,
        status: 429,
        error: "RATE_LIMIT_BURST_EXCEEDED",
        retryAfter: burst.ttlRemaining,
      };
    }

    // 2. IP Hourly Limit (e.g. 60 req / hour)
    const hourlyKey = `rl:hour:${cleanIp}`;
    const hourly = await this.store.incrWithTtl(hourlyKey, this.hourlyWindowSec);
    if (hourly.count > this.hourlyLimit) {
      return {
        allowed: false,
        status: 429,
        error: "RATE_LIMIT_HOURLY_EXCEEDED",
        retryAfter: hourly.ttlRemaining,
      };
    }

    // 3. Tenant Ceiling (e.g. 200 req / hour)
    const tenantKey = `rl:tenant:${cleanTenant}`;
    const tenantUsage = await this.store.incrWithTtl(tenantKey, this.hourlyWindowSec);
    if (tenantUsage.count > this.tenantHourlyLimit) {
      return {
        allowed: false,
        status: 429,
        error: "TENANT_QUOTA_EXCEEDED",
        retryAfter: tenantUsage.ttlRemaining,
      };
    }

    return { allowed: true };
  }
}
