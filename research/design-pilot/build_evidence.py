import json
import sys
from pathlib import Path
from datetime import datetime

# Add prospector-de-sites to path
sys.path.insert(0, str(Path("prospector-de-sites").resolve()))
from google_reviews_evidence import compute_entry_fingerprint, validate_evidence

PLACE_URL = "https://www.google.com/maps/place/Dentista+Dra.+Francine+Goulart/@-22.4125632,-47.5594921,17z/data=!4m6!3m5!1s0x94c7da5a58a30833:0x1f93843856f80228!8m2!3d-22.4125632!4d-47.5594921!16s%2Fg%2F11kn6x5g20"
PLACE_ID_CID = "0x94c7da5a58a30833:0x1f93843856f80228"
COLLECTED_AT = "2026-09-01T13:26:00-03:00"

raw_entries = [
    {
        "nativeReviewId": "Ci9DQUlRQUNvZENodHljRjlvT25kbmNHUktOMU53UTJZM1NYVTJSWGszTFhVeFlrRRAB",
        "author": "Luis",
        "rating": 5,
        "dateLabel": "um ano atrás",
        "text": "Foi muito bom excelente dentista eu recomendo",
        "hasText": True,
        "textEvidenceId": "review-1"
    },
    {
        "nativeReviewId": "ChdDSUhNMG9nS0VJQ0FnTUNvMHMtOHBnRRAB",
        "author": "Maria José Leite",
        "rating": 5,
        "dateLabel": "um ano atrás",
        "text": "Muuto eficiente e atenciosa.",
        "hasText": True,
        "textEvidenceId": "review-2"
    },
    {
        "nativeReviewId": "Ci9DQUlRQUNvZENodHljRjlvT25FdFRqQnhPVVppVW1ObFozZEpVbk5mWmtGNFMxRRAB",
        "author": "DELMA LOPES MATOS",
        "rating": 5,
        "dateLabel": "2 meses atrás",
        "text": "",
        "hasText": False,
        "textEvidenceId": None
    },
    {
        "nativeReviewId": "Ci9DQUlRQUNvZENodHljRjlvT2paS1RHbHNWWEJ1V1RGSFJYWTJUMWg0VFZwTVgyYxAB",
        "author": "isabelly polido",
        "rating": 1,
        "dateLabel": "2 meses atrás",
        "text": "",
        "hasText": False,
        "textEvidenceId": None
    },
    {
        "nativeReviewId": "ChZDSUhNMG9nS0VJQ0FnTURvX29PRmJBEAE",
        "author": "Yasmin Breda",
        "rating": 5,
        "dateLabel": "um ano atrás",
        "text": "",
        "hasText": False,
        "textEvidenceId": None
    }
]

reviews = [
    {
        "id": "review-1",
        "author": "Luis",
        "rating": 5,
        "dateLabel": "um ano atrás",
        "text": "Foi muito bom excelente dentista eu recomendo",
        "source": "google_maps",
        "placeIdOrCid": PLACE_ID_CID,
        "nativeReviewId": "Ci9DQUlRQUNvZENodHljRjlvT25kbmNHUktOMU53UTJZM1NYVTJSWGszTFhVeFlrRRAB"
    },
    {
        "id": "review-2",
        "author": "Maria José Leite",
        "rating": 5,
        "dateLabel": "um ano atrás",
        "text": "Muuto eficiente e atenciosa.",
        "source": "google_maps",
        "placeIdOrCid": PLACE_ID_CID,
        "nativeReviewId": "ChdDSUhNMG9nS0VJQ0FnTUNvMHMtOHBnRRAB"
    }
]

observed_entries = []
for r in raw_entries:
    review_text = r["text"] if r["hasText"] else ""
    fp = compute_entry_fingerprint(
        place_id=PLACE_ID_CID,
        author=r["author"],
        rating=r["rating"],
        date_label=r["dateLabel"],
        text=review_text,
        native_review_id=r["nativeReviewId"]
    )
    entry = {
        "fingerprint": fp,
        "fingerprintVersion": "maps-native-id-v1",
        "nativeReviewId": r["nativeReviewId"],
        "author": r["author"],
        "rating": r["rating"],
        "dateLabel": r["dateLabel"],
        "hasText": r["hasText"],
        "textEvidenceId": r["textEvidenceId"],
        "sourceSurface": "direct_google_maps",
        "collectedAt": COLLECTED_AT,
        "provenance": {
            "authorObserved": True,
            "ratingObserved": True,
            "dateLabelObserved": True,
            "nativeReviewIdObserved": True,
            "textObserved": r["hasText"]
        }
    }
    observed_entries.append(entry)

evidence_data = {
    "profileName": "Dentista Dra. Francine Goulart",
    "profileUrl": PLACE_URL,
    "googleMapsFeatureId": "0x94c7da5a58a30833:0x1f93843856f80228",
    "placeId": None,
    "cid": "2275304677764727336",
    "placeIdOrCid": "0x94c7da5a58a30833:0x1f93843856f80228",
    "aggregateRating": 4.2,
    "ratingCount": 5,
    "reviewCount": 5,
    "collectedAt": COLLECTED_AT,
    "sourceSurface": "direct_google_maps",
    "collectionMethod": "playwright_direct_maps",
    "profileHeaderObserved": True,
    "reviewsPanelOpened": True,
    "reviewsPanelFullyTraversed": True,
    "textReviewCollectionAttempted": True,
    "aggregateObservation": {
        "ratingText": "4,2",
        "countText": "5 avaliações",
        "surfaceUrl": PLACE_URL
    },
    "reviewsPanelObservation": {
        "countText": "5 avaliações",
        "surfaceUrl": PLACE_URL
    },
    "observedRatingEntries": 5,
    "observedTextReviewEntries": 2,
    "starOnlyRatingCount": 3,
    "capturedTextReviewCount": 2,
    "reviews": reviews,
    "observedEntries": observed_entries
}

# Validate with deterministic validator
res = validate_evidence(evidence_data)
print("Validator status:", res.status)
print("Errors:", res.errors)
print("Warnings:", res.warnings)

out_file = Path("research/design-pilot/google-reviews-evidence.json")
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(evidence_data, f, ensure_ascii=False, indent=2)
print(f"Wrote evidence to {out_file}")
