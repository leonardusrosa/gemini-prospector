"""Trusted administrator-side review bundle preparation and receipt verification.

No signing capability in the worker. Deploy the dashboard signer and bundle
directory under a separate owner-controlled identity, not worker-writable.
"""
from pathlib import Path
import json,os,shutil,tempfile,base64
from datetime import datetime,timezone
from hero_motion import sha_file,read_json,validate_plan,validate_delivery,is_storyboard,SHA256

RECEIPT_FIELDS=("leadSlug","planSha256","deliverySha256","qaSha256",
                "sourceManifestSha256","reviewBundleSha256","approverId","decision","issuedAt")
MEDIA_LIMIT=32*1024*1024

def receipt_payload(receipt):
    values=[receipt.get(k) for k in RECEIPT_FIELDS]
    if not all(isinstance(v,str) and v and "|" not in v for v in values):
        raise ValueError("Malformed owner receipt")
    return ("engine-c-owner-review-v2|"+"|".join(values)).encode("utf-8")

def verify_receipt(plan,delivery,qa,receipt,*,public_key=None,owner_id=None):
    from cryptography.hazmat.primitives.serialization import load_pem_public_key
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from cryptography.exceptions import InvalidSignature
    if receipt.get("schemaVersion")!=2 or receipt.get("decision")!="APPROVED" or receipt.get("channel")!="authenticated_admin_review" or receipt.get("actorType")!="human" or receipt.get("autoSelected") is not False:
        raise ValueError("Explicit owner approval required")
    expected={"leadSlug":plan.get("leadSlug"),"planSha256":plan.get("_fileSha256"),
              "deliverySha256":delivery.get("_fileSha256"),"qaSha256":qa.get("_fileSha256"),
              "sourceManifestSha256":plan.get("sourceManifestSha256")}
    for field,value in expected.items():
        if receipt.get(field)!=value or (field!="leadSlug" and (not isinstance(value,str) or not SHA256.fullmatch(value))):
            raise ValueError("Stale owner receipt: "+field)
    if not SHA256.fullmatch(str(receipt.get("reviewBundleSha256",""))):
        raise ValueError("Owner review bundle hash required")
    owner_id=owner_id or os.environ.get("ENGINE_C_HERO_OWNER_ID")
    if not owner_id or receipt.get("approverId")!=owner_id or owner_id==delivery.get("generatorId"):
        raise ValueError("Owner identity not authorized")
    try:
        issued=datetime.strptime(receipt["issuedAt"],"%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        age=(datetime.now(timezone.utc)-issued).total_seconds()
        if age < -60 or age > 86400*7:
            raise ValueError("Owner approval expired or future-dated")
        if public_key is None:
            filename=os.environ.get("ENGINE_C_HERO_OWNER_PUBLIC_KEY_FILE")
            if not filename:
                raise ValueError("Owner public verification key not configured")
            public_key=Path(filename).read_bytes()
        key=load_pem_public_key(public_key)
        if not isinstance(key,Ed25519PublicKey):
            raise ValueError("Ed25519 public key required")
        key.verify(base64.b64decode(receipt["signature"],validate=True),receipt_payload(receipt))
    except (InvalidSignature,KeyError,TypeError,OSError) as exc:
        raise ValueError("Invalid owner approval signature or configuration") from exc
    return owner_id

def prepare_review_bundle(plan_file,delivery_file,qa_file,source_file,review_root,*,probe=None):
    """Run by trusted administrator on exact review artifacts; not an API endpoint."""
    paths={k:Path(v).resolve(strict=True) for k,v in (("plan",plan_file),("delivery",delivery_file),("qa",qa_file),("source",source_file))}
    hashes={k:sha_file(v) for k,v in paths.items()}
    plan,delivery,qa,source=(read_json(paths[k]) for k in ("plan","delivery","qa","source"))
    if plan.get("sourceManifestSha256")!=hashes["source"]:
        raise ValueError("Source manifest hash mismatch")
    plan["_fileSha256"]=hashes["plan"]
    delivery["_fileSha256"]=hashes["delivery"]
    qa["_fileSha256"]=hashes["qa"]
    if not is_storyboard(plan):
        raise ValueError("Owner review bundle supports storyboard route only")
    validate_plan(plan,source)
    validate_delivery(plan,delivery,qa,**({"probe":probe} if probe else {}))
    root=Path(review_root).resolve(strict=True)
    slug=plan["leadSlug"]
    target=root/slug
    if target.exists():
        raise ValueError("Active owner review already exists; archive it explicitly")
    with tempfile.TemporaryDirectory(dir=root,prefix=".review-") as tmp:
        stage=Path(tmp)/slug
        stage.mkdir()
        media={}
        def copy_ref(name,ref,allowed):
            original=Path(ref["path"]).resolve(strict=True)
            ext=original.suffix.lower()
            if ext not in allowed or original.stat().st_size>MEDIA_LIMIT:
                raise ValueError("Unsupported or oversized review media")
            dest=stage/(name+ext)
            shutil.copyfile(original,dest)
            if sha_file(dest)!=ref["sha256"]:
                raise ValueError("Review media hash mismatch")
            media[name]={"file":dest.name,"sha256":ref["sha256"]}
        for name in ("desktop","mobile"):
            copy_ref(name+"_video",delivery["videos"][name],{".mp4",".webm"})
            copy_ref(name+"_storyboard",delivery["storyboards"][name],{".png",".jpg",".jpeg",".webp"})
            copy_ref(name+"_qa",qa["variants"][name]["browserVideoScreenshot"],{".png"})
            copy_ref(name+"_poster",delivery["frames"][delivery["videos"][name]["posterFrame"]],{".png",".jpg",".jpeg",".webp"})
        for i,ref in enumerate(plan["subject"]["sourceReferences"]):
            if i>=12: raise ValueError("Too many review source images")
            copy_ref("source_"+str(i),ref,{".png",".jpg",".jpeg",".webp"})
        manifest={"schemaVersion":1,"leadSlug":slug,"planSha256":hashes["plan"],
                  "deliverySha256":hashes["delivery"],"qaSha256":hashes["qa"],
                  "sourceManifestSha256":hashes["source"],"generatorId":delivery["generatorId"],
                  "media":media}
        # Recheck manifest inputs after media preparation.
        if any(sha_file(paths[k])!=v for k,v in hashes.items()):
            raise ValueError("Review input changed during preparation")
        (stage/"review.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
        stage.rename(target)
    return {"directory":str(target),"reviewBundleSha256":sha_file(target/"review.json"),
            "approval":False,"publicReleaseAuthorized":False}

if __name__=="__main__":
    import argparse
    parser=argparse.ArgumentParser(description="Trusted administrator: prepare a private owner review bundle without signing it.")
    for name in ("plan","delivery","qa","source","review-root"):
        parser.add_argument("--"+name,required=True,type=Path)
    args=parser.parse_args()
    print(json.dumps(prepare_review_bundle(args.plan,args.delivery,args.qa,args.source,args.review_root),indent=2))
