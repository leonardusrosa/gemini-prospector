---
name: hero-copy-density
description: HARD RULE and governance standard for hero copy structure and density on all public prospect sites. Eliminates redundant repetition of material facts across hero layers (eyebrow, headline, supporting copy, trust metadata, CTA). Enforces a disciplined, editorial 5-layer hero architecture, compact single-line trust presentation, and natural evidence-backed phrasing. Mandatory for every new or regenerated site.
---

# Hero Copy Density & De-Duplication Rule

This standard is mandatory for every new or actively regenerated public website created or audited by Prospector. It has absolute authority over hero textual composition and applies across GPT-Taste creative direction, copywriting review, and deterministic QA.

---

## 1. The 5 Hero Fact Layers

Every hero section is organized into up to five distinct structural layers:

1. **EYEBROW (`EYEBROW_FACTS`)**: Architectural location, service category, or business identifier (e.g., `AUTO DETAILING • ADDISON, TEXAS`).
2. **HEADLINE (`HEADLINE_FACTS`)**: Dominant, factual primary offer or capability statement (e.g., `AUTOMOTIVE DETAILING & PAINT REFINEMENT`).
3. **SUPPORTING COPY (`SUPPORTING_COPY_FACTS`)**: Exactly one short sentence expanding service scope or factual specialty.
4. **CTA (`CTA_FACTS`)**: One disciplined primary contact or action trigger (e.g., `Call (214) 400-7287 →`).
5. **TRUST METADATA (`TRUST_FACTS`)**: Maximum one compact editorial trust line (e.g., `★ 4.9 / 268 Reviews`).

---

## 2. Universal De-Duplication Invariant

**Rule:** The same material fact must never be repeated across hero layers. Repeating a fact across layers unnecessarily triggers an automatic **FAIL**.

### Fact Dimensions to Audit:
- **Location / City:** If city/state appears in the Eyebrow, it must NOT appear in Supporting Copy or CTA.
- **Rating:** If aggregate rating (e.g., `4.9`) appears in Trust Metadata, it must NOT be mentioned in Supporting Copy.
- **Review Count:** If review volume (e.g., `268 Reviews`) appears in Trust Metadata, it must NOT be mentioned in Supporting Copy.
- **Phone Number:** If phone number appears in the primary CTA button/link, it must NOT be repeated in Supporting Copy.
- **Service Scope:** Core service keywords should be divided cleanly between Headline and Supporting Copy rather than repeating the exact same terms.
- **Expert / Person:** Do not repeat the owner or specialist name in both eyebrow and supporting copy.

### Fact Normalization:
Gate checks normalize semantic equivalents:
- `4.9`, `4.9 / 5`, `4.9 rating`, `★ 4.9` are evaluated as the same rating fact.
- `268 reviews`, `268 public reviews`, `268` are evaluated as the same review-count fact.
- Formatted phone numbers `(214) 400-7287` and raw digits `2144007287` are evaluated as the same phone fact.
- `Addison`, `Addison, TX`, `Addison, Texas` are evaluated as the same location fact.

---

## 3. Supporting Copy Discipline & Natural English

Supporting copy must remain concise (1 short sentence) and describe the actual service capabilities.

### Banned Repetitions in Supporting Copy:
- Do **NOT** write: `Auto detailing in [City]. Backed by a 4.9 rating across 268 reviews.` (Duplicates location and trust facts).
- Do **NOT** write: `Call us today at [Phone] for appointments.` (Duplicates CTA).
- Do **NOT** write unnatural phrasing such as: `Individual service by Wilson` (Awkward English). If verified expert relationship is established and desired, use natural syntax: `Detailing and paint correction by Wilson.`—provided it introduces no duplicate facts. If direct evidence is ambiguous, omit personal names from supporting copy entirely.

---

## 4. Trust Presentation & Source-Neutral Wording

### Compact Editorial Trust Line:
Trust metadata must be rendered as a single compact editorial line:
```text
★ 4.9   /   268 Reviews
```
or
```text
4.9 / 5   •   268 Reviews
```

### Prohibited Trust Formats:
- NO separate rating cards or review cards.
- NO dual stat boxes or floating cards.
- NO pill badges, badge clusters, or pill capsules.
- NO platform vendor names (`Google`, `Google Reviews`, `Google Maps`).
- The word **"Public"** is NOT required merely to achieve source neutrality. Prefer clean terms: `Rating`, `Reviews`. Only include "Public" if disambiguation strictly requires it.

---

## 5. Hero Density Ceiling

The hero is an executive entry portal, not an exhaustive summary.

- **Eyebrow:** 0 or 1 line.
- **Headline:** 1 dominant title.
- **Supporting Copy:** 1 concise sentence (maximum 18 words).
- **CTA:** Exactly 1 primary action button or link.
- **Trust:** Maximum 1 compact line.

Do not transform the hero section into an About section, review summary, service catalog, or contact directory.
