import copy,json,shutil,subprocess,tempfile,unittest
from pathlib import Path
import test_hero_motion as fixtures
import test_hero_motion_direction_v4 as v4
import test_hero_motion_direction_v5 as v5
import test_hero_motion_direction_v6 as v6
from test_hero_motion_direction_v3 import variant
import flow_execution_ledger as flow
from hero_motion import validate_plan,validate_delivery,sha_file
from hero_motion_direction import compile_video_prompt
from hero_storyboard import extract_video_frames,verify_video_frames

class StoryboardTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.ref=self.file("source.jpg",b"source fixture")
        self.evidence=self.file("evidence.png",b"synthetic evidence")
        self.plan=fixtures.plan_fixture()
        self.plan["subject"]["sourceReferences"]=[self.ref]
        self.plan["budget"].update(plannedFrames=0,plannedStoryboards=2,maxGenerations=6)
        for name,v in self.plan["variants"].items():
            v["motionDirection"]=variant()["motionDirection"]
            v6.upgrade(v5.upgrade(v4.routed(v)))
            v["motionDirection"]["version"]=7
            v["motionDirection"]["motivated_transition"]="Reveal through a controlled foreground wipe."
            v["motionDirection"]["attention_direction"]["opening_hook"]="Accelerate toward the sauce."
            v["motionDirection"]["attention_direction"]["signature_event"]="Cheese and pepperoni assemble."
            v["motionDirection"]["attention_direction"]["rhythm"]="Accelerate, then slow the reveal."
            v["motionDirection"]["product_lock"]="Preserve the rectangular pizza and board."
            v["motionDirection"]["physical_continuity"]="Ingredients settle naturally under gravity."
            v["motionDirection"]["camera_choreography"]="Stabilized camera arcs toward the pizza."
            v["motionDirection"]["temporal_sequence"][0]["action"]="Cheese lands on the sauce."
            v["motionDirection"]["temporal_sequence"][1]["action"]="Pepperoni lands on the cheese."
            v["frameRouting"]={"provider":"google-flow","mode":"storyboard_ingredient","panelCount":4,"fullScreenOutput":True}
            v["firstAndLastFrameRequired"]=False
            v["storyboardPrompt"]="Four ordered panels show the sauce, cheese, pepperoni and finished pizza."
            v["storyboardPanels"]=["Sauced dough lies on the same board.","Cheese descends onto the sauce.","Pepperoni settles over the cheese.","Baked pizza resolves on the same board."]
            v["videoPrompt"]=compile_video_prompt(v)
        self.plan["_fileSha256"]=fixtures.SHA
        self.job=flow.new_job(self.plan,fixtures.SHA,cap=60,reconciliation_evidence=self.evidence["path"])
    def file(self,name,data):
        p=self.root/name;p.write_bytes(data)
        return {"path":str(p.resolve()),"sha256":sha_file(p)}
    def reserve(self,step,refs=None,**kwargs):
        if refs is None:
            refs=[self.ref["sha256"]] if step.endswith("storyboard") else [next(e["artifact"]["sha256"] for e in reversed(self.job["entries"]) if e["step"]==step.replace("video","storyboard"))]
        return flow.reserve(self.job,step,"flow-a","fixture",100,10,self.evidence["path"],reference_evidence=self.evidence["path"],reference_hashes=refs,**kwargs)
    def finish(self,step,artifact=None,failed=False):
        a=artifact or self.file(step+str(len(self.job["entries"]))+(".mp4" if step.endswith("video") else ".jpg"),step.encode())
        return flow.reconcile(self.job,"flow-a",90,self.evidence["path"],outcome="failed" if failed else "downloaded",artifact=None if failed else a["path"])
    def test_budget_and_source(self):
        self.assertEqual(validate_plan(self.plan)["storyboardsPlanned"],2)
        research={"leadSlug":self.plan["leadSlug"],"noOutbound":True,"assets":[]}
        with self.assertRaisesRegex(ValueError,"immutable research"):
            validate_plan(self.plan,research)
        research["assets"]=[self.ref]
        validate_plan(self.plan,research)
        with self.assertRaisesRegex(ValueError,"reconciliation"):
            flow.new_job(self.plan,fixtures.SHA)
    def test_wrong_ref_and_pending(self):
        with self.assertRaisesRegex(ValueError,"Reference hashes"):
            self.reserve("desktop_storyboard",["0"*64])
        self.reserve("desktop_storyboard")
        with self.assertRaisesRegex(ValueError,"Reconcile"):
            self.reserve("mobile_storyboard")
    def test_dependency_and_retry(self):
        self.reserve("desktop_storyboard");self.finish("desktop_storyboard",failed=True)
        self.reserve("mobile_storyboard");self.finish("mobile_storyboard")
        with self.assertRaisesRegex(ValueError,"reference downloads"):
            self.reserve("desktop_video",["0"*64])
        self.reserve("desktop_storyboard",retry=True);self.finish("desktop_storyboard")
        self.reserve("desktop_video");self.finish("desktop_video")
        with self.assertRaisesRegex(ValueError,"new job"):
            self.reserve("desktop_storyboard",retry=True)
        self.reserve("mobile_video");self.finish("mobile_video")
        result=flow.delivery_inputs(self.job)
        self.assertEqual(len(result["creditLedger"]),5)
        self.assertEqual(result["creditsSpent"],50)
    def test_replay_and_tamper(self):
        for step in flow.STORYBOARD_STEPS:
            self.reserve(step);self.finish(step)
        d=flow.delivery_inputs(self.job);d["planSha256"]=fixtures.SHA
        flow.verify_storyboard_delivery(self.plan,d)
        d=copy.deepcopy(d);d["creditLedger"][2]["referenceHashes"]=["0"*64]
        with self.assertRaisesRegex(ValueError,"Reference hashes"):
            flow.verify_storyboard_delivery(self.plan,d)
    @unittest.skipUnless(shutil.which("ffmpeg"),"ffmpeg required for actual endpoint extraction")
    def test_full_delivery_and_poster_proof(self):
        f=fixtures.HeroMotionContractTests();f.setUp();self.addCleanup(f.doCleanups)
        d=f.delivery;d["planSha256"]=fixtures.SHA
        f.qa["planSha256"]=fixtures.SHA
        frames={}
        for step in flow.STORYBOARD_STEPS:
            self.reserve(step)
            if step.endswith("video"):
                name=step.split("_")[0]
                path=self.root/(step+".mp4")
                # Deterministic synthetic clip, not provider generation.
                color="red" if name=="mobile" else "blue"
                subprocess.run(["ffmpeg","-v","error","-y","-f","lavfi","-i",f"color=c={color}:s=64x64:r=2:d=1","-c:v","libx264","-pix_fmt","yuv420p",str(path)],check=True)
                art={"path":str(path),"sha256":sha_file(path)}
                frames.update(extract_video_frames(path,self.root/name,name))
                self.finish(step,art)
            else:self.finish(step)
        result=flow.delivery_inputs(self.job)
        d.update(result);d["frames"]=frames
        for name in ("desktop","mobile"):
            d["videos"][name].update(ending="freeze_on_end",posterFrame=name+"_end")
            f.qa["variants"][name].update(**{k:True for k in ("storyboardReferenceVerified","storyboardSequenceVerified","sourceProductIdentityVerified","motivatedTransitionVerified","noGridArtifacts","meaningfulMotionPayoffVerified","scenePopulationVerified","openingHookVerified","signatureEventVerified","intentionalRhythmVerified","advertisingGradeMotionVerified","assemblyEquivalentIntensityVerified","substantiveVisualProgressionVerified")})
        self.assertEqual(validate_delivery(self.plan,d,f.qa,probe=f.probe)["result"],"VIDEO_QA_READY_FOR_HUMAN_APPROVAL")
        f.qa["variants"]["mobile"]["sourceProductIdentityVerified"]=False
        with self.assertRaisesRegex(ValueError,"V7 storyboard QA"):
            validate_delivery(self.plan,d,f.qa,probe=f.probe)
        with self.assertRaisesRegex(ValueError,"exact delivered video"):
            verify_video_frames(d["videos"]["mobile"],frames["desktop_start"],frames["mobile_end"])

        # The approved web video may be a proven derivative, not arbitrary bytes.
        from hero_video_derivative import create_web_derivative
        original=d["videos"]["mobile"]["path"]
        derivative=create_web_derivative(original,self.root/"mobile-web.mp4")
        d["videoDerivations"]={"mobile":derivative}
        d["videos"]["mobile"].update(derivative["output"])
        d["frames"].update(extract_video_frames(derivative["output"]["path"],self.root/"mobile-web","mobile"))
        f.qa["variants"]["mobile"]["sourceProductIdentityVerified"]=True
        with self.assertRaisesRegex(ValueError,"optimized video playback"):
            validate_delivery(self.plan,d,f.qa,probe=f.probe)
        f.qa["variants"]["mobile"]["optimizedPlaybackVerified"]=True
        self.assertEqual(validate_delivery(self.plan,d,f.qa,probe=f.probe)["result"],"VIDEO_QA_READY_FOR_HUMAN_APPROVAL")
        forged=copy.deepcopy(d)
        forged["videoDerivations"]["mobile"]["ffmpegSha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"FFmpeg build"):
            flow.verify_storyboard_delivery(self.plan,forged)

        from hero_owner_review import prepare_review_bundle,receipt_payload
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
        from unittest.mock import patch
        from datetime import datetime,timezone
        import base64
        source_path=self.root/"research.json"
        source_path.write_text(json.dumps({"leadSlug":self.plan["leadSlug"],"noOutbound":True,"assets":[self.ref]}))
        self.plan["sourceManifestSha256"]=sha_file(source_path)
        plan_path=self.root/"plan.json";plan_path.write_text(json.dumps(self.plan))
        d["planSha256"]=sha_file(plan_path)
        delivery_path=self.root/"delivery.json";delivery_path.write_text(json.dumps(d))
        f.qa["planSha256"]=sha_file(plan_path);f.qa["deliverySha256"]=sha_file(delivery_path)
        qa_path=self.root/"qa.json";qa_path.write_text(json.dumps(f.qa))
        review_root=self.root/"reviews";review_root.mkdir()
        bundle=prepare_review_bundle(plan_path,delivery_path,qa_path,source_path,review_root,probe=f.probe)
        self.assertFalse(bundle["approval"])
        manifest=json.loads((Path(bundle["directory"])/"review.json").read_text())
        self.assertEqual(len(manifest["media"]),9)
        self.assertEqual(manifest["media"]["mobile_video"]["sha256"],d["videos"]["mobile"]["sha256"])
        with self.assertRaisesRegex(ValueError,"already exists"):
            prepare_review_bundle(plan_path,delivery_path,qa_path,source_path,review_root,probe=f.probe)
        key=Ed25519PrivateKey.generate()
        public=self.root/"owner-public.pem"
        public.write_bytes(key.public_key().public_bytes(Encoding.PEM,PublicFormat.SubjectPublicKeyInfo))
        receipt={"schemaVersion":2,"channel":"authenticated_admin_review","actorType":"human",
                 "autoSelected":False,"decision":"APPROVED","approverId":"test-owner",
                 "issuedAt":datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "reviewBundleSha256":bundle["reviewBundleSha256"],
                 **{k:manifest[k] for k in ("leadSlug","planSha256","deliverySha256","qaSha256","sourceManifestSha256")}}
        receipt["signature"]=base64.b64encode(key.sign(receipt_payload(receipt))).decode()
        # In-memory review fixtures bind exact file hashes, not the original fixture hash.
        self.plan["_fileSha256"]=sha_file(plan_path)
        d["_fileSha256"]=sha_file(delivery_path)
        f.qa["_fileSha256"]=sha_file(qa_path)
        with patch.dict("os.environ",{"ENGINE_C_HERO_OWNER_ID":"test-owner","ENGINE_C_HERO_OWNER_PUBLIC_KEY_FILE":str(public)}):
            self.assertEqual(fixtures.hero.approve_with_human_receipt(self.plan,d,f.qa,receipt,probe=f.probe)["result"],"HERO_MOTION_MANUALLY_APPROVED")
