# Engine A Design Intelligence Backport

## Purpose
This document backports the architectural and editorial design principles proven in Engine B3 into **Engine A** (the vanilla HTML/CSS/JS engine) **without** introducing React, npm, build steps, or runtime complexity.

---

## 1. Spatial Rhythm & Negative Space
- **Current Engine A Pattern**: Tight vertical stacking (`py-12` / `py-16`) with uniform section breaks.
- **Engine B3 Learning**: Expand vertical spacing to **editorial scale** (`py-28` to `py-36` on desktop / `7rem` to `9rem`). High negative space immediately elevates perceived brand prestige for luxury automotive services.

## 2. Strict Card Budget (Maximum 1 Card per Viewport)
- **Current Engine A Pattern**: Repeated 3-column card grids for services and reviews.
- **Engine B3 Learning**: 
  - **Services**: Replace 3x3 cards with a **Horizontal Numbered Service Index** (`[ 01 ]` to `[ 06 ]`) with hairline dividers (`border-b border-white/10`).
  - **Reviews**: Replace multi-card carousel/grid with a **Single Dominant Pull-Quote Spotlight** flanked by subtle typographic index controls (`[ 01 ]`, `[ 02 ]`, `[ 03 ]`).

## 3. Ban on Generic Pill Bias
- **Current Engine A Pattern**: Floating island pill navbars, pill-shaped tags, pill buttons.
- **Engine B3 Learning**:
  - Replace floating island pill navbar with a **Full-Width Architectural Hairline Navigation** (`border-b border-white/[0.08]`, backdrop-blur, uppercase tracking).
  - Use crisp rectangular buttons (`rounded-none` or `rounded-sm`) with gold accent borders rather than pill capsules.
  - Typographic selectors replace pill chips.

## 4. Large Media Territory & Hero Geometry
- **Engine B3 Learning**: Full-width universal media plane (≥ 98% viewport width) with high-priority preloaded poster (`fetchpriority="high"`) and ambient video playback. Text is positioned in an asymmetric lower grid rather than boxed cards.

## 5. Review Provenance & Truth Invariant
- **Claim Hardening**: Visible badges must use strictly `Public Review` or `Public Rating`. All review provenance (Google Maps place profile, author name, timestamp) remains strictly in metadata/internal files, never exposed as marketing hype.
