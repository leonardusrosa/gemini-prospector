import unittest
from test_hero_motion_direction_v3 import variant
import test_hero_motion as fixtures
from test_hero_motion import hero
from hero_motion_direction import compile_video_prompt, validate_direction

ROUTE = {"provider":"google-flow","mode":"reference_linked_pair",
         "endUsesStartReference":True,"standaloneFramesRequired":True}

def routed(v):
    v["motionDirection"]["version"] = 4
    v["frameRouting"] = ROUTE.copy()
    v["videoPrompt"] = compile_video_prompt(v)
    return v

class FlowPairTests(unittest.TestCase):
    def test_flow_route(self):
        validate_direction(routed(variant()))
    def test_reject_non_flow_provider_and_missing_reference(self):
        for change in ({"provider":"chatgpt"}, {"endUsesStartReference":False},
                       {"standaloneFramesRequired":False}):
            v = routed(variant())
            v["frameRouting"].update(change)
            with self.assertRaisesRegex(ValueError,"matched frames"):
                validate_direction(v)

class FlowDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.HeroMotionContractTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        f = self.fixture
        for name in ("desktop","mobile"):
            v = f.plan["variants"][name]
            v["motionDirection"] = variant()["motionDirection"]
            routed(v)
            for field in ("flowPairReferenceVerified","standaloneFramesVerified",
                          "meaningfulMotionPayoffVerified","scenePopulationVerified"):
                f.qa["variants"][name][field] = True
        f.delivery["creditLedger"] = []
        for step in ("desktop_start","desktop_end","mobile_start","mobile_end","desktop_video","mobile_video"):
            asset = f.videos[step.split("_")[0]] if step.endswith("_video") else f.frames[step]
            f.delivery["creditLedger"].append({"accountAlias":"flow-a","model":"fixture",
              "creditsSpent":1,"uiCostChecked":True,"step":step,"outcome":"downloaded",
              "artifact":{"sha256":asset["sha256"]}})
    def test_delivery_binds_all_downloads(self):
        f=self.fixture
        self.assertEqual(hero.validate_delivery(f.plan,f.delivery,f.qa,probe=f.probe)["result"],"VIDEO_QA_READY_FOR_HUMAN_APPROVAL")
    def test_wrong_frame_hash_rejected(self):
        f=self.fixture
        f.delivery["creditLedger"][0]["artifact"]["sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"ledger download"):
            hero.validate_delivery(f.plan,f.delivery,f.qa,probe=f.probe)
    def test_missing_pair_review_rejected(self):
        f=self.fixture
        del f.qa["variants"]["desktop"]["flowPairReferenceVerified"]
        with self.assertRaisesRegex(ValueError,"independent QA"):
            hero.validate_delivery(f.plan,f.delivery,f.qa,probe=f.probe)
