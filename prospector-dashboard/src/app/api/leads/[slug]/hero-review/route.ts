import { NextRequest, NextResponse } from "next/server";
import { getOperatorSession } from "@/lib/auth";
import { NO_STORE_HEADERS, validateMutationRequest } from "@/lib/http";
import { isReviewOwner,loadReview,readReviewMedia,reviewStatus,decideReview,decisionSchema } from "@/lib/hero-owner-review";
export const runtime="nodejs";
export const dynamic="force-dynamic";
const headers={...NO_STORE_HEADERS,"X-Content-Type-Options":"nosniff"};
const fail=(status:number,error:string)=>NextResponse.json({error},{status,headers});
type Context={params:Promise<{slug:string}>};
export async function GET(request:NextRequest,{params}:Context) {
  const session=await getOperatorSession();
  if (!session) return fail(401,"Unauthorized");
  if (!isReviewOwner(session.id)) return fail(403,"Owner review unavailable");
  try {
    const review=await loadReview((await params).slug);
    const id=request.nextUrl.searchParams.get("media");
    if (id) {
      if (request.nextUrl.searchParams.get("bundle")!==review.hash) return fail(409,"Review changed");
      const {bytes,mime}=await readReviewMedia(review,id);
      const range=request.headers.get("range");
      const common={...headers,"Content-Type":mime,"Accept-Ranges":"bytes"};
      if (range) {
        const match=/^bytes=(\d+)-(\d*)$/.exec(range);
        const start=match?Number(match[1]):-1;
        const end=match?Math.min(match[2]?Number(match[2]):bytes.length-1,bytes.length-1):-1;
        if (!Number.isSafeInteger(start)||!Number.isSafeInteger(end)||start<0||end<start||start>=bytes.length)
          return new NextResponse(null,{status:416,headers:{...common,"Content-Range":"bytes */"+bytes.length}});
        return new NextResponse(new Uint8Array(bytes.subarray(start,end+1)),{status:206,headers:{...common,"Content-Range":`bytes ${start}-${end}/${bytes.length}`,"Content-Length":String(end-start+1)}});
      }
      return new NextResponse(new Uint8Array(bytes),{headers:{...common,"Content-Length":String(bytes.length)}});
    }
    return NextResponse.json({hash:review.hash,leadSlug:review.manifest.leadSlug,deliverySha256:review.manifest.deliverySha256,
      qaSha256:review.manifest.qaSha256,media:Object.keys(review.manifest.media),status:await reviewStatus(review)},{headers});
  } catch { return fail(404,"No valid active review"); }
}
export async function POST(request:NextRequest,{params}:Context) {
  const session=await getOperatorSession();
  if (!session) return fail(401,"Unauthorized");
  if (!isReviewOwner(session.id)) return fail(403,"Owner review unavailable");
  if (validateMutationRequest(request)) return fail(403,"Invalid origin or content type");
  try {
    const raw=await request.text();
    if (raw.length>2048) return fail(400,"Invalid request");
    const body=decisionSchema.safeParse(JSON.parse(raw));
    if (!body.success) return fail(400,"Explicit confirmation required");
    const review=await loadReview((await params).slug);
    return NextResponse.json(await decideReview(review,session.id,body.data),{headers});
  } catch {return fail(409,"Decision not recorded; reload current review");}
}
