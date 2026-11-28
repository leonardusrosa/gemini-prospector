import copy,shutil,subprocess,tempfile,unittest
from pathlib import Path
import test_hero_motion as fixtures
from hero_video_derivative import create_web_derivative,verify_web_derivative,digest

@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),"FFmpeg required")
class WebDerivativeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.source=self.root/"source.mp4"
        subprocess.run(["ffmpeg","-v","error","-y","-f","lavfi","-i","testsrc2=s=128x72:r=24:d=1","-f","lavfi","-i","sine=frequency=440:duration=1","-c:v","libx264","-c:a","aac","-pix_fmt","yuv420p",str(self.source)],check=True)
        self.record=create_web_derivative(self.source,self.root/"web.mp4")
    def test_reproducible_and_original_preserved(self):
        self.assertTrue(verify_web_derivative(self.record,self.record["original"],self.record["output"]))
        self.assertEqual(digest(self.source),self.record["original"]["sha256"])
        with self.assertRaisesRegex(ValueError,"new MP4 path"):
            create_web_derivative(self.source,self.root/"web.mp4")
    def test_wrong_original_and_unsupported_recipe(self):
        with self.assertRaisesRegex(ValueError,"bind original"):
            verify_web_derivative(self.record,{"sha256":"0"*64},self.record["output"])
        forged=copy.deepcopy(self.record);forged["recipe"]="arbitrary"
        with self.assertRaisesRegex(ValueError,"Unsupported"):
            verify_web_derivative(forged,self.record["original"],self.record["output"])
    def test_reject_alternate_valid_video_with_updated_hash(self):
        other=self.root/"other.mp4"
        subprocess.run(["ffmpeg","-v","error","-y","-f","lavfi","-i","color=c=red:s=128x72:r=24:d=1","-c:v","libx264","-pix_fmt","yuv420p",str(other)],check=True)
        forged=copy.deepcopy(self.record);forged["output"]={"path":str(other),"sha256":digest(other)}
        with self.assertRaisesRegex(ValueError,"do not reproduce"):
            verify_web_derivative(forged,self.record["original"],forged["output"])
