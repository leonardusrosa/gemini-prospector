# Engine C — Google Flow full-screen hero motion (v1)

Product decisions locked November 21, 2026. Applies to all niches and all generated websites. The hero is a video that fills the viewport on desktop and mobile, with title/subtitle/CTA as accessible live HTML, not text baked into generated pixels.

## Mandatory v3 review sequence

1. FACTS_AND_IDENTITIES
2. MEDIA_RIGHTS_AND_RELEVANCE
3. ENGINE_C_CANDIDATES
4. INDEPENDENT_DESIGN_DIRECTION
5. HERO_MOTION_MANUAL_APPROVAL
6. IMPLEMENTATION_AND_RESPONSIVE
7. CLIENT_CMS_COMPATIBILITY
8. BROWSER_VISUAL_AND_INTERACTIONS
9. FACTUAL_AND_CONVERSION_RECHECK

Step 5 contains four frame generations, two Flow clip generations, independent visual/motion/browser QA, and an authenticated HUMAN approval. Old incomplete v1/v2 runs must be restarted as new v3 runs. A video cannot be accepted as a fake image, a still poster, or a cropped desktop clip.

## Core visual contract

Desktop: bespoke 16:9 full-screen clip lasting 5–10 seconds.
Mobile: separately composed 9:16 full-screen clip lasting 5–10 seconds.
Every variant must have a first frame, last frame, detailed generation prompts and reasoned spatial boxes for the headline, subtitle, CTA and focal object. Text-safe regions must be respected throughout motion, not just the first/last frames. The mobile video must be created separately, not just cropped from desktop.

Creative subject: best tasteful option wins. Real first-party lead image is optional if verified and relevant; otherwise generate source-grounded brand imagery or abstract kinetic composition. Distinguish generic illustrative people/products from actual owner/staff/patient/menu items; never imply they are true business evidence. Niche defaults are energetic for pizza/restaurants, warm tactile for cafes, calm for clinics/dental offices. Strong reveals, flour/ingredient bursts and explosions are allowed where they look premium, with NO effect whitelist. Reject strobing, object warping, distracting text/CTA obstruction and inaccurate branding.

Ending policy: engine chooses a verified seamless loop or a beautiful freeze-on-end independently per variant. Never claim a visible hard seam is seamless. Final video should be legible at all points. Accessibility and data saver/reduced motion must show a true poster and functional CTA.

## Google Flow usage

Official Flow docs (checked November 21, 2026):
- https://support.google.com/flow/answer/16352836
- https://support.google.com/flow/answer/16353334
- https://support.google.com/flow/answer/16526234

Flow supports first/last Frames to Video, portrait/landscape, and compatible 5–10-second durations through Omni Flash 1.2 and Veo 3.1 Lite. Different models/plans can change availability and cost. Default desired length: 8 seconds, adjustable between 5 and 10.

Standard budget: 4 first/last frames + 2 clips + max 2 targeted retries per lead (eight generations total), not two retries per variant. Check exact credit cost, active model and balance in the live Flow UI before each request; no unexpected spending, top-ups or silent retries. As of check, Omni Flash 1.2 720p costs 3 credits per second and Veo 3.1 Lite costs 10 credits per clip for non-Ultra plans (5 for Ultra). Two 8-second Omni videos are about 48 credits before stills and retries; pricing is dynamic and cannot be fixed in code. Credits from two Google accounts are independent; do not assume both have 1,000 left. Account routing uses aliases flow-a and flow-b for normal owner-authorized scheduling only, not for bypassing restrictions. Never store Google logins, passwords or cookies in project files. No automatic purchase.

The browser executor will use authenticated user-owned Flow profiles through Remote Desktop Commander and carry out only permitted UI workflows. It must record account alias, model, credited cost, first/end frame hashes, actual video hashes and download metadata. Any UI/API capability mismatch stops the job.

## Human approval

The new stage requires a hero motion plan, the four frames, desktop/mobile video files, independent browser QA with actual screenshots and timing evidence, and a separate human approval receipt. The receipt must bind to exact plan and delivery SHA-256 and be signed with a human-only verification key. The engine cannot forge approval or mark its own generated outputs approved. The authenticated admin UI for the approval key is not yet wired, so final hero approval is intentionally blocked until that owner-facing action exists. Future scoring-based automatic selection is a separate product-policy rollout and is currently disabled.

## Website implementation

Both variants use muted autoplay, playsinline, appropriate responsive source switching, full-viewport cover and independently composed portrait/landscape posters. Use semantic HTML overlays, safe contrast gradients and CSS safe areas. Reduced motion, mobile power/data saving, network failure and autoplay-block must retain static artwork and usable CTAs. Verify playback, seam/freeze stability, text readability, accessibility, no horizontal overflow, and compressed asset size in Chromium. Avoid raw giant unoptimized exports.

## Restaurant on-page menu rule

For every restaurant/pizzeria/cafe with a verified official menu, generate a genuine ON-PAGE Menu section: all supported source-reviewed items, categories, descriptions and prices as available. The full menu must be mobile-readable, source-date-labelled and individually editable via the Client CMS menu collections. Never replace that section with a link to an external PDF, image, Square/Toast store or ordering page. An external ORDER CTA is allowed for checkout, separately from the actual embedded menu. An absent or incomplete menu must be documented rather than invented. The menu_catalog_gate.py validates the source screenshot hash, catalog source completeness, visible DOM cards and corresponding editable CMS collection attributes.
