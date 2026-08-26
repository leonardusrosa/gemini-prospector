# Hero Image Quality Standard

Use this reference for prominent hero assets, especially `expert_fullscreen` desktop/mobile images.

The goal is to keep the hero visually premium on 1440p, ultrawide and HiDPI displays without turning one benchmark file size or pixel dimension into a universal requirement.

## 1. Governing principle — HARD RULE

A premium hero should be **visually overqualified before compression, then efficiently compressed**.

Do not generate a small/soft hero and stretch it in CSS. Do not destroy expert facial detail merely to meet an arbitrary KB target.

Priority order:

```text
real identity/source fidelity
→ sufficient source/output resolution
→ visible large-screen sharpness
→ clean compression
→ efficient byte size
```

## 2. Desktop `expert_fullscreen` resolution target

For the preferred ultrawide desktop architecture, use a source/output large enough to remain crisp on wide and HiDPI displays.

Preferred production range when the source/generator supports it:

```text
~3500–4500+ px wide
ultrawide aspect ratio appropriate to the composition
```

A strong reference production result is:

```text
4200 × 1728 WebP
~417 KB
ultrawide expert hero
```

This is a **benchmark, not a mandatory dimension or byte target**.

`3584×1533`, `4200×1728`, or another 3K/4K-class output may all be correct depending on the real source, aspect ratio, rendering size and compression result.

## 3. HARD RULE — no destructive upscale

Do not upscale a weak, blurry or tiny source solely to hit a nominal 4K dimension.

If the source does not contain enough real detail:

1. prefer a better first-party source image;
2. use native/reference-based generation or source-preserving enhancement when available;
3. preserve the real expert identity;
4. stop increasing resolution when it only creates synthetic sharpness/halos.

Pixel count alone does not equal quality.

## 4. Visual quality gate

Before accepting a desktop hero, inspect it at the actual website size and at least one large desktop/wide viewport.

Required QA:

```text
Desktop Hero Quality QA
Source/output resolution: PASS
Large-screen sharpness: PASS
Expert facial detail: PASS
Hair/clothing edge detail: PASS
Compression artifacts: NONE MATERIAL
Oversharpening/halos: NONE MATERIAL
Ultrawide composition: PASS
Expert right-half centering: PASS
No destructive upscale: PASS
LCP/preload integration: PASS
```

Reject/reprocess when:

- face becomes visibly soft at 1440p/wide review;
- skin/hair/clothing is smeared by compression;
- ringing/halos appear around face, hair or clothing;
- blockiness/banding is noticeable in the background;
- generated enhancement changes identity or creates fake facial texture;
- high pixel dimensions mask a poor-quality source.

## 5. Compression — quality per byte, not smallest file

Prefer WebP/AVIF or another modern format supported by the workflow.

Use perceptual inspection after compression.

Rules:

- preserve expert facial fidelity first;
- a hero in the ~400–500 KB range can be acceptable when it is the primary visual/LCP asset and the quality justifies the bytes;
- smaller is better only when the visual result is materially unchanged;
- files above that range are also allowed when genuinely justified by image complexity and target rendering;
- do not force an arbitrary `200 KB`/`300 KB` ceiling if it visibly damages the hero.

WebP quality values such as `90–99` are tuning heuristics, not universal requirements.

## 6. Resampling / sharpening

Lanczos or an equivalent high-quality down/up-resampling filter is appropriate for offline preparation.

Restrained sharpening may be used after resampling.

Do not:

- oversharpen skin;
- create white/dark halos around hair or clothing;
- invent microtexture that changes the person's appearance;
- use aggressive super-resolution as a substitute for a good real source.

## 7. Mobile quality

The dedicated mobile hero must also be source-quality, not merely a low-resolution crop.

- target at least enough native pixels for a crisp modern phone/HiDPI render;
- `1080px` width is a useful baseline when supported;
- higher resolution is allowed when it materially improves the result without unnecessary payload;
- preserve face/upper-body detail and first-fold composition;
- do not reuse a low-quality crop from the ultrawide desktop asset.

## 8. Performance integration — HARD RULE

Quality does not excuse incorrect loading behavior.

- hero/LCP asset must not use `loading="lazy"`;
- preload the critical desktop/mobile hero resource when appropriate;
- use `fetchpriority="high"` on the actual LCP `<img>` when applicable;
- for CSS-background heroes, use `<link rel="preload" as="image">`;
- reserve stable hero geometry to avoid CLS;
- do not preload non-critical gallery assets.

## 9. Reporting

Record, when measurable:

```text
Desktop Hero Asset: [path]
Dimensions: [width × height]
Encoded Size: [KB]
Format: [WebP/AVIF/...]
Large-Screen Sharpness QA: PASS | FAIL
Facial Detail QA: PASS | FAIL
Compression Artifact QA: PASS | FAIL
No Destructive Upscale: PASS | FAIL
```

Do not report a file as "high quality" based on dimensions alone.