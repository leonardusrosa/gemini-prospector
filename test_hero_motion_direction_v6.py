import unittest
import test_hero_motion_direction_v5 as v5
import test_hero_motion_direction_v4 as v4
from test_hero_motion_direction_v3 import variant
from hero_motion_direction import compile_video_prompt, validate_direction
import test_hero_motion as fixtures

def upgrade(v):
    d=v["motionDirection"]
    d["version"]=6
    d["intensity_direction"]={
       "event_kind":"substantial_assembly",
       "initial_state":"Rectangular base with tomato sauce.",
       "intermediate_event":"Mozzarella and pepperoni arrive in ordered layers.",
       "final_state":"Finished pizza with a visibly complete topping layer.",
       "assembly_equivalent_rationale":"The main ingredients visibly build the entire dish."}
    v["videoPrompt"]=compile_video_prompt(v)
    return v

class IntensityTests(unittest.TestCase):
    def test_v6_valid_and_legacy_unchanged(self):
        v=v5.upgrade(v4.routed(variant()))
        before=v["videoPrompt"]
        validate_direction(v)
        self.assertEqual(compile_video_prompt(v),before)
        validate_direction(upgrade(v))
    def test_missing_intensity_rejected(self):
        v=upgrade(v5.upgrade(v4.routed(variant())))
        del v["motionDirection"]["intensity_direction"]
        with self.assertRaisesRegex(ValueError,"assembly-equivalent"):
            compile_video_prompt(v)
    def test_decorative_event_rejected(self):
        v=upgrade(v5.upgrade(v4.routed(variant())))
        v["motionDirection"]["intensity_direction"]["event_kind"]="seasoning_only"
        with self.assertRaisesRegex(ValueError,"decorative motion"):
            compile_video_prompt(v)
    def test_missing_state_rejected(self):
        v=upgrade(v5.upgrade(v4.routed(variant())))
        del v["motionDirection"]["intensity_direction"]["intermediate_event"]
        with self.assertRaisesRegex(ValueError,"intermediate_event"):
            compile_video_prompt(v)
    def test_intensity_review_required(self):
        f=v4.FlowDeliveryTests()
        f.setUp()
        self.addCleanup(f.doCleanups)
        h=f.fixture
        for name,v in h.plan["variants"].items():
            upgrade(v5.upgrade(v))
            h.qa["variants"][name].update(openingHookVerified=True,
                signatureEventVerified=True,intentionalRhythmVerified=True,
                advertisingGradeMotionVerified=True,
                assemblyEquivalentIntensityVerified=True,
                substantiveVisualProgressionVerified=True)
        self.assertEqual(fixtures.hero.validate_delivery(h.plan,h.delivery,h.qa,probe=h.probe)["result"],"VIDEO_QA_READY_FOR_HUMAN_APPROVAL")
        for key in ("assemblyEquivalentIntensityVerified","substantiveVisualProgressionVerified"):
            h.qa["variants"]["mobile"][key]=False
            with self.assertRaisesRegex(ValueError,"V6 intensity QA"):
                fixtures.hero.validate_delivery(h.plan,h.delivery,h.qa,probe=h.probe)
            h.qa["variants"]["mobile"][key]=True
