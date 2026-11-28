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
