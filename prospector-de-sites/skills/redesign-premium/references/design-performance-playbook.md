# Reusable Design & Performance Playbook

Use this reference during `redesign-premium` after factual research and before final QA. It separates **hard rules** from **mode-specific defaults** and **implementation heuristics** so useful lessons do not become another universal aesthetic template.

## 1. Rule hierarchy

Apply in this order:

1. factual integrity and authentic assets;
2. accessibility/usability;
3. subject-safe responsive composition;
4. performance/LCP/CLS;
5. business-specific art direction;
6. optional visual treatments.

Never promote a style treatment into a universal rule merely because it worked for one prospect.

---

## 2. HARD RULE — source tree before design

For `siteMode = redesign`, the official site is a source tree, not one homepage.

Read and follow `first-party-source-crawl.md`.

Before final Design Read:

- inspect relevant same-domain internal pages;
- capture stronger first-party facts and images;
- build provenance for important claims/assets;
- do not score content availability from the homepage alone when useful internal pages are discoverable.

---

## 3. HARD RULE — subject-safe hero rendering

Never use `cover` mechanically when it damages the primary visual subject.

Before choosing `cover`, test at wide desktop widths and ask:

- does the expert/product/venue remain recognizable?
- is the head/torso/product edge being cropped?
- does the composition still preserve the intended copy negative space?
- does the subject appear to zoom aggressively as viewport width increases?

If not, use a subject-safe strategy such as:

- dedicated desktop/mobile assets;
- `<picture>` + controlled `<img>` positioning;
- `object-fit: contain` or controlled `object-position`;
- background `contain` + anchored positioning;
- source-preserving compositing.

`contain` is a useful default for some expert heroes, not a universal requirement.

### Expert overlay boundary

If an overlay/gradient is needed for copy readability:

- confine it to the copy territory/environment;
- the expert's face, torso, shoulders, uniform/clothing and hands remain visually intact;
- do not fade the subject itself.

### Visible image edges

When a generated/composited hero reveals rectangular boundaries, dissolve those boundaries into the page/background with a subtle edge treatment, vignette or tonal continuation.

This is conditional: do not add a vignette when the image already fills the frame naturally.

### Hero-to-section transition

For immersive/composited heroes, avoid a hard divider if it creates an artificial seam. Prefer a smooth tonal/gradient transition into the next section when it improves continuity.

Do not ban borders globally; functional dividers remain valid elsewhere.

---

## 4. MODE DEFAULT — desktop `expert_fullscreen` ultrawide architecture

For desktop expert-led heroes with copy on the left and the real expert on the right, **prefer an art-directed ultrawide source asset instead of standard 16:9** when this improves subject preservation across wide displays.

### Preferred asset geometry

Recommended range:

```text
~2.3:1 to ~2.6:1
```

A 3K/4K-class canvas such as `3584×1533` is a useful example, not a hard requirement.

### HARD RULE — center expert inside right half

For this pattern, the expert is not merely "on the right".

The expert's visual center should sit approximately at the center of the **right half** of the asset:

```text
expert center ≈ x 75% of canvas
```

This protects three things simultaneously:

- left-half negative space for copy;
- breathing room around the expert;
- stable subject placement under `contain` on 1080p, 1440p, ultrawide and 4K-like widths.

Reject layouts where the expert:

- is pinned awkwardly against the far-right edge;
- drifts into the left/copy half;
- becomes partially cropped because the source was composed like a conventional 16:9 full-bleed photo.

### Preferred rendering behavior

For this mode, `contain` + stable anchoring is often the preferred desktop rendering architecture because it prevents viewport-driven zoom.

Typical pattern:

```css
.hero-section {
  position: relative;
  background-color: var(--hero-bg);
  background-image: url('assets/hero-expert-desktop.webp');
  background-size: contain;
  background-position: right center;
  background-repeat: no-repeat;
  min-height: clamp(580px, calc(100vh - var(--header-height, 105px)), 840px);
  display: flex;
  align-items: center;
  overflow: hidden;
}
```

The exact dimensions/height limits are heuristics. Use a single coherent height declaration rather than contradictory rules that override each other.

### Avoid desktop breakpoint jumps

Within the desktop range, prefer fluid CSS behavior over chains of hard `@media` zoom/position overrides.

A dedicated mobile breakpoint is appropriate because mobile uses a different composition/asset. Avoid unnecessary intermediate desktop breakpoints that create visible resize jumps.

### Four-edge integration

When `contain` intentionally leaves clean page background around the ultrawide image, no rectangular image box should remain visible.

If needed, dissolve **all visible canvas edges** into the hero background.

Four-edge feathering is a valid implementation technique, but:

- feather environment/canvas edges only;
- protect the expert silhouette at full opacity;
- do not let the expert intersect the fade zones.

Example values for a ~3584px-wide canvas may start around:

```text
left   ~220px
right  ~220px
top    ~110px
bottom ~130px
```

These values are heuristics and must scale with the actual image.

### Copy gradient

A bounded left-side readability gradient is allowed when needed. It must resolve to transparent before crossing the expert silhouette.

Example only:

```css
.hero-gradient-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    var(--hero-bg) 0%,
    rgba(248,250,249,.95) 28%,
    rgba(248,250,249,.40) 44%,
    transparent 54%
  );
  pointer-events: none;
}
```

Adapt color/stops to the actual page. The principle is fixed; the numbers are not.

### Smooth bottom transition

For a light immersive/composited hero, a soft bottom fade into the following section is a valid default when it removes a visible seam.

Do not force this effect if the hero already transitions naturally.

---

## 5. MODE DEFAULT — streamlined navigation

Prefer a single streamlined primary header over a cluttered utility bar + navbar stack.

Move secondary phone/social actions into:

- compact header actions;
- mobile drawer/menu;
- contact section.

Keep a top utility bar only when it has clear business value, e.g. emergency contact, materially different locations, critical opening state or another high-priority utility.

### Glass/translucent header

A translucent/glass header is an **optional treatment** for immersive heroes, not a default aesthetic.

Use only when it improves separation/legibility and fits the business identity.

Reference token, adapt rather than copy blindly:

```css
background: rgba(255,255,255,.72);
backdrop-filter: blur(16px) saturate(180%);
-webkit-backdrop-filter: blur(16px) saturate(180%);
border-bottom: 1px solid rgba(226,235,230,.7);
box-shadow: 0 4px 20px rgba(0,0,0,.02), inset 0 1px 0 rgba(255,255,255,.6);
```

Do not introduce glassmorphism when a solid, transparent or brand-colored header is more appropriate.

---

## 6. MODE DEFAULT — mobile immersive hero flow

For `expert_fullscreen` and similar immersive mobile heroes:

- do not reuse/crop the ultrawide desktop asset;
- do not simply place a portrait in a clipped top rectangle followed by a disconnected white card;
- prefer visual continuity between image and copy when the art direction supports it;
- a soft bottom fade from image into page background is a valid technique;
- keep the expert prominent in the upper region and HTML copy below/away from the face.

Example technique:

```css
.mobile-hero-visual::after {
  content: "";
  position: absolute;
  inset: auto 0 0;
  height: 18%;
  background: linear-gradient(to bottom, transparent, var(--page-bg));
  pointer-events: none;
}
```

Treat the exact fade height/color as implementation detail, not a fixed token.

---

## 7. HARD RULE — image performance and stability

### Hero/LCP

Hero/LCP images:

- must not use `loading="lazy"`;
- should use `fetchpriority="high"` on the actual LCP `<img>` when appropriate;
- preload dedicated desktop/mobile hero assets when they are known critical resources;
- when desktop hero is a CSS background, preload the resource explicitly rather than assuming CSS discovery is fast enough.

Example:

```html
<link rel="preload" as="image" href="assets/hero-expert-desktop.webp" media="(min-width: 769px)" fetchpriority="high">
<link rel="preload" as="image" href="assets/hero-expert-mobile.webp" media="(max-width: 768px)" fetchpriority="high">
```

Do not preload large non-critical gallery images.

### CLS prevention

For normal `<img>` elements, provide intrinsic `width` and `height` whenever known so the browser can reserve aspect ratio before load.

For CSS-background heroes, reserve the hero geometry with stable CSS height/min-height so image arrival cannot collapse/expand layout.

### Below-fold images

Below-fold images should normally use:

```html
loading="lazy" decoding="async"
```

Exceptions are allowed when an image is immediately needed for interaction or likely to become LCP.

### Format/compression

Prefer WebP/AVIF or another modern web format when supported by the workflow.

Optimize for **perceptual quality + byte size**, not one universal quality number.

Useful starting heuristics, not hard limits:

- high-resolution hero source appropriate to the largest intended rendering;
- WebP quality around 90–96 can be a starting point; values such as 99 are acceptable when the byte cost remains justified;
- gallery quality around 80–86 often works;
- aim for heroes around or below a few hundred KB when visual quality permits;
- aim for gallery images below ~100 KB when practical.

Lanczos is a suitable high-quality resampling option for offline resizing, but the implementation may use another equivalent high-quality filter.

Restrained unsharp masking may restore detail after resize, but avoid halos/oversharpened skin.

Never degrade a real expert face simply to hit an arbitrary byte threshold.

---

## 8. MODE DEFAULT — location conversion module

When physical location materially affects conversion, prefer a compact, usable location module containing verified information:

- address;
- opening hours when factual;
- direct route CTA such as `Abrir rota` / locale equivalent;
- optional responsive map embed when it adds value.

If the map iframe is below the fold:

```html
loading="lazy"
```

A map embed is optional. If it creates unnecessary weight or clutter, keep the verified address + route CTA instead.

Never invent coordinates or location details.

---

## 9. Implementation heuristics — not hard rules

These are examples the agent may use, adapt or reject.

### Ultrawide canvas

`2.3:1–2.6:1`, `3584×1533`, exact feather widths, WebP `quality=99`, Lanczos and dual-stage unsharp mask are implementation references — not universal requirements.

What **is** required for the preferred desktop expert architecture is:

- subject-safe composition;
- expert centered in right half;
- stable no-zoom behavior;
- no visible rectangular box edges;
- expert remains fully opaque.

### Wide expert background anchoring

For a hero implemented as CSS background, a subject-safe pattern may also use custom anchoring when `right center` is insufficient:

```css
background-size: contain;
background-position: right max(0px, calc(50vw - 660px)) center;
background-repeat: no-repeat;
```

The `660px` value is layout-specific. Derive the anchor from the actual max-width/copy geometry; do not copy it to every project.

### Compression

Exact WebP quality, image dimensions and byte budgets are tuning values. Measure screenshots/LCP and inspect the image instead of assuming one recipe.

---

## 10. Anti-universalization rules

Do NOT turn these into defaults across all businesses:

- glassmorphism;
- blurred backgrounds;
- top utility bar removal regardless of context;
- `contain` for every hero mode;
- ultrawide for every non-expert hero;
- map iframe on every site;
- vignettes on every image;
- one fixed WebP quality;
- one fixed feather width;
- one fixed background-position formula.

The governing principle is **business-specific art direction with reusable engineering standards**.

---

## 11. QA checklist

Before accepting the website:

### Research
- relevant official subpages were inspected when `redesign`;
- stronger facts/assets from internal pages were considered.

### Desktop expert hero
- ultrawide was considered/preferred when it preserves the subject better than 16:9;
- expert visual center is in the center of the right half;
- expert does not drift into copy territory or pin awkwardly to the right edge;
- main subject survives 1280/1440/ultrawide review;
- no destructive `cover` crop or viewport-driven zoom;
- no overlay washes out the expert;
- composited edges do not reveal an accidental rectangle;
- desktop resize is fluid rather than a sequence of visible breakpoint jumps.

### Mobile hero
- dedicated mobile asset is used when required;
- mobile is purpose-composed and first-fold aware;
- image→copy transition is not an accidental hard box/card seam.

### Navigation
- no redundant utility/header clutter;
- glass used only if justified;
- mobile secondary actions move cleanly into menu/drawer when appropriate.

### Performance
- hero is not lazy-loaded;
- correct critical hero is preloaded when useful;
- `<img>` dimensions or stable CSS geometry prevent avoidable CLS;
- below-fold imagery uses lazy/async by default;
- assets are appropriately compressed without visible subject degradation.

### Location
- route action is direct and factual;
- map iframe, if used below fold, is lazy-loaded;
- location module is compact rather than a heavy decorative section.