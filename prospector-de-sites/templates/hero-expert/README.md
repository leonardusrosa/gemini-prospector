# Hero Expert Template Library

## 1. Purpose
Reusable hero visual assets for first-version prospect concepts when a verified, usable real expert photo is unavailable during initial prospecting.

## 2. Selection Hierarchy
When designing or generating a prospect concept, visual assets must follow this strict selection order:
1. **Verified real expert image** (e.g. from validated first-party sources or official verified credentials).
2. **Verified first-party business/environment image** (e.g. real clinic facilities verified by place evidence).
3. **User/client-provided image** (explicitly submitted by the client).
4. **Matching hero-expert template** from this canonical library (`prospector-de-sites/templates/hero-expert/manifest.json`).
5. **Custom contextual illustrative hero** if no suitable template exists in the library for the niche.

## 3. Factual Integrity & Representation Rules
- **CRITICAL**: The template is **NOT** the real professional and **NOT** the real facility.
- Never present or label template silhouettes as the actual professional (e.g., never say "Dra. X", "Dr. X", "Foto da Dra. Aline", etc.).
- Never describe template clinical backgrounds as the real clinic installation (e.g., never say "nosso consultório", "nossa clínica", "instalações reais").
- When a template is rendered in HTML:
  - Must include `data-image-context="illustrative"` on the `<img>` tag or container.
  - Must use a factual, neutral `alt` text, e.g.:
    `"Imagem ilustrativa de consultório odontológico com espaço reservado para foto profissional"`
  - Manifest review must declare:
    - `representsActualExpert: false`
    - `representsActualBusiness: false`
    - `containsPhotoPlaceholder: true`
    - `placeholderText: "SUA FOTO AQUI"`

## 4. Expert Photo Replacement Workflow
A template with "SUA FOTO AQUI" is a **prospecting placeholder only**.
Once a verified real expert photo is obtained from the client/professional:
1. Replace placeholder asset with the real professional portrait.
2. Preserve the expert's true identity, features, and professional attire.
3. Build a dedicated desktop ultrawide composition (at least ~2000px wide) with negative space for copy.
4. Build a dedicated mobile composition (at least ~900px wide) with appropriate vertical crop and soft fade for text readability.
5. Remove the "SUA FOTO AQUI" badge and placeholder silhouette entirely.
6. Update the site's `review-manifest.json`:
   - `representsActualExpert: true`
   - `sourceType: "first_party"` (or `"user_provided"`)
   - `containsPhotoPlaceholder: false`

## 5. Library Structure
```
templates/hero-expert/
├── README.md
├── manifest.json
└── <niche>/
    ├── male/
    │   ├── desktop-ultrawide.webp
    │   └── mobile.webp
    └── female/
        ├── desktop-ultrawide.webp
        └── mobile.webp
```
