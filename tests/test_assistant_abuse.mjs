import assert from "node:assert";
import { MemorySharedStore, AssistantAbuseGuard } from "./abuse-guard.mjs";

async function runTests() {
  console.log("=== EXECUTING ASSISTANT ABUSE LAYER TEST SUITE ===");

  // Shared store representing distributed infrastructure (e.g. Redis / Upstash)
  const sharedStore = new MemorySharedStore();

  // Test 1: Burst Limit (10 requests / 60s / IP)
  {
    const guard = new AssistantAbuseGuard({
      store: sharedStore,
      burstLimit: 10,
      burstWindowSec: 60,
    });
    const ip = "192.168.1.10";
    const tenant = "test-tenant";

    for (let i = 1; i <= 10; i++) {
      const res = await guard.checkRateLimits(ip, tenant);
      assert.strictEqual(res.allowed, true, `Request ${i} should be allowed`);
    }

    // 11th request must fail with 429
    const res11 = await guard.checkRateLimits(ip, tenant);
    assert.strictEqual(res11.allowed, false, "11th request must be throttled");
    assert.strictEqual(res11.status, 429, "Status must be 429");
    assert.strictEqual(res11.error, "RATE_LIMIT_BURST_EXCEEDED");
    assert.ok(res11.retryAfter > 0, "Retry-After header value must be > 0");
    console.log("✓ TEST 1: Burst Limit Passed (10 allowed, 11th rejected with 429)");
  }

  // Test 2: Different IP Isolation
  {
    const guard = new AssistantAbuseGuard({
      store: sharedStore,
      burstLimit: 10,
      burstWindowSec: 60,
    });
    // IP 192.168.1.10 is currently throttled, but IP 192.168.1.20 must NOT be throttled
    const resDifferentIp = await guard.checkRateLimits("192.168.1.20", "test-tenant");
    assert.strictEqual(resDifferentIp.allowed, true, "Different IP must be isolated and allowed");
    console.log("✓ TEST 2: IP Isolation Passed (Throttling on IP A does not affect IP B)");
  }

  // Test 3: Hourly Limit (60 req / hr / IP)
  {
    await sharedStore.reset();
    const guard = new AssistantAbuseGuard({
      store: sharedStore,
      burstLimit: 100, // relax burst to test hourly
      hourlyLimit: 60,
      hourlyWindowSec: 3600,
    });
    const ip = "10.0.0.5";
    const tenant = "test-tenant";

    for (let i = 1; i <= 60; i++) {
      const res = await guard.checkRateLimits(ip, tenant);
      assert.strictEqual(res.allowed, true, `Hourly request ${i} should be allowed`);
    }

    const res61 = await guard.checkRateLimits(ip, tenant);
    assert.strictEqual(res61.allowed, false, "61st request must be throttled by hourly limit");
    assert.strictEqual(res61.status, 429);
    assert.strictEqual(res61.error, "RATE_LIMIT_HOURLY_EXCEEDED");
    assert.ok(res61.retryAfter > 0, "Retry-After must be positive");
    console.log("✓ TEST 3: Hourly Limit Passed (60 allowed, 61st rejected with 429)");
  }

  // Test 4: Tenant Limit & Tenant Isolation
  {
    await sharedStore.reset();
    const guard = new AssistantAbuseGuard({
      store: sharedStore,
      burstLimit: 100,
      hourlyLimit: 100,
      tenantHourlyLimit: 5,
    });

    // Send 5 requests from different IPs targeting tenant-alpha
    for (let i = 1; i <= 5; i++) {
      const res = await guard.checkRateLimits(`172.16.0.${i}`, "tenant-alpha");
      assert.strictEqual(res.allowed, true);
    }

    // 6th request to tenant-alpha fails
    const res6Alpha = await guard.checkRateLimits("172.16.0.6", "tenant-alpha");
    assert.strictEqual(res6Alpha.allowed, false);
    assert.strictEqual(res6Alpha.status, 429);
    assert.strictEqual(res6Alpha.error, "TENANT_QUOTA_EXCEEDED");

    // Request to tenant-beta must succeed (tenant isolation)
    const resBeta = await guard.checkRateLimits("172.16.0.6", "tenant-beta");
    assert.strictEqual(resBeta.allowed, true, "Tenant Beta must remain isolated and allowed");
    console.log("✓ TEST 4: Tenant Limit & Tenant Isolation Passed");
  }

  // Test 5: TTL Reset
  {
    await sharedStore.reset();
    const guard = new AssistantAbuseGuard({
      store: sharedStore,
      burstLimit: 2,
      burstWindowSec: 1, // 1 second window
    });
    const ip = "192.168.2.1";
    await guard.checkRateLimits(ip, "t");
    await guard.checkRateLimits(ip, "t");
    const blocked = await guard.checkRateLimits(ip, "t");
    assert.strictEqual(blocked.allowed, false);

    // Wait 1.1s for TTL expiration
    await new Promise((resolve) => setTimeout(resolve, 1100));

    const afterTtl = await guard.checkRateLimits(ip, "t");
    assert.strictEqual(afterTtl.allowed, true, "Counter must reset after TTL expires");
    console.log("✓ TEST 5: TTL Reset Passed");
  }

  // Test 6: Oversized Body Protection
  {
    const guard = new AssistantAbuseGuard({
      store: sharedStore,
      maxBodyBytes: 1000,
    });
    const validBody = JSON.stringify({ message: "Hello", tenant: "alpha" });
    assert.strictEqual(guard.validateRawBodySize(validBody).allowed, true);

    const oversizedBody = "x".repeat(1001);
    const check = guard.validateRawBodySize(oversizedBody);
    assert.strictEqual(check.allowed, false);
    assert.strictEqual(check.status, 413);
    assert.strictEqual(check.error, "PAYLOAD_TOO_LARGE");
    console.log("✓ TEST 6: Oversized Body Protection Passed (HTTP 413)");
  }

  // Test 7: Oversized History & Input Flooding
  {
    const guard = new AssistantAbuseGuard({
      store: sharedStore,
      maxUserChars: 200,
      maxHistoryMessages: 3,
      maxHistoryTotalChars: 500,
    });

    // Too many history messages
    const historyTooMany = [
      { role: "user", content: "1" },
      { role: "assistant", content: "2" },
      { role: "user", content: "3" },
      { role: "assistant", content: "4" },
    ];
    const checkHistCount = guard.validateInputIntegrity("test", historyTooMany);
    assert.strictEqual(checkHistCount.allowed, false);
    assert.strictEqual(checkHistCount.error, "HISTORY_TOO_LONG");

    // History too many characters
    const historyTooChars = [
      { role: "user", content: "a".repeat(300) },
      { role: "assistant", content: "b".repeat(300) },
    ];
    const checkHistChars = guard.validateInputIntegrity("test", historyTooChars);
    assert.strictEqual(checkHistChars.allowed, false);
    assert.strictEqual(checkHistChars.error, "HISTORY_OVERSIZED");

    // Repetitive character flooding
    const floodingMessage = "help " + "a".repeat(50);
    const checkFlooding = guard.validateInputIntegrity(floodingMessage, []);
    assert.strictEqual(checkFlooding.allowed, false);
    assert.strictEqual(checkFlooding.error, "INPUT_FLOODING");
    console.log("✓ TEST 7: Oversized History & Character Flooding Passed");
  }

  // Test 8: Provider Not Called on Rejected Request
  {
    await sharedStore.reset();
    const guard = new AssistantAbuseGuard({
      store: sharedStore,
      burstLimit: 1,
    });

    let providerCallCount = 0;
    const mockProvider = async () => {
      providerCallCount++;
      return "mock response";
    };

    const handleRequest = async (ip, tenant, msg) => {
      const bodyCheck = guard.validateRawBodySize(msg);
      if (!bodyCheck.allowed) return bodyCheck;
      const inputCheck = guard.validateInputIntegrity(msg, []);
      if (!inputCheck.allowed) return inputCheck;
      const rateCheck = await guard.checkRateLimits(ip, tenant);
      if (!rateCheck.allowed) return rateCheck;
      return { allowed: true, text: await mockProvider() };
    };

    // Request 1: succeeds
    await handleRequest("1.2.3.4", "t1", "Valid question");
    assert.strictEqual(providerCallCount, 1);

    // Request 2: blocked by rate limit
    const blockedRes = await handleRequest("1.2.3.4", "t1", "Valid question 2");
    assert.strictEqual(blockedRes.allowed, false);
    assert.strictEqual(providerCallCount, 1, "Provider MUST NOT be called when request is rejected");

    // Request 3: blocked by empty input
    const emptyRes = await handleRequest("1.2.3.5", "t1", "   ");
    assert.strictEqual(emptyRes.allowed, false);
    assert.strictEqual(providerCallCount, 1, "Provider MUST NOT be called on invalid input");
    console.log("✓ TEST 8: Provider Protection Passed (0 downstream calls on rejection)");
  }

  // Test 9 & 10: 429 Status and Retry-After Header
  {
    await sharedStore.reset();
    const guard = new AssistantAbuseGuard({
      store: sharedStore,
      burstLimit: 1,
      burstWindowSec: 45,
    });
    await guard.checkRateLimits("8.8.8.8", "t");
    const blocked = await guard.checkRateLimits("8.8.8.8", "t");
    assert.strictEqual(blocked.status, 429);
    assert.ok(blocked.retryAfter <= 45 && blocked.retryAfter > 0);
    console.log("✓ TEST 9 & 10: 429 Response & Accurate Retry-After Passed");
  }

  // Test 11 & 12: Serverless Multi-Instance Simulation (Two separate instances share state)
  {
    await sharedStore.reset();
    // Instance A and Instance B represent two separate ephemeral serverless function containers
    // connecting to the same distributed KV/store.
    const instanceA = new AssistantAbuseGuard({
      store: sharedStore,
      burstLimit: 3,
      burstWindowSec: 60,
    });
    const instanceB = new AssistantAbuseGuard({
      store: sharedStore,
      burstLimit: 3,
      burstWindowSec: 60,
    });

    const ip = "198.51.100.1";
    const tenant = "shared-tenant";

    // Hit 1 on Instance A
    const r1 = await instanceA.checkRateLimits(ip, tenant);
    assert.strictEqual(r1.allowed, true);

    // Hit 2 on Instance B
    const r2 = await instanceB.checkRateLimits(ip, tenant);
    assert.strictEqual(r2.allowed, true);

    // Hit 3 on Instance A
    const r3 = await instanceA.checkRateLimits(ip, tenant);
    assert.strictEqual(r3.allowed, true);

    // Hit 4 on Instance B: Must be throttled across instances!
    const r4 = await instanceB.checkRateLimits(ip, tenant);
    assert.strictEqual(r4.allowed, false, "Instance B must see hits recorded by Instance A");
    assert.strictEqual(r4.status, 429);
    assert.strictEqual(r4.error, "RATE_LIMIT_BURST_EXCEEDED");
    console.log("✓ TEST 11 & 12: Serverless Multi-Instance State Sharing Passed (Cold/Separate Instances Share State)");
  }

  console.log("=== ALL 12 ASSISTANT ABUSE LAYER TESTS PASSED ===");
}

runTests().catch((err) => {
  console.error("Test failure:", err);
  process.exit(1);
});
