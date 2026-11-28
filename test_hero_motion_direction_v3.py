import unittest
from test_hero_motion_direction_v2 import upgraded
from hero_motion_direction import compile_video_prompt

def variant():
    v=upgraded()["variants"]["mobile"]
    d=v["motionDirection"]
    d["version"]=3
    d["motion_payoff"]={"kind":"viewpoint_change","description":"Reveal the front crust from a lower camera angle."}
    return v

class SceneDirectionTests(unittest.TestCase):
    def test_default_human_free(self):
        self.assertIn("no people, hands, limbs",compile_video_prompt(variant()))
    def test_missing_payoff_rejected(self):
        v=variant()
        del v["motionDirection"]["motion_payoff"]
        with self.assertRaisesRegex(ValueError,"visual payoff"):
            compile_video_prompt(v)
    def test_scale_only_requires_rationale(self):
        v=variant()
        v["motionDirection"]["motion_payoff"]["kind"]="scale_only_fallback"
        with self.assertRaisesRegex(ValueError,"fallback rationale"):
            compile_video_prompt(v)
    def test_exception_requires_specific_reason_and_role(self):
        v=variant()
        d=v["motionDirection"]
        d["scene_population"]="human_exception"
        with self.assertRaisesRegex(ValueError,"specific justification"):
            compile_video_prompt(v)
        d["human_exception"]={"reason":"A clinician demonstrates the required instrument positioning.","role":"One clinician positions the instrument on a training model."}
        self.assertIn("Only this necessary human action",compile_video_prompt(v))
    def test_conflicting_exception_rejected(self):
        v=variant()
        v["motionDirection"]["human_exception"]={"reason":"Unnecessary human appearance"}
        with self.assertRaisesRegex(ValueError,"cannot include"):
            compile_video_prompt(v)
