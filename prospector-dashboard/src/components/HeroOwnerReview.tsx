"use client";
import { useEffect,useState } from "react";
type Review={hash:string;leadSlug:string;deliverySha256:string;qaSha256:string;media:string[];status:string};
export default function HeroOwnerReview({slug}:{slug:string}) {
  const endpoint="/api/leads/"+encodeURIComponent(slug)+"/hero-review";
  const [review,setReview]=useState<Review|null>(null);
  const [message,setMessage]=useState("Loading review...");
  const [confirmed,setConfirmed]=useState(false);
  const [busy,setBusy]=useState(false);
  useEffect(()=>{let active=true;fetch(endpoint,{cache:"no-store"}).then(async r=>{if(!r.ok)throw Error();const data=await r.json();if(active){setReview(data);setMessage("");}}).catch(()=>{if(active)setMessage("No active validated review.");});return()=>{active=false;};},[endpoint]);
  if(!review)return <section className="card"><h2>Hero review</h2><p>{message}</p></section>;
  const media=(id:string)=>endpoint+"?media="+encodeURIComponent(id)+"&bundle="+review.hash;
  async function decide(decision:"APPROVED"|"REJECTED") {
    if(!review||!confirmed||busy)return;
    setBusy(true);
    try{
      const response=await fetch(endpoint,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({reviewBundleSha256:review.hash,confirmed:true,decision})});
      if(!response.ok)throw Error();
      setMessage(decision==="APPROVED"?"Owner decision recorded. Site publication is not authorized.":"Candidate rejected.");
      setReview({...review,status:"DECIDED"});setConfirmed(false);
    }catch{setMessage("Decision was not recorded. Reload the current review.");}finally{setBusy(false);}
  }
  return <section className="card stack">
    <h2 className="section-title">Hero video owner review</h2>
    <p>Review the exact final media, storyboard and source references. Approval does not publish a website.</p>
    <p className="subtle" style={{overflowWrap:"anywhere"}}>Candidate: {review.hash}</p>
    {["desktop","mobile"].map(name=><div key={name} className="stack"><h3>{name}</h3>
      <video controls playsInline muted preload="metadata" poster={media(name+"_poster")} src={media(name+"_video")} style={{width:"100%",maxWidth:name==="mobile"?360:800}}/>
      <details><summary>Storyboard and QA capture</summary><img src={media(name+"_storyboard")} alt={name+" storyboard"} style={{maxWidth:"100%"}}/><img src={media(name+"_qa")} alt={name+" QA capture"} style={{maxWidth:"100%"}}/></details>
    </div>)}
    <details><summary>Business source references</summary>{review.media.filter(x=>x.startsWith("source_")).map(id=><img key={id} src={media(id)} alt="Business source reference" style={{maxWidth:320,width:"100%"}}/>)}</details>
    {review.status==="PENDING"?<><label><input type="checkbox" checked={confirmed} onChange={e=>setConfirmed(e.target.checked)}/> I have reviewed this exact candidate, including both final videos and product accuracy, and want to record my decision.</label><div className="actions"><button className="button" disabled={!confirmed||busy} onClick={()=>decide("APPROVED")}>Approve exact candidate</button><button className="button" disabled={!confirmed||busy} onClick={()=>decide("REJECTED")}>Reject candidate</button></div></>:<p>Decision already recorded.</p>}
    <p role="status">{message}</p>
  </section>;
}
