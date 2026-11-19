import os
import sys
import subprocess
import unittest

sys.path.insert(0, os.path.abspath("python"))

from opengen.ai.providers import AIProviderFactory, OfflineDeterministicProvider
from opengen.creative import (
    FootageAuditor,
    AdDirectorAgent,
    SmartReframer,
    SoundDesigner,
    AdCriticAgent
)

class TestEngine5Pipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = os.path.abspath("out/test_scratch")
        os.makedirs(cls.test_dir, exist_ok=True)
        cls.test_video = os.path.join(cls.test_dir, "test_input_16x9.mp4")

        # Synthesize a short 3-second test video if not present
        if not os.path.exists(cls.test_video):
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "testsrc=duration=3:size=1280x720:rate=30",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                cls.test_video
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    def test_provider_factory_offline(self):
        provider = AIProviderFactory.get_provider("offline")
        self.assertIsInstance(provider, OfflineDeterministicProvider)
        self.assertEqual(provider.model_name, "offline-deterministic-v1")

    def test_footage_auditor(self):
        auditor = FootageAuditor(provider=OfflineDeterministicProvider())
        report = auditor.audit_footage(self.test_video)
        self.assertIsNotNone(report.video_summary)
        self.assertGreater(len(report.shots), 0)
        self.assertGreaterEqual(report.shots[0].hook_score, 1)
        self.assertLessEqual(report.shots[0].hook_score, 10)

    def test_ad_director_and_critic(self):
        director = AdDirectorAgent(provider=OfflineDeterministicProvider(), target_duration=16.7)
        plan = director.build_creative_ad_plan("Automate viral motion graphics with OpenGen Engine 5")
        
        self.assertEqual(plan.get("schemaVersion"), "1.1.0")
        self.assertEqual(plan.get("settings", {}).get("aspectRatio"), "9:16")
        self.assertLessEqual(plan.get("settings", {}).get("duration"), 30.0)

        critic = AdCriticAgent()
        audit = critic.audit_ad_timeline(plan)
        self.assertTrue(audit["passed"])
        self.assertEqual(audit["score"], 100)
        self.assertEqual(len(audit["violations"]), 0)

    def test_smart_reframer(self):
        reframer = SmartReframer(smoothing_factor=0.15)
        out_vertical = os.path.join(self.test_dir, "test_output_9x16.mp4")
        result = reframer.reframe_to_vertical(self.test_video, out_vertical, focal_override_x=0.5)
        self.assertTrue(os.path.exists(result))
        self.assertGreater(os.path.getsize(result), 1000)

    def test_sound_designer_mastering(self):
        designer = SoundDesigner(sfx_library_dir=os.path.join(self.test_dir, "sfx"))
        mastered_out = os.path.join(self.test_dir, "test_mastered_audio.mp4")

        # Synthesize a 3s voice and 3s music track
        vo_file = os.path.join(self.test_dir, "vo.mp3")
        bgm_file = os.path.join(self.test_dir, "bgm.mp3")
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=300:duration=3", vo_file],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=100:duration=3", bgm_file],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        sfx_cues = [
            {"sound": "sub_impact_heavy", "timestamp_sec": 0.0, "volume": 0.8},
            {"sound": "whoosh_slide", "timestamp_sec": 1.5, "volume": 0.7}
        ]

        out = designer.master_audio_track(self.test_video, vo_file, bgm_file, sfx_cues, mastered_out)
        self.assertTrue(os.path.exists(out))
        self.assertGreater(os.path.getsize(out), 1000)

if __name__ == "__main__":
    unittest.main()
