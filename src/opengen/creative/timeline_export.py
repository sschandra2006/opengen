"""
NLE Timeline Exporter for Engine 5 (StoryToolkitAI & AutoSubs Ecosystem Adapter).
Converts OpenGen IR v1.1.0 project specifications into industry-standard:
1. CMX 3600 EDL (.edl) for DaVinci Resolve and Avid Media Composer.
2. Apple Final Cut Pro XML (.fcpxml) for DaVinci Resolve, Premiere Pro, and Final Cut Pro.
Enables professional human video editors to polish AI-directed rough cuts inside NLEs.
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
import xml.etree.ElementTree as ET
import xml.dom.minidom


def seconds_to_smpte(seconds: float, fps: int = 30) -> str:
    """Converts decimal seconds into standard SMPTE timecode (HH:MM:SS:FF)."""
    total_frames = max(0, int(round(seconds * fps)))
    ff = total_frames % fps
    total_secs = total_frames // fps
    ss = total_secs % 60
    total_mins = total_secs // 60
    mm = total_mins % 60
    hh = total_mins // 60
    return f"{hh:02d}:{mm:02d}:{ss:02d}:{ff:02d}"


class NLETimelineExporter:
    """Generates professional NLE timeline interchange formats from OpenGen IR."""

    @classmethod
    def export_cmx3600_edl(
        cls,
        project_ir: Dict[str, Any],
        output_edl_path: Optional[str] = None,
        reel_name: str = "AX"
    ) -> str:
        """
        Exports OpenGen IR scenes into a standard CMX 3600 Edit Decision List.
        """
        title = project_ir.get("title", "OpenGen_Ad").replace(" ", "_")
        settings = project_ir.get("settings", {})
        fps = settings.get("fps", 30)
        scenes = project_ir.get("scenes", [])

        lines = [
            f"TITLE: {title}",
            f"FCM: NON-DROP FRAME",
            ""
        ]

        record_in = 0.0
        for idx, sc in enumerate(scenes):
            event_num = f"{idx + 1:03d}"
            dur = sc.get("duration", 2.0)
            record_out = record_in + dur

            # Source timecode (assuming media starts at 00:00:00:00)
            src_in_tc = "00:00:00:00"
            src_out_tc = seconds_to_smpte(dur, fps)

            # Record timecode
            rec_in_tc = seconds_to_smpte(record_in, fps)
            rec_out_tc = seconds_to_smpte(record_out, fps)

            # CMX 3600 Event line: [EVENT] [REEL] [TRACK] [TRANSITION] [SRC_IN] [SRC_OUT] [REC_IN] [REC_OUT]
            lines.append(f"{event_num}  {reel_name:<8} V     C        {src_in_tc} {src_out_tc} {rec_in_tc} {rec_out_tc}")
            sc_id = sc.get("id", f"scene_{idx}")
            sc_name = sc.get("name", sc_id)
            lines.append(f"* FROM CLIP NAME: {sc_name}")
            lines.append("")

            record_in = record_out

        edl_content = "\n".join(lines)

        if output_edl_path:
            out_p = Path(output_edl_path).resolve()
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(edl_content, encoding="utf-8")

        return edl_content

    @classmethod
    def export_fcpxml(
        cls,
        project_ir: Dict[str, Any],
        output_fcpxml_path: Optional[str] = None
    ) -> str:
        """
        Exports OpenGen IR scenes into Apple Final Cut Pro XML (FCPXML v1.9).
        """
        title = project_ir.get("title", "OpenGen Ad")
        settings = project_ir.get("settings", {})
        fps = settings.get("fps", 30)
        width = settings.get("width", 1080)
        height = settings.get("height", 1920)
        scenes = project_ir.get("scenes", [])
        total_duration = sum(s.get("duration", 0) for s in scenes)

        # FCPXML Root
        fcpxml = ET.Element("fcpxml", version="1.9")
        resources = ET.SubElement(fcpxml, "resources")

        # Format Resource
        format_elem = ET.SubElement(
            resources, "format",
            id="r1",
            name=f"FFVideoFormat{width}x{height}p{fps}",
            frameDuration=f"1/{fps}s",
            width=str(width),
            height=str(height)
        )

        library = ET.SubElement(fcpxml, "library")
        event = ET.SubElement(library, "event", name="OpenGen Commercials")
        project = ET.SubElement(event, "project", name=title)
        sequence = ET.SubElement(
            project, "sequence",
            format="r1",
            duration=f"{int(total_duration * fps)}/{fps}s"
        )
        spine = ET.SubElement(sequence, "spine")

        # Add scenes as sequence clips
        for idx, sc in enumerate(scenes):
            dur = sc.get("duration", 2.0)
            sc_id = sc.get("id", f"sc_{idx}")
            sc_name = sc.get("name", sc_id)
            frames = int(dur * fps)

            clip = ET.SubElement(
                spine, "clip",
                name=sc_name,
                duration=f"{frames}/{fps}s",
                format="r1",
                offset=f"{int(sc.get('start', 0) * fps)}/{fps}s"
            )
            # Add metadata note
            note = ET.SubElement(clip, "note")
            note.text = f"Scene ID: {sc_id} | Phase: {sc.get('creativeAdDirectives', {}).get('funnelPhase', 'content')}"

        # Pretty print XML
        raw_xml = ET.tostring(fcpxml, encoding="utf-8")
        parsed = xml.dom.minidom.parseString(raw_xml)
        pretty_xml = parsed.toprettyxml(indent="  ")

        if output_fcpxml_path:
            out_p = Path(output_fcpxml_path).resolve()
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(pretty_xml, encoding="utf-8")

        return pretty_xml
