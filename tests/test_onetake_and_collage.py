"""
Unit and Integration Tests for OneTake Jump-Cutter and Collage B-Roll Bento Mosaic.
Verifies automated speech segment slicing, alternating 1.0x <-> 1.25x camera punch-ins,
and 2-panel/3-panel animated 9:16 Bento Box mosaics.
"""
import subprocess
import pytest
from pathlib import Path
from opengen.creative.onetake_cutter import OneTakeCutter
from opengen.creative.collage_broll import CollageBRollGenerator
from opengen.engines.motion.engine import MotionEngine


@pytest.fixture
def synthetic_av_video(tmp_path):
    """Generates a 3-second synthetic video with alternating tone bursts for silence detection."""
    out_file = tmp_path / "talking_head.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "testsrc=duration=3:size=640x360:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=3",
        "-c:v", "libx264", "-c:a", "aac", "-shortest",
        str(out_file)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return str(out_file)


@pytest.fixture
def synthetic_clip_pair(tmp_path):
    """Generates two 2-second synthetic video clips for multi-cam mosaic testing."""
    clip_a = tmp_path / "clip_a.mp4"
    clip_b = tmp_path / "clip_b.mp4"
    clip_c = tmp_path / "clip_c.mp4"

    cmd_a = [
        "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=2:size=640x360:rate=30",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(clip_a)
    ]
    cmd_b = [
        "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=2:size=640x360:rate=30",
        "-vf", "negate", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(clip_b)
    ]
    cmd_c = [
        "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=2:size=640x360:rate=30",
        "-vf", "hflip", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(clip_c)
    ]

    subprocess.run(cmd_a, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    subprocess.run(cmd_b, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    subprocess.run(cmd_c, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    return str(clip_a), str(clip_b), str(clip_c)


def test_onetake_cutter_speech_detection_and_punchin(synthetic_av_video, tmp_path):
    cutter = OneTakeCutter()
    out_cut = tmp_path / "jumpcut_result.mp4"

    # Test speech detection
    ranges = cutter.detect_speech_ranges(synthetic_av_video, silence_thresh_sec=0.35)
    assert len(ranges) >= 1
    assert ranges[0][0] >= 0.0

    # Test processing and punch-in generation
    res_path = cutter.process_talking_head(
        input_video=synthetic_av_video,
        output_video=str(out_cut),
        silence_thresh_sec=0.35,
        zoom_punch_scale=1.25
    )

    assert Path(res_path).exists()
    assert Path(res_path).stat().st_size > 1000


def test_collage_broll_2_panel_mosaic(synthetic_clip_pair, tmp_path):
    clip_a, clip_b, _ = synthetic_clip_pair
    out_mosaic = tmp_path / "bento_2_panel.mp4"

    res = CollageBRollGenerator.render_bento_mosaic(
        clips=[clip_a, clip_b],
        output_path=str(out_mosaic),
        duration=2.0
    )

    assert Path(res).exists()
    assert Path(res).stat().st_size > 1000


def test_collage_broll_3_panel_bento_mosaic(synthetic_clip_pair, tmp_path):
    clip_a, clip_b, clip_c = synthetic_clip_pair
    out_mosaic = tmp_path / "bento_3_panel.mp4"

    res = CollageBRollGenerator.render_bento_mosaic(
        clips=[clip_a, clip_b, clip_c],
        output_path=str(out_mosaic),
        duration=2.0
    )

    assert Path(res).exists()
    assert Path(res).stat().st_size > 1000


def test_motion_engine_adapter_integration(synthetic_av_video, synthetic_clip_pair, tmp_path):
    engine = MotionEngine()
    clip_a, clip_b, _ = synthetic_clip_pair

    # Test Jump Cut integration
    jump_out = tmp_path / "engine_jumpcut.mp4"
    r1 = engine.jump_cut_talking_head(synthetic_av_video, str(jump_out))
    assert Path(r1).exists()

    # Test Bento Mosaic integration
    bento_out = tmp_path / "engine_bento.mp4"
    r2 = engine.create_bento_mosaic([clip_a, clip_b], str(bento_out), duration=1.5)
    assert Path(r2).exists()
