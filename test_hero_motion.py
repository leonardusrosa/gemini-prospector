"""Deterministic unit tests for v3 Hero Motion approval and Flow budgets.

No real Flow requests, account logins, credit spending or videos generated.
"""
from __future__ import annotations
import copy,hashlib,hmac,json,sys,tempfile,unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/"prospector-de-sites"/"automation"))
import hero_motion as hero
from hero_motion_direction import compile_video_prompt
import site_review_rounds as rounds

SHA="a"*64
KEY="test-only-human-admin-signature-secret-000000001"

def zones(desktop=True):
    return {
        "title":    {"x":.05,"y":.20,"width":.40,"height":.19} if desktop else {"x":.08,"y":.17,"width":.84,"height":.14},
        "subtitle": {"x":.05,"y":.43,"width":.40,"height":.13} if desktop else {"x":.08,"y":.33,"width":.84,"height":.12},
        "cta":      {"x":.05,"y":.63,"width":.36,"height":.12} if desktop else {"x":.08,"y":.49,"width":.84,"height":.10},
        "subject":  {"x":.54,"y":.10,"width":.42,"height":.77} if desktop else {"x":.18,"y":.64,"width":.66,"height":.29},
    }

def plan_fixture():
    p={
        "schemaVersion":1,
        "leadSlug":"fictional-pizzeria-hero-qa",
        "sourceManifestSha256":SHA,
        "provider":"google-flow",
        "noOutbound":True,
        "selectedDesignDirectionSha256":SHA,
        "placement":"AFTER_DESIGN_BEFORE_IMPLEMENTATION",
        "appliesToAllNiches":True,
        "manualApprovalRequired":True,
        "publicReleaseAuthorized":False,
        "durationRangeSeconds":[5,10],
        "subject":{
            "sourceStrategy":"optional_lead_asset",
            "basedOnLeadPhoto":False,
            "creativeRationale":"An artistic cinematic pizza dust burst feels energetic while preserving real brand cues.",
            "brandConsistencyRules":["No invented products or unsupported factual claims","Tasteful reveal"],
        },
        "budget":{
            "tier":"standard","plannedFrames":4,"plannedVideos":2,
            "maxRetries":2,"maxGenerations":8,"creditsAreUIVerified":False,
        },
        "accountRouting":{
            "mode":"authenticated_desktop_profiles",
            "aliases":["flow-a","flow-b"],
            "noStoredPasswords":True,
            "checkCreditsAndCostsBeforeEachJob":True,
        },
        "variants":{},
    }
    for name,ratio in hero.VARIANTS.items():
        p["variants"][name]={
            "aspectRatio":ratio,"targetSeconds":8,
            "loopMode":"engine_choice","fullViewport":True,
            "firstAndLastFrameRequired":True,
            "independentMobileComposition":name=="mobile",
            "startFramePrompt":"Overhead view of sourdough pizza on dark stone. The subject sits away from headline and CTA.",
            "endFramePrompt":"Pizza and flour gently settle into a pleasing final composition with safe text space.",
            "videoPrompt":"placeholder",
            "motionReason":"The motion must feel premium, playful and brand grounded without sacrificing readability.",
            "safeZones":zones(desktop=name=="desktop"),
        }
        v=p["variants"][name]
        v["motionDirection"]={
            "version":1,"cameraSetup":"Three-quarter overhead view, fixed focal length.",
            "startComposition":"Pizza occupies the lower or right area of the frame.",
            "endComposition":"Pizza board is centered inside its designated subject area.",
            "continuity":"Preserve identical crust, toppings and board throughout.",
            "protectedTextArea":"The declared text boxes remain dark and empty.",
            "forbiddenEffects":"No flames, sparks, melting or additional toppings.",
            "beats":[
                {"start":0,"end":3,"phase":"motion","camera":"Track right by five centimeters.","action":"Board slides right into the lit area."},
                {"start":3,"end":7.5,"phase":"motion","camera":"Continue tracking at a decreasing speed.","action":"Board continues moving toward its final position."},
                {"start":7.5,"end":8,"phase":"settle","camera":"Stop on the supplied last frame.","action":"Board stops without additional movement."},
            ],
        }
        v["videoPrompt"]=compile_video_prompt(v)
    return p

class HeroMotionContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)
        self.research={"leadSlug":"fictional-pizzeria-hero-qa","noOutbound":True,"assets":[]}
        self.plan=plan_fixture()
        self.plan_path=self.folder/"plan.json"
        self.plan_path.write_text(json.dumps(self.plan))
        self.plan["_fileSha256"]=hero.sha_file(self.plan_path)
        self.frames={}
        for name in hero.FRAMES:
            file=self.folder/(name+".png")
            file.write_bytes(("synthetic PNG frame "+name).encode())
            self.frames[name]={"path":str(file),"sha256":hero.sha_file(file)}
        self.videos={}
        for name in hero.VARIANTS:
            file=self.folder/(name+".mp4")
            file.write_bytes(("synthetic video fixture for metadata probe "+name).encode())
            self.videos[name]={
                "path":str(file),"sha256":hero.sha_file(file),
                "ending":"seamless_loop" if name=="desktop" else "freeze_on_end",
                "posterFrame":name+"_end",
            }
        self.delivery={
            "schemaVersion":1,"leadSlug":self.research["leadSlug"],
            "planSha256":self.plan["_fileSha256"],
            "generatorId":"flow-generation-agent",
            "frames":self.frames,"videos":self.videos,
            "creditLedger":[{"accountAlias":"flow-a","model":"Omni Flash 1.2",
                             "creditsSpent":24,"uiCostChecked":True} for _ in range(6)],
        }
        self.delivery_path=self.folder/"delivery.json"
        self.delivery_path.write_text(json.dumps(self.delivery))
        self.delivery["_fileSha256"]=hero.sha_file(self.delivery_path)
        screenshot=self.folder/"qa.png"
        screenshot.write_bytes(b"synthetic screenshot fixture")
        self.qa={
            "schemaVersion":1,"planSha256":self.plan["_fileSha256"],
            "deliverySha256":self.delivery["_fileSha256"],
            "variants":{},
        }
        for name in hero.VARIANTS:
            self.qa["variants"][name]={
                "reviewer":"independent-browser-qa",
                **{k:True for k in hero.QA_FIELDS},
                "loopSeamAcceptable":True,"endFrameStable":True,
                "browserVideoScreenshot":{"path":str(screenshot),"sha256":hero.sha_file(screenshot)}
            }
        self.qa_path=self.folder/"qa.json"
        self.qa_path.write_text(json.dumps(self.qa))
        self.approval={
            "schemaVersion":1,"decision":"APPROVED","channel":"authenticated_admin_review",
            "autoSelected":False,"actorType":"human","approverId":"human-owner",
            "planSha256":self.plan["_fileSha256"],
            "deliverySha256":self.delivery["_fileSha256"],
        }
        self.approval["signature"]=hmac.new(KEY.encode(),hero._approval_payload(self.approval),hashlib.sha256).hexdigest()

    def probe(self,path):
        if "desktop" in path.name:
            return {"durationSeconds":8,"width":1280,"height":720}
        return {"durationSeconds":8,"width":720,"height":1280}

    def test_standard_budget_and_creative_plan_valid_for_every_niche(self):
        self.assertEqual(hero.validate_plan(self.plan,self.research)["result"],"PLAN_VALID")
        self.assertEqual(hero.validate_plan(self.plan)["framesPlanned"],4)

    def test_no_fixed_motion_effect_whitelist(self):
        v=self.plan["variants"]["desktop"]
        v["motionDirection"]["beats"][0]["action"]="A measured burst of flour crosses the foreground rightward."
        v["videoPrompt"]=compile_video_prompt(v)
        self.assertEqual(hero.validate_plan(self.plan)["result"],"PLAN_VALID")

    def test_generic_prompt_rejected(self):
        v=self.plan["variants"]["desktop"]
        v["startFramePrompt"]="Premium cinematic pizza composition with dark stone and orange lighting."
        with self.assertRaisesRegex(ValueError,"Generic prompt"):
            hero.validate_plan(self.plan)

    def test_early_settling_rejected(self):
        v=self.plan["variants"]["mobile"]
        v["motionDirection"]["beats"][1]["phase"]="settle"
        with self.assertRaisesRegex(ValueError,"final second"):
            compile_video_prompt(v)

    def test_timing_gap_rejected(self):
        v=self.plan["variants"]["desktop"]
        v["motionDirection"]["beats"][1]["start"]=4
        with self.assertRaisesRegex(ValueError,"without gaps"):
            compile_video_prompt(v)

    def test_prompt_cannot_disagree_with_direction(self):
        v=self.plan["variants"]["mobile"]
        v["videoPrompt"]+=" Add flames."
        with self.assertRaisesRegex(ValueError,"compiled shot direction"):
            hero.validate_plan(self.plan)

    def test_motion_qa_rejects_unplanned_effect_and_early_stop(self):
        for field in ("noUnplannedEffects","noPrematureMotionStop","directedMotionVerified"):
            self.qa["variants"]["desktop"][field]=False
            with self.assertRaisesRegex(ValueError,"QA failed"):
                hero.validate_delivery(self.plan,self.delivery,self.qa,probe=self.probe)
            self.qa["variants"]["desktop"][field]=True

    def test_mobile_may_not_be_cropped_desktop(self):
        self.plan["variants"]["mobile"]["independentMobileComposition"]=False
        with self.assertRaisesRegex(ValueError,"Mobile may not"):
            hero.validate_plan(self.plan)

    def test_text_and_subject_overlap_blocks(self):
        self.plan["variants"]["desktop"]["safeZones"]["subject"]=self.plan["variants"]["desktop"]["safeZones"]["title"]
        with self.assertRaisesRegex(ValueError,"overlaps"):
            hero.validate_plan(self.plan)

    def test_missing_human_approval_or_unknown_key_blocks(self):
        with self.assertRaisesRegex(ValueError,"key not configured"):
            hero.approve_with_human_receipt(self.plan,self.delivery,self.qa,self.approval,key="short",probe=self.probe)

    def test_human_signature_verified_against_exact_delivered_assets(self):
        result=hero.approve_with_human_receipt(self.plan,self.delivery,self.qa,self.approval,key=KEY,probe=self.probe)
        self.assertEqual(result["result"],"HERO_MOTION_MANUALLY_APPROVED")
        self.assertFalse(result["productionReleaseAuthorized"])

    def test_automated_approval_cannot_pass(self):
        self.approval["autoSelected"]=True
        with self.assertRaisesRegex(ValueError,"Automatic approval"):
            hero.approve_with_human_receipt(self.plan,self.delivery,self.qa,self.approval,key=KEY,probe=self.probe)

    def test_stale_signature_cannot_approve_changed_media(self):
        self.approval["signature"]="0"*64
        with self.assertRaisesRegex(ValueError,"forged"):
            hero.approve_with_human_receipt(self.plan,self.delivery,self.qa,self.approval,key=KEY,probe=self.probe)

    def test_rejects_changed_video_bytes(self):
        Path(self.videos["mobile"]["path"]).write_bytes(b"modified after generation")
        with self.assertRaisesRegex(ValueError,"changed"):
            hero.validate_delivery(self.plan,self.delivery,self.qa,probe=self.probe)

    def test_rejects_retries_over_two(self):
        self.delivery["creditLedger"].extend([self.delivery["creditLedger"][0]]*3)
        with self.assertRaisesRegex(ValueError,"at most two retries"):
            hero.validate_delivery(self.plan,self.delivery,self.qa,probe=self.probe)

    def test_rejects_incorrect_mobile_video_ratio(self):
        def bad_probe(path):
            return {"durationSeconds":8,"width":1280,"height":720}
        with self.assertRaisesRegex(ValueError,"9:16"):
            hero.validate_delivery(self.plan,self.delivery,self.qa,probe=bad_probe)

    def test_rejects_unapproved_loop_seam(self):
        self.qa["variants"]["desktop"]["loopSeamAcceptable"]=False
        with self.assertRaisesRegex(ValueError,"seam"):
            hero.validate_delivery(self.plan,self.delivery,self.qa,probe=self.probe)

    def test_rejects_unstable_freeze(self):
        self.qa["variants"]["mobile"]["endFrameStable"]=False
        with self.assertRaisesRegex(ValueError,"Freeze"):
            hero.validate_delivery(self.plan,self.delivery,self.qa,probe=self.probe)

    def test_video_probe_needed_for_actual_file_integrity(self):
        with self.assertRaisesRegex(ValueError,"ffprobe"):
            hero.validate_delivery(self.plan,self.delivery,self.qa)

    def test_source_photo_requires_verified_research_asset_hash(self):
        self.plan["subject"]["basedOnLeadPhoto"]=True
        self.plan["subject"]["assetProvenanceSha256"]="f"*64
        with self.assertRaisesRegex(ValueError,"not in immutable"):
            hero.validate_plan(self.plan,self.research)

    def test_controller_refuses_hero_without_human_receipt(self):
        manifest=self.folder/"research.json"
        manifest.write_text(json.dumps({
            "schemaVersion":1,"leadSlug":self.research["leadSlug"],
            "noOutbound":True,"country":"US","socialProfiles":[],"assets":[],
            "researchChecks":{"businessIdentityVerified":True,
                              "websiteClassificationVerified":True,
                              "socialProfileIdentityVerified":True,
                              "mediaRightsReviewed":True,
                              "factualSourceManifestComplete":True},
        }))
        run=rounds.new_run(manifest)
        self.assertEqual(run["schemaVersion"],3)
        self.assertEqual(rounds.STAGES[4],"HERO_MOTION_MANUAL_APPROVAL")
        run["currentStageIndex"]=rounds.STAGES.index("HERO_MOTION_MANUAL_APPROVAL")
        path=self.folder/"stage.json"
        path.write_text(json.dumps({
            "schemaVersion":1,"stage":"HERO_MOTION_MANUAL_APPROVAL",
            "sourceManifestSha256":run["sourceManifestSha256"],
        }))
        with self.assertRaisesRegex(ValueError,"Four stage files mandatory"):
            rounds.submit_artifact(run,"HERO_MOTION_MANUAL_APPROVAL",path,"flow-generator")
        self.assertEqual(rounds.current_stage(run),"HERO_MOTION_MANUAL_APPROVAL")
        self.assertFalse(run["productionReleaseAuthorized"])

if __name__=="__main__":
    unittest.main(verbosity=2)
