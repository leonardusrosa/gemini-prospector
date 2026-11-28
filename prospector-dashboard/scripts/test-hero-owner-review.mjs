import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, mkdir, writeFile, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { createHash, generateKeyPairSync, verify } from "node:crypto";
import { ownerReviewEnabled, isReviewOwner, loadReview, readReviewMedia, reviewStatus, decideReview, decisionSchema } from "../src/lib/hero-owner-review.ts";

test("owner-only exact candidate review with immutable decisions",async()=>{
  const root=await mkdtemp(path.join(tmpdir(),"hero-review-test-"));
  try {
    const dir=path.join(root,"fixture");await mkdir(dir);
    const {privateKey,publicKey}=generateKeyPairSync("ed25519");
    const privateFile=path.join(root,"fixture-private.pem");
    await writeFile(privateFile,privateKey.export({type:"pkcs8",format:"pem"}),{mode:0o600});
    process.env.ENGINE_C_HERO_REVIEW_ENABLED="false";
    process.env.ENGINE_C_HERO_REVIEW_ROOT=root;
    process.env.ENGINE_C_HERO_OWNER_ID="fixture-owner";
    process.env.ENGINE_C_HERO_OWNER_PRIVATE_KEY_FILE=privateFile;
    assert.equal(ownerReviewEnabled(),false);
    process.env.ENGINE_C_HERO_REVIEW_ENABLED="true";
    assert.equal(isReviewOwner("other"),false);
    assert.equal(isReviewOwner("fixture-owner"),true);
    const hash=b=>createHash("sha256").update(b).digest("hex");
    const media={};
    for(const id of ["desktop_video","mobile_video","desktop_storyboard","mobile_storyboard","desktop_qa","mobile_qa","desktop_poster","mobile_poster","source_0"]){
      const file=id+(id.endsWith("_video")?".mp4":".png");
      const bytes=Buffer.from("synthetic fixture "+id);
      await writeFile(path.join(dir,file),bytes);media[id]={file,sha256:hash(bytes)};
    }
    const manifest={schemaVersion:1,leadSlug:"fixture",planSha256:"a".repeat(64),deliverySha256:"b".repeat(64),qaSha256:"c".repeat(64),sourceManifestSha256:"d".repeat(64),generatorId:"worker",media};
    await writeFile(path.join(dir,"review.json"),JSON.stringify(manifest));
    await assert.rejects(loadReview("../fixture"));
    const review=await loadReview("fixture");
    assert.equal(await reviewStatus(review),"PENDING");
    assert.equal((await readReviewMedia(review,"desktop_video")).mime,"video/mp4");
    const body=decisionSchema.parse({reviewBundleSha256:review.hash,decision:"APPROVED",confirmed:true});
    assert.equal(decisionSchema.safeParse({...body,confirmed:false}).success,false);
    await assert.rejects(decideReview(review,"other",body));
    await assert.rejects(decideReview(review,"fixture-owner",{...body,reviewBundleSha256:"0".repeat(64)}));
    const target=path.join(dir,media.desktop_video.file);const original=await readFile(target);
    await writeFile(target,"changed");
    await assert.rejects(decideReview(review,"fixture-owner",body));
    await writeFile(target,original);
    const competing=await Promise.allSettled([decideReview(review,"fixture-owner",body),decideReview(review,"fixture-owner",body)]);
    assert.equal(competing.filter(r=>r.status==="fulfilled").length,1);
    assert.equal(await reviewStatus(review),"DECIDED");
    const r=JSON.parse(await readFile(path.join(dir,"decision.json"),"utf8"));
    const payload=["engine-c-owner-review-v2",r.leadSlug,r.planSha256,r.deliverySha256,r.qaSha256,r.sourceManifestSha256,r.reviewBundleSha256,r.approverId,r.decision,r.issuedAt].join("|");
    assert.equal(verify(null,Buffer.from(payload),publicKey,Buffer.from(r.signature,"base64")),true);
    await assert.rejects(decideReview(review,"fixture-owner",{...body,decision:"REJECTED"}));
  } finally {
    delete process.env.ENGINE_C_HERO_REVIEW_ENABLED;delete process.env.ENGINE_C_HERO_REVIEW_ROOT;
    delete process.env.ENGINE_C_HERO_OWNER_ID;delete process.env.ENGINE_C_HERO_OWNER_PRIVATE_KEY_FILE;
    await rm(root,{recursive:true,force:true});
  }
});
