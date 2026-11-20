"""
Marp Core & Slidev AST Presentation Compiler (Engine 2 Ecosystem Adapter).
Adapted from Marp Core and Slidev:
Compiles PresentationDeckSpec and Bento grid layouts into standardized,
developer-friendly Marp Markdown decks (.md) for instant VS Code preview or PDF rendering.
"""
from typing import Dict, Any, List, Optional
from pathlib import Path
from opengen.domain.presentation import PresentationDeckSpec, SlideSpec
from opengen.domain.brand import BrandKitSpec


class MarpSlideCompiler:
    """Compiles native presentation specifications into Marp Markdown."""

    @classmethod
    def compile_deck_to_markdown(
        cls,
        deck: PresentationDeckSpec,
        output_md_path: Optional[str] = None,
        brand: Optional[BrandKitSpec] = None
    ) -> str:
        """
        Compiles PresentationDeckSpec into Marp-compatible Markdown.
        """
        bg_dark = brand.colorPalette.backgroundDark if brand else "#090d16"
        card_bg = brand.colorPalette.surfaceCard if brand else "#131b2e"
        primary = brand.colorPalette.primary if brand else "#38bdf8"
        font_family = brand.typography.headingFont if brand else "Plus Jakarta Sans"

        lines = [
            "---",
            "marp: true",
            "theme: gaia",
            "_class: lead",
            "paginate: true",
            f"backgroundColor: '{bg_dark}'",
            "color: '#f8fafc'",
            "style: |",
            f"  section {{",
            f"    font-family: '{font_family}', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;",
            f"    padding: 40px;",
            f"    background-color: {bg_dark};",
            f"  }}",
            f"  .card {{",
            f"    background-color: {card_bg};",
            f"    border: 1px solid rgba(255, 255, 255, 0.08);",
            f"    border-radius: 12px;",
            f"    padding: 20px;",
            f"    margin-bottom: 12px;",
            f"  }}",
            f"  .accent {{",
            f"    color: {primary};",
            f"    font-weight: 700;",
            f"  }}",
            "---",
            ""
        ]

        for idx, slide in enumerate(deck.slides):
            if idx > 0:
                lines.append("\n---\n")

            title = slide.title or f"Slide {idx + 1}"
            subtitle = slide.subtitle or ""

            lines.append(f"# {title}")
            if subtitle:
                lines.append(f'<span class="accent">{subtitle}</span>\n')

            # Render bento cards or standard cards
            cards = slide.bento_cards or slide.cards or []
            if cards:
                for c in cards:
                    if isinstance(c, dict):
                        c_title = c.get("card_title") or c.get("title") or ""
                        c_body = c.get("body_text") or c.get("body") or c.get("description") or ""
                        c_stat = c.get("stat_callout") or c.get("metric") or c.get("value") or ""
                    else:
                        c_title = getattr(c, "card_title", None) or getattr(c, "title", None) or ""
                        c_body = getattr(c, "body_text", None) or getattr(c, "body", None) or getattr(c, "description", None) or ""
                        c_stat = getattr(c, "stat_callout", None) or getattr(c, "metric", None) or getattr(c, "value", None) or ""

                    lines.append('<div class="card">')
                    if c_stat:
                        lines.append(f'  <h2 class="accent">{c_stat}</h2>')
                    if c_title:
                        lines.append(f'  <h3>{c_title}</h3>')
                    if c_body:
                        lines.append(f'  <p>{c_body}</p>')
                    lines.append('</div>')
            elif slide.body_paragraphs:
                for p in slide.body_paragraphs:
                    lines.append(f"\n{p}")

        md_content = "\n".join(lines)

        if output_md_path:
            out_p = Path(output_md_path).resolve()
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(md_content, encoding="utf-8")

        return md_content
