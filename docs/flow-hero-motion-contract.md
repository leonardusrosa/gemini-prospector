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

## Pilot execution checkpoint (Nov 23)

The first Feral pilot downloaded four stills and two actual 7.93-second clips (1280x720 and 720x1280). This is a supervised browser proof, not an automated executor or final stage acceptance. Flow-a showed 1,050 starting credits; two clips were quoted at 10 credits each. The four still charges and final balance were not reconciled. Do not fabricate a complete ledger from this run. Human approval remains pending.

The pilot has no fixed per-lead credit cap (null), but the account balance, six base generations and two total retry limit still apply. No purchases. For the next pilot, the trusted single browser operator uses flow_execution_ledger.py to reserve and atomically checkpoint a request BEFORE any submission, then reconcile the same account's balance and download (or observed failure) with immutable evidence. Unknown outcomes block all further requests; never resubmit after a crash without reconciliation. Switch accounts only between reconciled requests, and explicitly transfer the matching frame pair if needed. The ledger produces delivery inputs, not visual QA or approval. It is not a security boundary against arbitrary local file writes; production browser adapter and separate authenticated owner signer remain outstanding.

### Required shot direction (owner feedback, Nov 23)

Write concrete physical instructions, not aesthetic filler: no cinematic, premium, stunning, tasteful or similar generic wording in Flow prompts. Specify camera setup, independently composed endpoints, continuous timed camera and subject actions covering the entire clip, protected text areas, continuity and shot-specific exclusions. Compile the video prompt from the structured motionDirection using hero_motion_direction.py. Reserve settling for at most the final second; intentional fixed camera is allowed if subject action supplies motion. Endpoints must visibly support the intended action. No effect whitelist: effects must be deliberate, physically plausible and brand-specific. Review actual playback through the full duration and reject early stops, unplanned effects and failure to follow the directed movement, regardless of technical QA. For food, explicitly exclude flames on or touching food unless the specific cooking action requires them. Do not regenerate rejected assets without recording a new candidate and the applicable generation budget.


### Flow execution policy (November 24, 2026)

Headless Flow generation is suspended for all account aliases. Following an unusual-activity warning and an unrelated or potentially related subscription entitlement change, automated Flow submissions are also paused pending clarification. Use only a normal visible browser with human-operated generation when the provider allows access; no automated clicks, stealth changes, account rotation or retries to work around restrictions. Keep the owner's desktop undisturbed: the owner opens the dedicated browser and submits the request. The engine may prepare prompts, frame assets, local QA and ledger records offline. Do not resume automated submissions until provider restrictions are resolved and the owner authorizes a permitted workflow. The V4 request remains unreconciled; no repeat until verified. Ordinary headless website QA is unaffected.


### Motion brief v2 and provider policy (November 27, 2026)

Use motionDirection version 2 for new candidates; version 1 remains readable and validates with its original compiler for existing signed artifacts. The v2 internal brief retains cameraSetup, startComposition, endComposition, protectedTextArea and forbiddenEffects, and adds product_lock, physical_continuity, camera_choreography, temporal_sequence (the timed camera/action/phase list replacing beats) and end_state. physical_continuity replaces continuity. State exactly what remains invariant and what moves, including realistic contact, gravity and shape where relevant. The timed sequence must cover the clip, without premature settling. First and last frame descriptions and camera setup remain in the internal brief; compile only the motion, invariants, timing, exclusions, text-safe region and final state into the Flow execution prompt. The 180-word ceiling is an internal experimental guardrail, not a Google limit. Do not re-describe the reference image unnecessarily. QA remains independent; neither prompt structure nor syntactic validation proves physical plausibility or endpoint adherence.

Reference inspiration: https://www.threads.com/@arnoldalvaro/post/DgP6ShKjzNp (public reply describes ordered actions, settling and realistic physical behavior; parent thread and resulting video not verified). Google image-to-video prompting guidance: https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/video/best-practice

Image creation: ChatGPT Image Generation or permitted human-operated visible Google Flow. Video: human-operated visible Google Flow remains the default; local ComfyUI, Comfy Cloud and fal benchmarks are paused. No new generation, provider charge, automatic browser submission or account rotation is authorized by this compiler. V4 charge reconciliation and the November 24 restrictions remain binding. Preserve rejected assets and ledger evidence; do not overwrite prior plan or approval hashes. Ordinary headless website QA is unaffected.
