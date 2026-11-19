import asyncio
import json
import os
import subprocess
import wave
import edge_tts
import numpy as np

PROJECT_DIR = r"f:\motion graphics\motion studio\projects\cng-explainer"
AUDIO_DIR = os.path.join(PROJECT_DIR, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

SCENES = [
    {
        "id": "scene1",
        "title": "Intro & Overview",
        "text": (
            "Hello everyone. I am Dr. Chander Amgoth Pawar, Chemistry Faculty at V N R, V J I E T. "
            "Today, we will explore Compressed Natural Gas, or CNG — its composition, properties, and applications."
        ),
    },
    {
        "id": "scene2",
        "title": "Compression & Context",
        "text": (
            "Natural gas is an abundant fuel, yet at atmospheric pressure it occupies huge volume. "
            "Compressing purified gas to two hundred to two hundred fifty bar shrinks it below one percent volume for practical transport."
        ),
    },
    {
        "id": "scene3",
        "title": "Chemical Composition",
        "text": (
            "In composition, CNG is predominantly methane, CH4, accounting for eighty-five to ninety-five percent by volume. "
            "It also contains small amounts of ethane, propane, and trace nitrogen and carbon dioxide."
        ),
    },
    {
        "id": "scene4",
        "title": "Physical & Combustion Properties",
        "text": (
            "CNG is colorless, non-toxic, and naturally odorless, so trace mercaptan is added for leak detection. "
            "With a high octane rating near one hundred twenty to one hundred thirty, it burns smoothly and cleanly."
        ),
    },
    {
        "id": "scene5",
        "title": "Emissions & Density Comparison",
        "text": (
            "Compared to petrol and diesel, CNG cuts carbon monoxide and particulate emissions dramatically. "
            "Because methane is lighter than air with specific gravity near zero point five five, leaks disperse rapidly upward."
        ),
    },
    {
        "id": "scene6",
        "title": "Safety & Flammability Limits",
        "text": (
            "CNG has a narrow flammability range of just five to fifteen percent in air, "
            "and a high auto-ignition temperature near five hundred forty degrees Celsius. "
            "Reinforced cylinders and pressure relief valves minimize explosion hazards."
        ),
    },
    {
        "id": "scene7",
        "title": "Applications & Future",
        "text": (
            "Today, CNG powers buses, auto-rickshaws, and passenger cars worldwide. "
            "Beyond clean transport, it fuels industrial boilers and turbines, supplies city gas networks, "
            "and expands sustainably through renewable Bio-CNG."
        ),
    },
]


async def synth_all():
    for sc in SCENES:
        out_mp3 = os.path.join(AUDIO_DIR, f"{sc['id']}.mp3")
        comm = edge_tts.Communicate(
            sc["text"],
            "en-IN-PrabhatNeural",
            rate="+10%",
            pitch="+15Hz",
        )
        await comm.save(out_mp3)
        out_wav = os.path.join(AUDIO_DIR, f"{sc['id']}.wav")
        subprocess.run(
            ["ffmpeg", "-y", "-i", out_mp3, "-ar", "48000", "-ac", "2", out_wav],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


def wav_duration(path: str) -> float:
    with wave.open(path, "rb") as w:
        return w.getnframes() / float(w.getframerate())


def build_timeline_and_mix():
    sr = 48000
    lead_in = 0.40
    tail_pad = 0.65

    timeline = []
    cursor = 0.0
    voice_chunks = []

    for sc in SCENES:
        wpath = os.path.join(AUDIO_DIR, f"{sc['id']}.wav")
        dur = wav_duration(wpath)
        scene_dur = round(lead_in + dur + tail_pad, 2)
        start_t = round(cursor, 2)
        end_t = round(start_t + scene_dur, 2)
        timeline.append(
            {
                "id": sc["id"],
                "title": sc["title"],
                "start": start_t,
                "end": end_t,
                "duration": scene_dur,
                "speech_start": round(start_t + lead_in, 2),
                "speech_end": round(start_t + lead_in + dur, 2),
                "speech_duration": round(dur, 3),
                "text": sc["text"],
            }
        )
        with wave.open(wpath, "rb") as w:
            pcm = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
            pcm = pcm.reshape(-1, 2)
        pad_pre = np.zeros((int(round(lead_in * sr)), 2), dtype=np.float32)
        target_samples = int(round(scene_dur * sr))
        pad_post_len = max(0, target_samples - len(pad_pre) - len(pcm))
        pad_post = np.zeros((pad_post_len, 2), dtype=np.float32)
        chunk = np.vstack([pad_pre, pcm, pad_post])[:target_samples]
        voice_chunks.append(chunk)
        cursor = end_t

    total_dur = round(cursor, 2)
    voice_full = np.vstack(voice_chunks)
    n_samples = len(voice_full)
    t = np.linspace(0.0, n_samples / sr, n_samples, endpoint=False)

    # Warm scientific corporate ambient pad (D minor / F major progression)
    bed = np.zeros((n_samples, 2), dtype=np.float32)
    chords = [
        (146.83, 220.00, 261.63, 349.23),  # Dm7
        (130.81, 196.00, 246.94, 329.63),  # Cmaj7
        (116.54, 174.61, 220.00, 293.66),  # Bbmaj7
        (130.81, 196.00, 261.63, 329.63),  # Cadd9
    ]
    bar_len = 8.0
    for i in range(int(np.ceil(total_dur / bar_len))):
        c = chords[i % len(chords)]
        i0 = int(i * bar_len * sr)
        i1 = min(n_samples, int((i + 1) * bar_len * sr))
        if i1 <= i0:
            break
        lt = t[i0:i1] - i * bar_len
        env = np.sin(np.pi * np.clip(lt / bar_len, 0, 1)) ** 0.45
        sig = np.zeros_like(lt)
        for idx, freq in enumerate(c):
            sig += (0.28 / (idx + 1)) * np.sin(2 * np.pi * freq * lt)
            sig += (0.08 / (idx + 1)) * np.sin(2 * np.pi * (freq * 1.002) * lt)
        pulse = 0.04 * np.exp(-((lt % 0.5) / 0.08)) * np.sin(2 * np.pi * 110.0 * lt)
        bed[i0:i1, 0] += env * (sig + pulse)
        bed[i0:i1, 1] += env * (sig * 0.98 + pulse)

    fade_in = int(1.0 * sr)
    fade_out = int(2.0 * sr)
    bed[:fade_in] *= np.linspace(0, 1, fade_in)[:, None]
    bed[-fade_out:] *= np.linspace(1, 0, fade_out)[:, None]

    sfx = np.zeros((n_samples, 2), dtype=np.float32)

    def add_chime(at_t: float, base_f: float = 880.0, amp: float = 0.08):
        s0 = int(at_t * sr)
        dur_s = int(0.8 * sr)
        s1 = min(n_samples, s0 + dur_s)
        if s1 <= s0:
            return
        lt = np.linspace(0, (s1 - s0) / sr, s1 - s0, endpoint=False)
        tone = amp * np.exp(-lt / 0.22) * (
            0.7 * np.sin(2 * np.pi * base_f * lt) + 0.3 * np.sin(2 * np.pi * (base_f * 1.5) * lt)
        )
        sfx[s0:s1, 0] += tone
        sfx[s0:s1, 1] += tone

    for idx, sc in enumerate(timeline):
        add_chime(sc["start"] + 0.12, 784.0 if idx % 2 == 0 else 987.77, 0.06)

    # Scene 6 dramatic pressure-relief / spark burst SFX
    sc6 = timeline[5]
    burst_t = sc6["start"] + sc6["duration"] * 0.52
    b0 = int(burst_t * sr)
    b_len = int(1.6 * sr)
    b1 = min(n_samples, b0 + b_len)
    if b1 > b0:
        lt = np.linspace(0, (b1 - b0) / sr, b1 - b0, endpoint=False)
        rng = np.random.default_rng(42)
        noise = rng.normal(0, 1, len(lt)).astype(np.float32)
        hiss = np.convolve(noise, np.ones(12) / 12.0, mode="same")
        thump = np.sin(2 * np.pi * (95.0 * np.exp(-lt * 3.5) + 38.0) * lt) * np.exp(-lt / 0.28)
        burst = 0.24 * thump + 0.12 * hiss * np.exp(-lt / 0.45)
        sfx[b0:b1, 0] += burst
        sfx[b0:b1, 1] += burst

    voice_env = np.abs(voice_full[:, 0])
    win = int(0.15 * sr)
    kernel = np.ones(win, dtype=np.float32) / win
    smooth_v = np.convolve(voice_env, kernel, mode="same")
    duck = np.clip(1.0 - smooth_v * 3.5, 0.35, 1.0)[:, None]

    mix = voice_full * 0.95 + bed * 0.14 * duck + sfx * 0.75
    mix = np.clip(mix, -0.98, 0.98)

    raw_mix_path = os.path.join(AUDIO_DIR, "raw_mix.wav")
    with wave.open(raw_mix_path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((mix * 32767.0).astype(np.int16).tobytes())

    master_wav = os.path.join(AUDIO_DIR, "master_audio.wav")
    master_mp3 = os.path.join(AUDIO_DIR, "master_audio.mp3")
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", raw_mix_path,
            "-af", "loudnorm=I=-14:TP=-1.5:LRA=6",
            "-ar", "48000", "-ac", "2",
            master_wav,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        ["ffmpeg", "-y", "-i", master_wav, "-b:a", "192k", master_mp3],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    timeline_path = os.path.join(PROJECT_DIR, "src", "scene_timings.json")
    with open(timeline_path, "w", encoding="utf-8") as f:
        json.dump({"total_duration": total_dur, "fps": 30, "scenes": timeline}, f, indent=2)

    print(f"Total video duration: {total_dur}s")
    for sc in timeline:
        print(f"  {sc['id']}: {sc['start']:.2f}s -> {sc['end']:.2f}s (dur={sc['duration']:.2f}s, speech={sc['speech_duration']:.2f}s)")


if __name__ == "__main__":
    asyncio.run(synth_all())
    build_timeline_and_mix()
