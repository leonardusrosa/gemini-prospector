import { createHash, createPrivateKey, sign, randomUUID } from "node:crypto";
import { readFile, realpath, lstat, open, link, unlink } from "node:fs/promises";
import path from "node:path";
import { z } from "zod";

const sha = z.string().regex(/^[a-f0-9]{64}$/);
const slugSchema = z.string().regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/);
const mediaKey = /^(?:(?:desktop|mobile)_(?:video|storyboard|qa|poster)|source_(?:[0-9]|1[01]))$/;
const manifestSchema = z.object({
  schemaVersion: z.literal(1), leadSlug: slugSchema,
  planSha256: sha, deliverySha256: sha, qaSha256: sha, sourceManifestSha256: sha,
  generatorId: z.string().min(1).max(160),
  media: z.record(z.string().regex(mediaKey), z.object({
    file: z.string().regex(/^[a-z0-9_]+[.](?:mp4|webm|png|jpg|jpeg|webp)$/), sha256: sha,
  }).strict()),
}).strict();
export const decisionSchema = z.object({
  reviewBundleSha256: sha, decision: z.enum(["APPROVED","REJECTED"]),
  confirmed: z.literal(true),
}).strict();
const digest = (bytes: Buffer) => createHash("sha256").update(bytes).digest("hex");
export function ownerReviewEnabled() {
  return process.env.ENGINE_C_HERO_REVIEW_ENABLED === "true" &&
    Boolean(process.env.ENGINE_C_HERO_REVIEW_ROOT && process.env.ENGINE_C_HERO_OWNER_ID &&
      process.env.ENGINE_C_HERO_OWNER_PRIVATE_KEY_FILE);
}
export function isReviewOwner(id: string) {
  return ownerReviewEnabled() && id === process.env.ENGINE_C_HERO_OWNER_ID;
}
async function boundedFile(dir: string, file: string, max: number) {
  const target = path.join(dir,file);
  const info = await lstat(target);
  if (!info.isFile() || info.isSymbolicLink() || info.size < 1 || info.size > max ||
      path.dirname(await realpath(target)) !== dir) throw new Error("Invalid review file");
  const bytes=await readFile(target);
  if (bytes.length !== info.size || bytes.length > max) throw new Error("Changed review file");
  return bytes;
}
export async function loadReview(slug: string) {
  if (!ownerReviewEnabled() || !slugSchema.safeParse(slug).success) throw new Error("Review unavailable");
  const root = await realpath(process.env.ENGINE_C_HERO_REVIEW_ROOT!);
  const candidate = path.join(root,slug);
  const stat = await lstat(candidate);
  if (!stat.isDirectory() || stat.isSymbolicLink()) throw new Error("Invalid review directory");
  const dir=await realpath(candidate);
  if (path.dirname(dir)!==root) throw new Error("Invalid review directory");
  const raw=await boundedFile(dir,"review.json",65536);
  const manifest=manifestSchema.parse(JSON.parse(raw.toString("utf8")));
  if (manifest.leadSlug!==slug) throw new Error("Review lead mismatch");
  for (const name of ["desktop","mobile"]) {
    for (const kind of ["video","storyboard","qa","poster"]) {
      if (!manifest.media[name+"_"+kind]) throw new Error("Incomplete review media");
    }
  }
  if (!manifest.media.source_0) throw new Error("Source evidence missing");
  for (const [id,ref] of Object.entries(manifest.media)) {
    if (!ref.file.startsWith(id+".")) throw new Error("Review media name mismatch");
    const ext=path.extname(ref.file);
    if (id.endsWith("_video") ? ![".mp4",".webm"].includes(ext) : ![".png",".jpg",".jpeg",".webp"].includes(ext))
      throw new Error("Wrong media format");
  }
  return {dir,manifest,hash:digest(raw)};
}
type Review = Awaited<ReturnType<typeof loadReview>>;
export async function readReviewMedia(review: Review, id: string) {
  if (!mediaKey.test(id)) throw new Error("Unknown review media");
  const ref=review.manifest.media[id];
  if (!ref) throw new Error("Unknown review media");
  const bytes=await boundedFile(review.dir,ref.file,32*1024*1024);
  if (digest(bytes)!==ref.sha256) throw new Error("Review asset hash mismatch");
  const mime: Record<string,string>={".mp4":"video/mp4",".webm":"video/webm",".png":"image/png",".jpg":"image/jpeg",".jpeg":"image/jpeg",".webp":"image/webp"};
  return {bytes,mime:mime[path.extname(ref.file)]};
}
export async function reviewStatus(review: Review) {
  try { await lstat(path.join(review.dir,"decision.json")); return "DECIDED"; }
  catch (e) { if ((e as NodeJS.ErrnoException).code==="ENOENT") return "PENDING"; throw e; }
}
export async function decideReview(review: Review, ownerId: string, body: z.infer<typeof decisionSchema>) {
  if (!isReviewOwner(ownerId) || ownerId===review.manifest.generatorId) throw new Error("Owner required");
  if (body.reviewBundleSha256!==review.hash || !body.confirmed) throw new Error("Stale review");
  if (await reviewStatus(review)!=="PENDING") throw new Error("Review already decided");
  for (const id of Object.keys(review.manifest.media)) await readReviewMedia(review,id);
  const current=await loadReview(review.manifest.leadSlug);
  if (current.hash!==review.hash || current.dir!==review.dir) throw new Error("Stale review");
  const m=review.manifest;
  const receipt={
    schemaVersion:2, channel:"authenticated_admin_review", actorType:"human", autoSelected:false,
    leadSlug:m.leadSlug, planSha256:m.planSha256, deliverySha256:m.deliverySha256, qaSha256:m.qaSha256,
    sourceManifestSha256:m.sourceManifestSha256, reviewBundleSha256:review.hash, approverId:ownerId,
    decision:body.decision, issuedAt:new Date().toISOString().replace(/[.]\d{3}Z$/,"Z"),
  };
  const key=createPrivateKey(await readFile(process.env.ENGINE_C_HERO_OWNER_PRIVATE_KEY_FILE!));
  if (key.asymmetricKeyType!=="ed25519") throw new Error("Invalid owner signing key");
  const payload=["engine-c-owner-review-v2",receipt.leadSlug,receipt.planSha256,receipt.deliverySha256,
    receipt.qaSha256,receipt.sourceManifestSha256,receipt.reviewBundleSha256,receipt.approverId,receipt.decision,receipt.issuedAt].join("|");
  const result={...receipt,signature:sign(null,Buffer.from(payload,"utf8"),key).toString("base64")};
  // Atomic no-overwrite decision: concurrent approval/rejection cannot replace each other.
  const temp=path.join(review.dir,".decision-"+randomUUID()+".tmp");
  const handle=await open(temp,"wx",0o600);
  try {
    await handle.writeFile(JSON.stringify(result,null,2),"utf8"); await handle.sync(); await handle.close();
    await link(temp,path.join(review.dir,"decision.json"));
  } finally { await handle.close().catch(()=>{}); await unlink(temp).catch(()=>{}); }
  return {decision:result.decision,reviewBundleSha256:review.hash};
}
