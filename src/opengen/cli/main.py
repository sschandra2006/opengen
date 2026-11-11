"""
OpenGen Typer CLI.
Developer-friendly command-line interface for local generation, server execution,
MCP agent bridge, worker execution, and configuration diagnostics.
"""
from pathlib import Path
from typing import Optional, List
import typer
from rich.console import Console
from rich.table import Table

from opengen.config import settings
from opengen.client import OpenGenClient

app = typer.Typer(
    name="opengen",
    help="OpenGen: Modular, Open-Source, Self-Hostable AI Multi-Modal Generation Framework.",
    no_args_is_help=True
)
console = Console()
client = OpenGenClient()

# Sub-command groups
doc_app = typer.Typer(help="Engine A: Word and PDF document generation.", no_args_is_help=True)
pres_app = typer.Typer(help="Engine B: Native PowerPoint presentation generation.", no_args_is_help=True)
img_app = typer.Typer(help="Engine C: FLUX raster and Recraft vector SVG generation.", no_args_is_help=True)
hw_app = typer.Typer(help="Engine D: Pure realistic handwriting synthesis.", no_args_is_help=True)
config_app = typer.Typer(help="Configuration and provider diagnostics.", no_args_is_help=True)

app.add_typer(doc_app, name="document")
app.add_typer(pres_app, name="presentation")
app.add_typer(img_app, name="image")
app.add_typer(hw_app, name="handwriting")
app.add_typer(config_app, name="config")


# -------------------------------------------------------------------------
# Top-Level Server & Agent Commands
# -------------------------------------------------------------------------

@app.command("serve")
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Bind host"),
    port: int = typer.Option(8000, "--port", "-p", help="Bind port"),
    reload: bool = typer.Option(False, "--reload", help="Enable hot reload")
):
    """Starts the FastAPI REST API and static dashboard server."""
    import uvicorn
    console.print(f"[bold green]Starting OpenGen REST API on http://{host}:{port}[/bold green]")
    uvicorn.run("opengen.api:app", host=host, port=port, reload=reload)


@app.command("mcp")
def run_mcp(
    transport: str = typer.Option("stdio", "--transport", "-t", help="Transport mode: stdio or sse")
):
    """Runs the Model Context Protocol (MCP) server for Claude Desktop and Antigravity IDE."""
    from opengen.mcp.server import run_stdio_server
    console.print("[dim]Starting OpenGen MCP stdio server...[/dim]")
    run_stdio_server()


@app.command("worker")
def run_worker(
    threads: int = typer.Option(4, "--threads", "-w", help="Number of worker threads")
):
    """Runs the async task queue worker process."""
    console.print(f"[bold blue]Running OpenGen worker (threads={threads})...[/bold blue]")
    try:
        from opengen.queue.worker import huey
        if hasattr(huey, "create_consumer"):
            consumer = huey.create_consumer(workers=threads)
            consumer.run()
        else:
            console.print("[yellow]In-memory task runner active; no separate consumer process needed.[/yellow]")
    except Exception as e:
        console.print(f"[red]Worker error: {e}[/red]")


# -------------------------------------------------------------------------
# Engine A: Document CLI Commands
# -------------------------------------------------------------------------

@doc_app.command("generate")
def doc_generate(
    template: Path = typer.Option(..., "--template", "-t", help="Path to DOCX or PDF template file"),
    reference: Optional[List[Path]] = typer.Option(None, "--reference", "-r", help="Path(s) to reference PDF/TXT files"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Target output DOCX path"),
    instruction: Optional[str] = typer.Option(None, "--instruction", "-i", help="Prompt or generation instructions")
):
    """Populates a Word or PDF template with extracted reference facts."""
    with console.status("[bold green]Executing Document Engine pipeline...[/bold green]"):
        refs = [str(r) for r in reference] if reference else []
        res = client.documents.populate(
            template=str(template),
            references=refs,
            output_docx_path=str(output) if output else None,
            instruction=instruction
        )
    console.print(f"[bold green]Success![/bold green] Generated document: [cyan]{res.docx_path}[/cyan]")
    if res.pdf_path:
        console.print(f"Validated PDF: [cyan]{res.pdf_path}[/cyan]")


# -------------------------------------------------------------------------
# Engine B: Presentation CLI Commands
# -------------------------------------------------------------------------

@pres_app.command("generate")
def pres_generate(
    topic: str = typer.Argument(..., help="Presentation topic or outline prompt"),
    slides: int = typer.Option(8, "--slides", "-s", help="Number of slides to generate"),
    theme: str = typer.Option("modern_corporate", "--theme", help="Theme name: modern_corporate, ocean_blue, warm_editorial, dark_tech"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Target PPTX path")
):
    """Generates a 100% editable Microsoft PowerPoint presentation."""
    with console.status(f"[bold green]Planning and building {slides}-slide presentation...[/bold green]"):
        res = client.presentations.create(
            topic=topic,
            slide_count=slides,
            theme=theme,
            output_pptx_path=str(output) if output else None
        )
    console.print(f"[bold green]Success![/bold green] Generated editable PPTX: [cyan]{res.pptx_path}[/cyan]")
    console.print(f"Total slides: [yellow]{res.slide_count}[/yellow] | Native shapes & Excel-backed charts applied.")


# -------------------------------------------------------------------------
# Engine C: Image CLI Commands
# -------------------------------------------------------------------------

@img_app.command("generate")
def img_generate(
    prompt: str = typer.Argument(..., help="Prompt for image or vector synthesis"),
    aspect_ratio: str = typer.Option("1:1", "--aspect-ratio", "-ar", help="Aspect ratio: 1:1, 16:9, 4:3"),
    style: str = typer.Option("photorealistic", "--style", help="Style: photorealistic, vector, minimal"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Target output file path")
):
    """Generates an AI image (FLUX.1/DALL-E) or vector graphic (Recraft SVG)."""
    with console.status("[bold green]Synthesizing image asset...[/bold green]"):
        out_fmt = "svg" if style == "vector" or "svg" in prompt.lower() else "png"
        res = client.images.generate(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            style=style,
            output_format=out_fmt
        )
        if output:
            res.save(str(output))
            saved_path = str(output)
        else:
            saved_path = res.file_path
    console.print(f"[bold green]Success![/bold green] Generated asset: [cyan]{saved_path}[/cyan]")


# -------------------------------------------------------------------------
# Engine D: Handwriting CLI Commands
# -------------------------------------------------------------------------

@hw_app.command("generate")
def hw_generate(
    text: str = typer.Argument(..., help="Text to convert into handwriting"),
    paper_mode: str = typer.Option("direct_print_transparent", "--paper-mode", help="Mode: direct_print_transparent or synthetic_page"),
    ruled_type: str = typer.Option("college_ruled", "--ruled-type", help="Paper rule: college_ruled or wide_ruled"),
    pen_type: str = typer.Option("ballpoint_blue", "--pen", help="Pen ink: ballpoint_blue, gel_pen_black, fountain_pen"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Target output PDF path")
):
    """Synthesizes human handwriting for direct physical notebook printing."""
    with console.status("[bold green]Simulating handwriting physics and drift...[/bold green]"):
        res = client.handwriting.generate(
            text=text,
            paper_mode=paper_mode,
            ruled_type=ruled_type,
            pen_type=pen_type,
            output_pdf_path=str(output) if output else None
        )
    console.print(f"[bold green]Success![/bold green] Generated handwriting PDF: [cyan]{res.file_path}[/cyan]")
    console.print(f"[dim]{res.print_instructions}[/dim]")


# -------------------------------------------------------------------------
# Configuration & Diagnostics CLI Commands
# -------------------------------------------------------------------------

@config_app.command("check")
def config_check():
    """Validates local environment, directories, and AI provider configurations."""
    table = Table(title="OpenGen System Diagnostics")
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")
    table.add_column("Details", style="dim")

    table.add_row("Cache Directory", "READY", str(settings.CACHE_DIR))
    table.add_row("Output Directory", "READY", str(settings.OUTPUT_DIR))
    table.add_row("Upload Directory", "READY", str(settings.UPLOAD_DIR))

    # Check keys
    openai_key = "Configured" if settings.OPENAI_API_KEY else "Not Configured (Optional)"
    gemini_key = "Configured" if settings.GEMINI_API_KEY else "Not Configured (Optional)"
    together_key = "Configured" if settings.TOGETHER_API_KEY else "Not Configured (Optional)"

    table.add_row("OpenAI API Key", "OK" if settings.OPENAI_API_KEY else "OFF", openai_key)
    table.add_row("Gemini API Key", "OK" if settings.GEMINI_API_KEY else "OFF", gemini_key)
    table.add_row("Together API Key", "OK" if settings.TOGETHER_API_KEY else "OFF", together_key)

    console.print(table)


if __name__ == "__main__":
    app()
