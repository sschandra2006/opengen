import asyncio
import edge_tts
import subprocess
import os

AUDIO_DIR = r"F:\motion graphics\motion studio\projects\orizine-promotion\audio"

VO_TRACKS = [
    {
        "id": "vo_1_hero",
        "text": "Tired of Xerox queues? Meet Orizine.",
        "start": 0.35,
        "rate": "+20%",
        "pitch": "+2Hz"
    },
    {
        "id": "vo_2_upload",
        "text": "Drop files up to 200MB. Free PDF tools included.",
        "start": 4.65,
        "rate": "+20%",
        "pitch": "+1Hz"
    },
    {
        "id": "vo_3_config",
        "text": "Split sections easily. Colour covers, B&W notes, and thermal binding.",
        "start": 10.35,
        "rate": "+20%",
        "pitch": "+1Hz"
    },
    {
        "id": "vo_4_store",
        "text": "Printouts from one rupee. Plus official college stationery.",
        "start": 16.95,
        "rate": "+20%",
        "pitch": "+1Hz"
    },
    {
        "id": "vo_5_delivery",
        "text": "Delivered at your gate before 9 AM.",
        "start": 21.95,
        "rate": "+20%",
        "pitch": "+2Hz"
    },
    {
        "id": "vo_6_cta",
        "text": "Order today at Orizine.in.",
        "start": 26.25,
        "rate": "+18%",
        "pitch": "+2Hz"
    }
]

async def generate_vo():
    for vo in VO_TRACKS:
        out_p = os.path.join(AUDIO_DIR, f"{vo['id']}.mp3")
        c = edge_tts.Communicate(vo["text"], "en-IN-PrabhatNeural", rate=vo["rate"], pitch=vo["pitch"])
        await c.save(out_p)
        res = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", out_p
        ], capture_output=True, text=True)
        dur = float(res.stdout.strip())
        print(f"Generated {vo['id']}: start={vo['start']}s, dur={dur:.2f}s, ends={vo['start']+dur:.2f}s")

def mix_master():
    master_path = os.path.join(AUDIO_DIR, "master_audio.mp3")
    inputs = []

    # Input 0: Warm subtle paper texture noise
    inputs.extend(["-f", "lavfi", "-i", "anoisesrc=d=30:c=pink:r=48000:a=0.008"])

    # Inputs 1-6: Voices
    for vo in VO_TRACKS:
        inputs.extend(["-i", os.path.join(AUDIO_DIR, f"{vo['id']}.mp3")])

    filter_parts = []
    # Background music: upbeat, warm organic acoustic-electronic groove (BPM 120, warm chords)
    filter_parts.append(
        "aevalsrc='0.09*sin(2*PI*130.81*t)*exp(-3*mod(t,0.5)) + 0.06*sin(2*PI*196.00*t)*exp(-4*mod(t,0.25)) + 0.04*sin(2*PI*329.63*t)*sin(2*PI*0.2*t)':s=48000:d=30[bg_music];"
    )

    # Tactile Sound Effects (Mechanical printer clicks, paper shuffles, stamps):
    # t=0.3: Paper fan slide shuffle
    filter_parts.append("aevalsrc='0.22*sin(2*PI*(300+1200*t)*t)*between(t,0.25,0.75)*exp(-5*(t-0.25))':s=48000:d=30[sfx_fan];")
    # t=4.6: Digital drag & drop dropzone snap
    filter_parts.append("aevalsrc='0.3*sin(2*PI*880*t)*between(t,4.5,5.1)*exp(-6*(t-4.5))':s=48000:d=30[sfx_drop];")
    # t=10.3: 4-block tactile switch clicks
    filter_parts.append("aevalsrc='0.35*(sin(2*PI*1400*t)+sin(2*PI*1750*t))*between(t,10.2,10.7)*exp(-8*(t-10.2))':s=48000:d=30[sfx_switch];")
    # t=16.9: Cash register bell & paper slip pop
    filter_parts.append("aevalsrc='0.28*sin(2*PI*2093*t)*between(t,16.8,17.6)*exp(-4*(t-16.8))':s=48000:d=30[sfx_chime];")
    # t=21.9: Thermal receipt tear line / delivery notification
    filter_parts.append("aevalsrc='0.32*(sin(2*PI*1174*t)+sin(2*PI*1480*t))*between(t,21.8,22.6)*exp(-4*(t-21.8))':s=48000:d=30[sfx_gate];")
    # t=26.2: Final tactile pill button press hit
    filter_parts.append("aevalsrc='0.4*sin(2*PI*164.81*t)*between(t,26.1,29.5)*exp(-1*(t-26.1))':s=48000:d=30[sfx_cta];")

    # Delays for voiceovers
    for idx, vo in enumerate(VO_TRACKS):
        d_ms = int(vo["start"] * 1000)
        filter_parts.append(f"[{idx+1}:a]adelay={d_ms}|{d_ms},volume=1.55[v{idx+1}];")

    v_refs = "".join([f"[v{i+1}]" for i in range(len(VO_TRACKS))])
    total_mix = 1 + len(VO_TRACKS) + 6
    filter_parts.append(
        f"[bg_music][sfx_fan][sfx_drop][sfx_switch][sfx_chime][sfx_gate][sfx_cta]{v_refs}"
        f"amix=inputs={total_mix}:duration=first:dropout_transition=2,"
        f"loudnorm=I=-14:TP=-1.5:LRA=7[out_audio]"
    )

    full_filter = "".join(filter_parts)
    cmd = [
        "ffmpeg", "-y",
        *inputs,
        "-filter_complex", full_filter,
        "-map", "[out_audio]",
        "-t", "30.0",
        "-b:a", "192k",
        master_path
    ]
    subprocess.run(cmd, check=True)
    print(f"[SUCCESS] Aligned Master Audio generated: {master_path}")

if __name__ == "__main__":
    asyncio.run(generate_vo())
    mix_master()
