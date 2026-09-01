import json
from pathlib import Path

evidence_path = Path("sites/clinica-dra-francine-goulart-rio-claro/research/google-reviews-evidence.json")
evidence = json.loads(evidence_path.read_text(encoding="utf-8"))

manifest = {
    "schemaVersion": 2,
    "slug": "clinica-dra-francine-goulart-rio-claro",
    "siteMode": "new_site_concept",
    "preview": True,
    "businessName": "Clínica Odontológica Dra. Francine Goulart",
    "niche": "odontologia",
    "city": "Rio Claro",
    "state": "SP",
    "phone": "19998844898",
    "whatsapp": {
        "verified": True,
        "number": "5519998844898",
        "floatingRequired": True,
        "contactActionRequired": True,
        "mockAffordanceRequired": False
    },
    "address": {
        "verified": True,
        "public": True,
        "mapEmbedRequired": True,
        "text": "Avenida 7, nº 310, Centro, Rio Claro - SP, CEP 13506-800"
    },
    "cnpj": "33.339.590/0001-30",
    "factualEvidence": {
        "verifiedServices": [
            {
                "claim": "Avaliação e Prevenção",
                "verified": True,
                "source": "official_record"
            },
            {
                "claim": "Restaurações Estéticas",
                "verified": True,
                "source": "official_record"
            },
            {
                "claim": "Profilaxia Profissional",
                "verified": True,
                "source": "official_record"
            },
            {
                "claim": "Conservação e Alívio de Dor",
                "verified": True,
                "source": "official_record"
            }
        ]
    },
    "openDesignDirection": {
        "required": True,
        "mcpServerName": "open-design",
        "mcpProbeAttempted": True,
        "status": "used",
        "directionsGenerated": 2,
        "selectedDirection": "Ateliê Clínico Editorial",
        "designMdPath": "open-design/DESIGN.md",
        "gptTasteSelectionReviewed": True
    },
    "gptTaste": {
        "required": True,
        "skillSha256Required": True
    },
    "heroVisual": {
        "required": True,
        "kind": "expert-placeholder",
        "sourceType": "generated-template",
        "templateId": "dentistry-female",
        "desktopAssetPath": "assets/templates/dentistry-female.webp",
        "mobileAssetPath": "assets/templates/dentistry-female-mobile.webp",
        "representsActualBusiness": False,
        "representsActualExpert": False,
        "illustrativeDisclosureRequired": True,
        "expertBackgroundRequired": True,
        "desktopFullWidthRequired": True,
        "mobileFullWidthRequired": True
    },
    "googleReviews": {
        "checked": True,
        "sourceSurface": evidence["sourceSurface"],
        "collectionMethod": evidence["collectionMethod"],
        "placeId": evidence["placeId"],
        "cid": evidence["cid"],
        "profileName": evidence["profileName"],
        "profileUrl": evidence["profileUrl"],
        "verifiedGoogleProfile": True,
        "collectedAt": evidence["collectedAt"],
        "aggregateRating": evidence["aggregateRating"],
        "ratingCount": evidence["ratingCount"],
        "observedRatingEntries": evidence["observedRatingEntries"],
        "observedTextReviewEntries": evidence["observedTextReviewEntries"],
        "capturedTextReviewCount": evidence["capturedTextReviewCount"],
        "starOnlyRatingCount": evidence["starOnlyRatingCount"],
        "usableTextReviews": evidence["capturedTextReviewCount"],
        "profileHeaderObserved": evidence["profileHeaderObserved"],
        "reviewsPanelOpened": evidence["reviewsPanelOpened"],
        "reviewsPanelFullyTraversed": evidence["reviewsPanelFullyTraversed"],
        "textReviewCollectionAttempted": evidence["textReviewCollectionAttempted"],
        "aggregateObservation": evidence["aggregateObservation"],
        "reviewsPanelObservation": evidence["reviewsPanelObservation"],
        "state": "VERIFIED_TEXT_LIMITED",
        "reviewSectionRequired": True,
        "reviewSectionRendered": True,
        "reviews": [
            {**r, "verified": True, "hasText": True} for r in evidence["reviews"]
        ],
        "observedEntries": evidence["observedEntries"]
    },
    "motion": {
        "required": True,
        "minimumRevealGroups": 2,
        "headerScrollStateRequired": True
    },
    "assistant": {
        "present": False
    },
    "instagram": {
        "state": "not_applicable",
        "mockAffordanceRequired": False
    }
}

manifest_file = Path("sites/clinica-dra-francine-goulart-rio-claro/review-manifest.json")
with open(manifest_file, "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
print(f"Wrote manifest to {manifest_file}")
