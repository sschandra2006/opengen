"""
Audio Generation Pipeline for Orizine Product Showcase Reel (30 Seconds)
Generates youthful Indian English voiceover and mixes synchronized sound design.
"""

import os
import subprocess
import asyncio
import edge_tts

AUDIO_DIR = os.path.dirname(os.path.abspath(__file__))

SCENES_VO = [
    {
        "id": "s1_hook",
        "voice": "en-IN-PrabhatNeural",
        "rate": "+15%",
        "pitch": "+2Hz",
        "text": "Tired of standing in morning Xerox queues before class? There is a smarter way to print.",
        "start": 0.4
    },
    {
        "id": "s2_homepage",
        "voice": "en-IN-PrabhatNeural",
        "rate": "+12%",
        "pitch": "+0Hz",
        "text": "Meet Orizine. Your college print shop, right on your screen.",
        "start": 3.4
    },
    {
        "id": "s3_upload",
        "voice": "en-IN-PrabhatNeural",
        "rate": "+15%",
        "pitch": "+0Hz",
        "text": "Drag and drop any lab manual, notes, or slides up to 200MB. Plus, free built-in PDF tools.",
        "start": 7.6
    },
    {
        "id": "s4_config",
        "voice": "en-IN-PrabhatNeural",
        "rate": "+15%",
        "pitch": "+2Hz",
        "text": "Split sections with full control. Colour for diagrams, B&W for notes, professional binding, and live transparent pricing.",
        "start": 12.6
    },
    {
        "id": "s5_stationery",
        "voice": "en-IN-PrabhatNeural",
        "rate": "+14%",
        "pitch": "+2Hz",
        "text": "Need lab sheets or registers? Add college stationery to the exact same order with zero extra delivery fee.",
        "start": 17.6
    },
    {
        "id": "s6_delivery",
        "voice": "en-IN-PrabhatNeural",
        "rate": "+12%",
        "pitch": "+0Hz",
        "text": "Order before midnight. We print, bind, and deliver directly to your college gate before 9 AM, 100% free.",
        "start": 22.6
    },
    {
        "id": "s7_cta",
        "voice": "en-IN-PrabhatNeural",
        "rate": "+10%",
        "pitch": "+2Hz",
        "text": "Zero queues. Perfect prints. Order now at Orizine.in.",
        "start": 26.8
    }
]

async def generate_speech():
    print("[Audio] Generating scene voiceovers with edge-tts (en-IN-PrabhatNeural)...")
    for s in SCENES_VO:
        out_path = os.path.join(AUDIO_DIR, f"{s['id']}.mp3")
        communicate = edge_tts.Communicate(
            text=s["text"],
            voice=s["voice"],
            rate=s["rate"],
            pitch=s["pitch"]
        )
        await communicate.save(out_path)
        print(f"  -> Generated: {s['id']}.mp3")

def create_master_mix():
    print("[Audio] Mixing multi-track master audio with background bed and UI sound design...")
    master_path = os.path.join(AUDIO_DIR, "master_audio.mp3")

    inputs = []
    # Input 0: base noise bed
    inputs.extend(["-f", "lavfi", "-i", "anoisesrc=d=30:c=pink:r=48000:a=0.010"])

    # Inputs 1-7: Voiceovers
    for s in SCENES_VO:
        vo_file = os.path.join(AUDIO_DIR, f"{s['id']}.mp3")
        inputs.extend(["-i", vo_file])

    filter_parts = []
    
    # Background music bed: modern upbeat electronic tech pulse (BPM 124, 48kHz)
    filter_parts.append(
        "aevalsrc='0.12*sin(2*PI*124*t)*exp(-3*mod(t,0.484)) + 0.08*sin(2*PI*248*t)*exp(-6*mod(t,0.242)) + 0.04*sin(2*PI*496*t)*sin(2*PI*0.25*t)':s=48000:d=30[bg_music];"
    )

    # UI Sound Effects:
    # t=0.4: Attention whoosh
    filter_parts.append("aevalsrc='0.25*sin(2*PI*(200+1000*t)*t)*between(t,0.3,0.9)*exp(-4*(t-0.3))':s=48000:d=30[sfx_whoosh1];")
    # t=3.3: Modern UI click / slide
    filter_parts.append("aevalsrc='0.3*sin(2*PI*1500*t)*between(t,3.3,3.6)*exp(-10*(t-3.3))':s=48000:d=30[sfx_click1];")
    # t=7.7: File upload drop confirmation
    filter_parts.append("aevalsrc='0.35*sin(2*PI*880*t)*between(t,7.6,8.2)*exp(-5*(t-7.6))':s=48000:d=30[sfx_drop];")
    # t=12.7: Section splitter mechanical switches
    filter_parts.append("aevalsrc='0.3*(sin(2*PI*1200*t)+sin(2*PI*1600*t))*between(t,12.7,13.2)*exp(-6*(t-12.7))':s=48000:d=30[sfx_switch];")
    # t=17.7: Shopping cart pop & coin chime
    filter_parts.append("aevalsrc='0.3*sin(2*PI*2093*t)*between(t,17.6,18.4)*exp(-4*(t-17.6))':s=48000:d=30[sfx_cart];")
    # t=22.7: Morning gate drop notification
    filter_parts.append("aevalsrc='0.35*(sin(2*PI*1046*t)+sin(2*PI*1318*t))*between(t,22.6,23.4)*exp(-3*(t-22.6))':s=48000:d=30[sfx_gate];")
    # t=27.0: Brand chord resonance
    filter_parts.append("aevalsrc='0.4*sin(2*PI*110*t)*between(t,26.8,29.8)*exp(-0.8*(t-26.8))':s=48000:d=30[sfx_brand];")

    # Delays for voice clips
    for idx, s in enumerate(SCENES_VO):
        delay_ms = int(s["start"] * 1000)
        filter_parts.append(f"[{idx+1}:a]adelay={delay_ms}|{delay_ms},volume=1.45[vo{idx+1}];")

    vo_refs = "".join([f"[vo{i+1}]" for i in range(len(SCENES_VO))])
    total_mix_inputs = 1 + len(SCENES_VO) + 7
    filter_parts.append(
        f"[bg_music][sfx_whoosh1][sfx_click1][sfx_drop][sfx_switch][sfx_cart][sfx_gate][sfx_brand]{vo_refs}"
        f"amix=inputs={total_mix_inputs}:duration=first:dropout_transition=2,"
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

    print("[Audio] Running FFmpeg master audio mix...")
    subprocess.run(cmd, check=True)
    print(f"[SUCCESS] Master audio generated: {master_path}")

if __name__ == "__main__":
    asyncio.run(generate_speech())
    create_master_mix()
