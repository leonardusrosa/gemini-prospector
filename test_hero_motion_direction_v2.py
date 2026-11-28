"""Motion-only Flow prompts: deterministic, offline regression tests."""
import copy
import unittest
from test_hero_motion import plan_fixture, hero, compile_video_prompt

def upgraded():
    p = plan_fixture()
    for v in p["variants"].values():
        d = v["motionDirection"]
        d["version"] = 2
        d["product_lock"] = "Keep the same crust, toppings and serving board."
        d["physical_continuity"] = d.pop("continuity")
        d["camera_choreography"] = "Track right steadily with unchanged focal length."
        d["temporal_sequence"] = d.pop("beats")
        d["end_state"] = "Arrive at the supplied final frame without a cut."
        v["videoPrompt"] = compile_video_prompt(v)
    return p

class DirectionV2Tests(unittest.TestCase):
    def test_v2_valid_for_both_viewports(self):
        p = upgraded()
        self.assertEqual(hero.validate_plan(p)["result"], "PLAN_VALID")
        for v in p["variants"].values():
            self.assertLessEqual(len(v["videoPrompt"].split()),180)
            for k in ("cameraSetup","startComposition","endComposition"):
                self.assertNotIn(v["motionDirection"][k], v["videoPrompt"])
            self.assertIn("Product lock:", v["videoPrompt"])
            self.assertIn("Physical continuity:", v["videoPrompt"])
            self.assertIn("End state:", v["videoPrompt"])

    def test_legacy_plan_unchanged(self):
        self.assertEqual(hero.validate_plan(plan_fixture())["result"], "PLAN_VALID")

    def test_required_structured_fields(self):
        for k in ("product_lock","physical_continuity","camera_choreography","temporal_sequence","end_state"):
            with self.subTest(field=k):
                v = upgraded()["variants"]["mobile"]
                del v["motionDirection"][k]
                with self.assertRaises(ValueError):
                    compile_video_prompt(v)

    def test_legacy_alias_rejected(self):
        v = upgraded()["variants"]["mobile"]
        v["motionDirection"]["beats"] = []
        with self.assertRaisesRegex(ValueError,"legacy aliases"):
            compile_video_prompt(v)

    def test_timing_gap_and_early_settle(self):
        v = upgraded()["variants"]["mobile"]
        v["motionDirection"]["temporal_sequence"][1]["start"] = 4
        with self.assertRaisesRegex(ValueError,"without gaps"):
            compile_video_prompt(v)
        v = upgraded()["variants"]["mobile"]
        v["motionDirection"]["temporal_sequence"][1]["phase"] = "settle"
        with self.assertRaisesRegex(ValueError,"final second"):
            compile_video_prompt(v)

    def test_prompt_budget_and_filler(self):
        v = upgraded()["variants"]["mobile"]
        v["motionDirection"]["product_lock"] = "Preserve the pizza. " * 100
        with self.assertRaisesRegex(ValueError,"180 words"):
            compile_video_prompt(v)
        v = upgraded()["variants"]["mobile"]
        v["motionDirection"]["camera_choreography"] = "A premium cinematic shot."
        with self.assertRaisesRegex(ValueError,"Generic prompt"):
            compile_video_prompt(v)

    def test_tampering_cannot_pass_plan_gate(self):
        p = upgraded()
        p["variants"]["mobile"]["videoPrompt"] += " Add flames."
        with self.assertRaisesRegex(ValueError,"compiled shot direction"):
            hero.validate_plan(p)

if __name__ == "__main__":
    unittest.main()
