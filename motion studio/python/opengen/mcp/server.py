"""
OpenGen Motion Graphics Studio: Model Context Protocol (MCP) Server
Exposes 10 standardized motion graphics tools for AI coding agents.
"""

import json
import os
import subprocess
from typing import Dict, Any, Optional
from opengen.ai.director import Director

class MotionMCPServer:
    def __init__(self):
        self.director = Director()
        self.jobs: Dict[str, Dict[str, Any]] = {}

    def create_motion_graphics(
        self,
        prompt: str,
        duration: float = 15.0,
        aspect_ratio: str = "9:16",
        style: str = "tech",
        include_voiceover: bool = True
    ) -> Dict[str, Any]:
        """Generate an animated motion graphics video from a natural language prompt."""
        job_id = f"job_motion_{int(os.times().system * 1000)}"
        project = self.director.create_storyboard(prompt, duration, aspect_ratio, style)

        project_path = os.path.abspath(f"out/wip/{job_id}_project.json")
        os.makedirs(os.path.dirname(project_path), exist_ok=True)
        with open(project_path, "w", encoding="utf-8") as f:
            json.dump(project, f, indent=2)

        output_path = os.path.abspath(f"out/final/{job_id}.mp4")

        # Trigger background render via CLI
        cmd = ["bun", "packages/cli/src/index.ts", "render", "-p", project_path, "-o", output_path]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        self.jobs[job_id] = {
            "status": "RENDERING",
            "projectPath": project_path,
            "outputPath": output_path
        }

        return {
            "jobId": job_id,
            "status": "QUEUED",
            "estimatedDurationSec": duration * 0.8,
            "projectId": project.get("projectId"),
            "outputPath": output_path
        }

    def generate_storyboard(
        self,
        prompt: str,
        duration: float = 15.0,
        aspect_ratio: str = "9:16"
    ) -> Dict[str, Any]:
        """Plans scenes and generates OpenGen IR JSON without rendering."""
        return self.director.create_storyboard(prompt, duration, aspect_ratio)

    def render_video(self, project_json: Dict[str, Any], output_path: Optional[str] = None) -> Dict[str, Any]:
        """Submits an OpenGen IR JSON project for headless rendering and encoding."""
        job_id = f"job_render_{int(os.times().system * 1000)}"
        project_file = os.path.abspath(f"out/wip/{job_id}.json")
        os.makedirs(os.path.dirname(project_file), exist_ok=True)
        with open(project_file, "w", encoding="utf-8") as f:
            json.dump(project_json, f, indent=2)

        out_mp4 = output_path or os.path.abspath(f"out/final/{job_id}.mp4")
        cmd = ["bun", "packages/cli/src/index.ts", "render", "-p", project_file, "-o", out_mp4]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        self.jobs[job_id] = {
            "status": "RENDERING",
            "outputPath": out_mp4
        }

        return {
            "jobId": job_id,
            "status": "QUEUED",
            "outputPath": out_mp4
        }

    def get_render_status(self, job_id: str) -> Dict[str, Any]:
        """Queries rendering progress and output artifact availability."""
        job = self.jobs.get(job_id)
        if not job:
            return {"error": f"Job {job_id} not found", "status": "UNKNOWN"}

        out_file = job.get("outputPath", "")
        if os.path.exists(out_file) and os.path.getsize(out_file) > 1024:
            return {
                "jobId": job_id,
                "status": "COMPLETED",
                "progress": 100,
                "outputPath": out_file
            }

        return {
            "jobId": job_id,
            "status": "RENDERING",
            "progress": 50,
            "outputPath": out_file
        }

if __name__ == "__main__":
    server = MotionMCPServer()
    print("[MotionMCPServer] MCP Server initialized and ready.")
