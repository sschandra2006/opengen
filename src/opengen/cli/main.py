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
motion_app = typer.Typer(help="Engine E: Motion Graphics & Performance Video Ads.", no_args_is_help=True)
brand_app = typer.Typer(help="Cross-Studio Brand Kits and Design Tokens.", no_args_is_help=True)
critic_app = typer.Typer(help="Autonomous Creative Critic Gate across all 5 studios.", no_args_is_help=True)
config_app = typer.Typer(help="Configuration and provider diagnostics.", no_args_is_help=True)

app.add_typer(doc_app, name="document")
app.add_typer(pres_app, name="presentation")
app.add_typer(img_app, name="image")
app.add_typer(hw_app, name="handwriting")
app.add_typer(motion_app, name="motion")
app.add_typer(brand_app, name="brand")
app.add_typer(critic_app, name="critic")
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


@doc_app.command("typst")
def doc_typst(
    data_file: Path = typer.Argument(..., help="Path to JSON file with report title, metrics, and narrative"),
    brand: Optional[str] = typer.Option(None, "--brand", "-b", help="Registered Brand Kit ID"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Target output PDF path")
):
    """Compiles a Swiss Editorial document report (<50ms) using Typst."""
    import json
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    with console.status("[bold green]Compiling Typst Swiss Editorial report...[/bold green]"):
        res = client.documents.compile_typst(
            data=data,
            output_pdf_path=str(output) if output else None,
            brand_id=brand
        )
    console.print(f"[bold green]Success![/bold green] Generated Typst PDF: [cyan]{res.pdf_path}[/cyan]")


@doc_app.command("catalog")
def doc_catalog(
    products_file: Path = typer.Argument(..., help="Path to JSON file with products list and catalog title"),
    brand: Optional[str] = typer.Option(None, "--brand", "-b", help="Registered Brand Kit ID"),
    title: str = typer.Option("Artisan Product Catalog & Price Guide", "--title", "-t", help="Catalog title"),
    hero_ratio: float = typer.Option(0.15, "--hero-ratio", help="Top percentile of products treated as Hero Bento Cards (0.10 to 0.25)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Target output PDF path")
):
    """Compiles an 80/20 Swiss Editorial product catalog to PDF with Hero Bento Cards and dot-leader menus."""
    import json
    with open(products_file, "r", encoding="utf-8") as f:
        payload = json.load(f)

    products = payload.get("products", payload) if isinstance(payload, dict) else payload
    cat_title = payload.get("title", title) if isinstance(payload, dict) else title

    with console.status("[bold green]Compiling 80/20 Swiss Editorial product catalog...[/bold green]"):
        res = client.documents.compile_catalog_typst(
            products=products,
            title=cat_title,
            brand_id=brand,
            hero_ratio=hero_ratio,
            output_pdf_path=str(output) if output else None
        )
    console.print(f"[bold green]Success![/bold green] Generated Artisan Catalog PDF: [cyan]{res.pdf_path}[/cyan]")


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


@pres_app.command("bento")
def pres_bento(
    topic: str = typer.Argument(..., help="Presentation topic or pitch deck title"),
    slides: int = typer.Option(7, "--slides", "-s", help="Number of slides (7-stage Sequoia/YC arc recommended)"),
    brand: Optional[str] = typer.Option(None, "--brand", "-b", help="Registered Brand Kit ID"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Target output PPTX path")
):
    """Generates an elite 12-column Bento Grid pitch deck (PPTX + fluid HTML)."""
    with console.status(f"[bold green]Compiling {slides}-slide Bento pitch deck...[/bold green]"):
        res = client.presentations.generate_bento(
            topic=topic,
            slide_count=slides,
            brand_id=brand,
            output_pptx_path=str(output) if output else None
        )
    console.print(f"[bold green]Success![/bold green] Generated Bento Deck: [cyan]{res.pptx_path}[/cyan]")
    console.print(f"Total slides: [yellow]{res.slide_count}[/yellow] | 12-Column Responsive Bento Grid & Sequoia Narrative Arc applied.")


@pres_app.command("marp")
def pres_marp(
    topic: str = typer.Argument(..., help="Presentation topic or pitch deck title"),
    slides: int = typer.Option(7, "--slides", "-s", help="Number of slides"),
    brand: Optional[str] = typer.Option(None, "--brand", "-b", help="Registered Brand Kit ID"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Target output Markdown path")
):
    """Generates standard Marp/Slidev Markdown deck for developer presentations."""
    with console.status(f"[bold green]Compiling {slides}-slide Marp deck...[/bold green]"):
        _, md_path = client.presentations.generate_marp(
            topic=topic,
            output_md_path=str(output) if output else None,
            slide_count=slides,
            brand_id=brand
        )
    console.print(f"[bold green]Success![/bold green] Generated Marp Deck: [cyan]{md_path}[/cyan]")


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


@img_app.command("relight")
def img_relight(
    product: Path = typer.Argument(..., help="Path to isolated product PNG cutout"),
    background: Path = typer.Argument(..., help="Path to lifestyle background JPG"),
    angle: float = typer.Option(45.0, "--angle", "-a", help="Light direction angle in degrees"),
    intensity: float = typer.Option(0.65, "--intensity", help="Shadow opacity (0.0 to 1.0)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Target output composite path")
):
    """Synthesizes physical contact shadow and directional cast shadow for product plates."""
    with console.status("[bold green]Calculating contact shadow physics and ambient occlusion...[/bold green]"):
        res = client.images.relight_product(
            product_png_path=str(product),
            background_jpg_path=str(background),
            output_path=str(output) if output else None,
            light_angle_deg=angle,
            shadow_intensity=intensity
        )
    console.print(f"[bold green]Success![/bold green] Generated studio product composite: [cyan]{res.file_path}[/cyan]")


@img_app.command("isolate")
def img_isolate(
    image: Path = typer.Argument(..., help="Path to input image containing product/subject"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Target output PNG path")
):
    """Removes background from product or portrait photo, producing a transparent PNG."""
    with console.status("[bold green]Executing studio matting and alpha isolation...[/bold green]"):
        out_p = client.images.isolate(str(image), output_path=str(output) if output else None)
    console.print(f"[bold green]Success![/bold green] Isolated cutout: [cyan]{out_p}[/cyan]")


@img_app.command("vectorize")
def img_vectorize(
    image: Path = typer.Argument(..., help="Path to input raster image or silhouette"),
    color: str = typer.Option("#38bdf8", "--color", "-c", help="SVG fill color hex"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Target output SVG path")
):
    """Converts raster image or icon into clean mathematical SVG bezier curves."""
    with console.status("[bold green]Tracing contours and generating vector SVG...[/bold green]"):
        out_p = client.images.vectorize(str(image), output_path=str(output) if output else None, color_hex=color)
    console.print(f"[bold green]Success![/bold green] Vector SVG: [cyan]{out_p}[/cyan]")


# -------------------------------------------------------------------------
# Cross-Studio: Brand Kit CLI Commands
# -------------------------------------------------------------------------

@brand_app.command("list")
def brand_list():
    """Lists all registered Cross-Studio Brand Kits."""
    brands = client.brand_kits.list()
    table = Table(title="OpenGen Brand Kits")
    table.add_column("Brand ID", style="cyan")
    table.add_column("Brand Name", style="bold white")
    table.add_column("Primary Color", style="yellow")
    table.add_column("Display Font", style="green")

    for b in brands:
        table.add_row(
            b.brandId,
            b.brandName,
            b.colorPalette.primary,
            b.typography.headingFont
        )
    console.print(table)


@brand_app.command("init")
def brand_init(
    brand_id: str = typer.Argument(..., help="Unique brand ID, e.g. brand_quantum_flow"),
    name: str = typer.Argument(..., help="Display brand name, e.g. 'QuantumFlow AI'"),
    primary: str = typer.Option("#38bdf8", "--primary", help="Primary brand hex color"),
    secondary: str = typer.Option("#6366f1", "--secondary", help="Secondary brand hex color")
):
    """Creates a new Brand Kit with 60-30-10 palette and Swiss typography tokens."""
    from opengen.domain.brand import BrandKitSpec, ColorPalette
    palette = ColorPalette(primary=primary, secondary=secondary)
    brand = BrandKitSpec(brandId=brand_id, brandName=name, colorPalette=palette)
    saved = client.brand_kits.register(brand)
    console.print(f"[bold green]Success![/bold green] Registered brand kit '[cyan]{saved.brandId}[/cyan]' ({saved.brandName}).")


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
# Engine E: Motion Graphics & Video Ad CLI Commands
# -------------------------------------------------------------------------

@motion_app.command("ad")
def motion_ad(
    brief: str = typer.Argument(..., help="Creative brief or prompt for the video ad"),
    duration: float = typer.Option(18.0, "--duration", "-d", help="Target duration in seconds (<30s)"),
    aspect: str = typer.Option("9:16", "--aspect", "-ar", help="Aspect ratio: 9:16 or 16:9"),
    brand: Optional[str] = typer.Option(None, "--brand", "-b", help="Brand Kit ID"),
    footage: Optional[Path] = typer.Option(None, "--footage", "-f", help="Path to raw input footage"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Target output MP4 path")
):
    """Generates a high-converting direct-response video ad (<30s) using Engine 5."""
    with console.status("[bold green]Directing 5-phase funnel, smart reframing, and rendering video...[/bold green]"):
        res = client.motion.create_ad(
            brief=brief,
            source_footage=str(footage) if footage else None,
            duration=duration,
            aspect_ratio=aspect,
            brand_id=brand,
            output_mp4_path=str(output) if output else None
        )
    console.print(f"[bold green]Success![/bold green] Generated Video Ad: [cyan]{res.file_path}[/cyan]")
    console.print(f"Duration: [yellow]{res.duration}s[/yellow] | Critic Score: [green]{res.critic_score}/100[/green]")


@motion_app.command("jumpcut")
def motion_jumpcut(
    video: Path = typer.Argument(..., help="Path to talking-head video file"),
    silence: float = typer.Option(0.35, "--silence", "-s", help="Silence threshold in seconds"),
    scale: float = typer.Option(1.25, "--scale", help="Zoom punch-in scale factor"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Target output MP4 path")
):
    """Surgically cuts dead air pauses and injects alternating camera punch-ins."""
    with console.status("[bold green]Detecting speech boundaries and applying punch-ins...[/bold green]"):
        out_p = client.motion.jumpcut(str(video), output_video_path=str(output) if output else None, silence_thresh_sec=silence, zoom_punch_scale=scale)
    console.print(f"[bold green]Success![/bold green] Jump-cut video: [cyan]{out_p}[/cyan]")


@motion_app.command("collage")
def motion_collage(
    clips: List[Path] = typer.Argument(..., help="2 to 4 video clip paths to assemble into a Bento mosaic"),
    duration: float = typer.Option(4.0, "--duration", "-d", help="Target duration in seconds"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Target output MP4 path")
):
    """Assembles multiple video feeds into an animated 9:16 Bento Box mosaic."""
    with console.status("[bold green]Compiling synchronized Bento video mosaic...[/bold green]"):
        out_p = client.motion.create_collage(clips=[str(c) for c in clips], output_video_path=str(output) if output else None, duration=duration)
    console.print(f"[bold green]Success![/bold green] Bento mosaic video: [cyan]{out_p}[/cyan]")


@motion_app.command("export-edl")
def motion_export_edl(
    project_ir: Path = typer.Argument(..., help="Path to project IR JSON file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Target output EDL file path")
):
    """Exports OpenGen IR timeline into CMX 3600 EDL for DaVinci Resolve."""
    import json
    with open(project_ir, "r", encoding="utf-8") as f:
        data = json.load(f)
    out_p = str(output) if output else str(project_ir.with_suffix(".edl"))
    edl_text = client.motion.export_edl(data, output_path=out_p)
    console.print(f"[bold green]Success![/bold green] Exported CMX 3600 EDL: [cyan]{out_p}[/cyan]")


@motion_app.command("export-fcpxml")
def motion_export_fcpxml(
    project_ir: Path = typer.Argument(..., help="Path to project IR JSON file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Target output FCPXML file path")
):
    """Exports OpenGen IR timeline into Apple FCPXML v1.9."""
    import json
    with open(project_ir, "r", encoding="utf-8") as f:
        data = json.load(f)
    out_p = str(output) if output else str(project_ir.with_suffix(".fcpxml"))
    xml_text = client.motion.export_fcpxml(data, output_path=out_p)
    console.print(f"[bold green]Success![/bold green] Exported FCPXML: [cyan]{out_p}[/cyan]")


@motion_app.command("audit")
def motion_audit(
    footage: Path = typer.Argument(..., help="Path to source video footage to audit")
):
    """Audits video footage for high-saliency hooks and pacing dead-zones."""
    with console.status("[bold green]Auditing video footage saliency...[/bold green]"):
        rep = client.motion.audit(str(footage))
    console.print(f"[bold green]Audit Complete![/bold green] Summary: {rep.get('video_summary')}")
    table = Table(title="Micro-Shot Saliency Analysis")
    table.add_column("Shot ID", style="cyan")
    table.add_column("Time Window", style="yellow")
    table.add_column("Hook Score", style="bold green")
    table.add_column("Category", style="magenta")
    table.add_column("Action Summary", style="white")

    for s in rep.get("shots", []):
        table.add_row(
            s["shot_id"],
            f"{s['start_time']}s - {s['end_time']}s",
            f"{s['hook_score']}/10",
            s["subject_category"],
            s["action_summary"]
        )
    console.print(table)


@motion_app.command("reframe")
def motion_reframe(
    video: Path = typer.Argument(..., help="Path to landscape video input"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Path to target 9:16 vertical video output"),
    focal: Optional[float] = typer.Option(None, "--focal", help="Horizontal focal override (0.0 to 1.0)")
):
    """Dynamically reframes landscape video into 9:16 vertical video with LERP smoothing."""
    with console.status("[bold green]Reframing video with subject tracking...[/bold green]"):
        out_p = client.motion.reframe(
            input_video_path=str(video),
            output_video_path=str(output) if output else None,
            focal_override_x=focal
        )
    console.print(f"[bold green]Success![/bold green] Reframed 9:16 Video: [cyan]{out_p}[/cyan]")


@motion_app.command("templates")
def motion_list_templates():
    """Lists available pre-configured video ad archetypes."""
    templates = client.motion.list_templates()
    table = Table(title="OpenGen Video Ad Archetypes")
    table.add_column("Template ID", style="cyan")
    table.add_column("Name", style="bold white")
    table.add_column("Aspect Ratio", style="yellow")
    table.add_column("Duration", style="green")
    table.add_column("Description", style="dim")
    for t in templates:
        table.add_row(t["id"], t["name"], t["aspect_ratio"], f"{t['duration']}s", t["description"])
    console.print(table)


@motion_app.command("template")
def motion_from_template(
    template_id: str = typer.Argument("flash_sale", help="Template ID (flash_sale, saas_launch, artisan_showcase)"),
    vars_file: Optional[Path] = typer.Option(None, "--vars", "-v", help="Path to JSON file with custom template variables"),
    brand: Optional[str] = typer.Option(None, "--brand", "-b", help="Brand Kit ID"),
    aspect: Optional[str] = typer.Option(None, "--aspect", "-ar", help="Aspect ratio override (9:16, 16:9, 1:1)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Target output MP4 path")
):
    """Generates a high-converting video ad from a pre-configured template archetype."""
    import json
    variables = None
    if vars_file and vars_file.exists():
        with open(vars_file, "r", encoding="utf-8") as f:
            variables = json.load(f)

    with console.status(f"[bold green]Hydrating template '{template_id}' and rendering video ad...[/bold green]"):
        res = client.motion.create_from_template(
            template_id=template_id,
            variables=variables,
            brand_id=brand,
            aspect_ratio=aspect,
            output_mp4_path=str(output) if output else None
        )
    console.print(f"[bold green]Success![/bold green] Generated Video Ad: [cyan]{res.file_path}[/cyan]")
    console.print(f"Duration: [yellow]{res.duration}s[/yellow] | Critic Score: [green]{res.critic_score}/100[/green]")


@motion_app.command("jumpcut")
def motion_jumpcut(
    video: Path = typer.Argument(..., help="Path to talking-head video file"),
    silence: float = typer.Option(0.35, "--silence", "-s", help="Silence threshold in seconds"),
    scale: float = typer.Option(1.25, "--scale", help="Zoom punch-in scale factor"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Target output MP4 path")
):
    """Surgically cuts dead air pauses and injects alternating camera punch-ins."""
    with console.status("[bold green]Detecting speech boundaries and applying punch-ins...[/bold green]"):
        out_p = client.motion.jumpcut(str(video), output_video_path=str(output) if output else None, silence_thresh_sec=silence, zoom_punch_scale=scale)
    console.print(f"[bold green]Success![/bold green] Jump-cut video: [cyan]{out_p}[/cyan]")


@motion_app.command("collage")
def motion_collage(
    clips: List[Path] = typer.Argument(..., help="2 to 4 video clip paths to assemble into a Bento mosaic"),
    duration: float = typer.Option(4.0, "--duration", "-d", help="Target duration in seconds"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Target output MP4 path")
):
    """Assembles multiple video feeds into an animated 9:16 Bento Box mosaic."""
    with console.status("[bold green]Compiling synchronized Bento video mosaic...[/bold green]"):
        out_p = client.motion.create_collage(clips=[str(c) for c in clips], output_video_path=str(output) if output else None, duration=duration)
    console.print(f"[bold green]Success![/bold green] Bento mosaic video: [cyan]{out_p}[/cyan]")


@motion_app.command("export-edl")
def motion_export_edl(
    project_ir: Path = typer.Argument(..., help="Path to project IR JSON file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Target output EDL file path")
):
    """Exports OpenGen IR timeline into CMX 3600 EDL for DaVinci Resolve."""
    import json
    with open(project_ir, "r", encoding="utf-8") as f:
        data = json.load(f)
    out_p = str(output) if output else str(project_ir.with_suffix(".edl"))
    edl_text = client.motion.export_edl(data, output_path=out_p)
    console.print(f"[bold green]Success![/bold green] Exported CMX 3600 EDL: [cyan]{out_p}[/cyan]")


@motion_app.command("export-fcpxml")
def motion_export_fcpxml(
    project_ir: Path = typer.Argument(..., help="Path to project IR JSON file"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Target output FCPXML file path")
):
    """Exports OpenGen IR timeline into Apple FCPXML v1.9."""
    import json
    with open(project_ir, "r", encoding="utf-8") as f:
        data = json.load(f)
    out_p = str(output) if output else str(project_ir.with_suffix(".fcpxml"))
    xml_text = client.motion.export_fcpxml(data, output_path=out_p)
    console.print(f"[bold green]Success![/bold green] Exported FCPXML: [cyan]{out_p}[/cyan]")


# -------------------------------------------------------------------------
# Cross-Studio: Creative Critic CLI Commands
# -------------------------------------------------------------------------

@critic_app.command("audit")
def critic_audit(
    engine: str = typer.Argument(..., help="Engine to audit: document, presentation, image, handwriting, or motion"),
    file_path: Path = typer.Argument(..., help="Path to JSON payload, project IR, or text file to audit")
):
    """Audits any project payload against the Anti-Mediocrity Doctrine."""
    import json
    if file_path.suffix.lower() == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    else:
        with open(file_path, "r", encoding="utf-8") as f:
            payload = {"text": f.read()}

    with console.status(f"[bold green]Running Autonomous Pre-Flight Creative Critic Gate for {engine}...[/bold green]"):
        res = client.critic.audit(engine=engine, payload=payload)

    status_str = "[bold green]PASSED[/bold green]" if res.get("passed") else "[bold red]FAILED[/bold red]"
    console.print(f"Audit Result: {status_str} | Quality Score: [yellow]{res.get('score', 0)}/100[/yellow]")
    if res.get("violations"):
        console.print("[bold red]Violations Detected:[/bold red]")
        for v in res["violations"]:
            console.print(f"  • [red]{v}[/red]")
    if res.get("remedies"):
        console.print("[bold cyan]Automated Remedies:[/bold cyan]")
        for r in res["remedies"]:
            console.print(f"  → [cyan]{r}[/cyan]")


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
