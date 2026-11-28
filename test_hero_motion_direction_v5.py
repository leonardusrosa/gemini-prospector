import unittest
import test_hero_motion_direction_v4 as v4
from test_hero_motion_direction_v3 import variant
from hero_motion_direction import compile_video_prompt, validate_direction
import test_hero_motion as fixtures

def upgrade(v):
    v["motionDirection"]["version"]=5
    v["motionDirection"]["attention_direction"]={
       "technique":"speed-ramped orbit",
       "opening_hook":"Sweep toward the crust immediately.",
       "signature_event":"Reveal the crust with strong parallax.",
       "rhythm":"Accelerate briefly, then decelerate into a slow reveal.",
       "niche_fit":"Reveal appetizing crust texture without obscuring the CTA."}
    # Keep the execution prompt compact.
    d=v["motionDirection"]
    d["temporal_sequence"]=[
       {"start":0,"end":1,"phase":"motion","camera":"Accelerate downward.","action":"Keep the pizza fixed."},
       {"start":1,"end":7.5,"phase":"motion","camera":"Decelerate into a slow arc.","action":"Reveal the crust texture."},
       {"start":7.5,"end":8,"phase":"settle","camera":"Match the final view.","action":"Keep the board stationary."}]
    v["videoPrompt"]=compile_video_prompt(v)
    return v

class AttentionTests(unittest.TestCase):
    def test_creative_prompt(self):
        v=upgrade(v4.routed(variant()))
        validate_direction(v)
        self.assertIn("Signature event:",v["videoPrompt"])
        self.assertIn("Rhythm:",v["videoPrompt"])
    def test_missing_signature_event(self):
        v=upgrade(v4.routed(variant()))
        del v["motionDirection"]["attention_direction"]["signature_event"]
        with self.assertRaisesRegex(ValueError,"signature visual event"):
            compile_video_prompt(v)
    def test_routine_motion_rejected(self):
        v=upgrade(v4.routed(variant()))
        v["motionDirection"]["attention_direction"]["technique"]="steady orbit"
        with self.assertRaisesRegex(ValueError,"Routine camera motion"):
            compile_video_prompt(v)
    def test_legacy_unchanged(self):
        validate_direction(v4.routed(variant()))

class AttentionDeliveryTests(unittest.TestCase):
    def test_creative_qa_required(self):
        f=v4.FlowDeliveryTests()
        f.setUp()
        self.addCleanup(f.doCleanups)
        h=f.fixture
        for name,v in h.plan["variants"].items():
            upgrade(v)
            h.qa["variants"][name].update(openingHookVerified=True,
                signatureEventVerified=True,intentionalRhythmVerified=True,
                advertisingGradeMotionVerified=True)
        self.assertEqual(fixtures.hero.validate_delivery(h.plan,h.delivery,h.qa,probe=h.probe)["result"],"VIDEO_QA_READY_FOR_HUMAN_APPROVAL")
        for key in ("openingHookVerified","signatureEventVerified","intentionalRhythmVerified","advertisingGradeMotionVerified"):
            h.qa["variants"]["mobile"][key]=False
            with self.assertRaisesRegex(ValueError,"V5 creative QA"):
                fixtures.hero.validate_delivery(h.plan,h.delivery,h.qa,probe=h.probe)
            h.qa["variants"]["mobile"][key]=True
