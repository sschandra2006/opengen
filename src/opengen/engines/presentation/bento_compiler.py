"""
Gamma-Style Bento Slide Compiler for Engine 2 (Presentation Studio).
Renders responsive 1920x1080 12-column CSS Grid presentations,
curing the "bullet point disease" with semantic visual bento containers.
"""
from typing import List, Optional, Dict, Any
from pathlib import Path
from opengen.domain.presentation import PresentationDeckSpec, SlideSpec, BentoCardSpec
from opengen.domain.brand import BrandKitSpec
from opengen.brand.resolver import BrandKitTokenResolver


class BentoSlideCompiler:
    """Compiles presentation decks into Gamma-style fluid Bento Grid HTML slides."""

    @classmethod
    def render_slide_html(
        cls,
        slide: SlideSpec,
        brand: Optional[BrandKitSpec] = None,
        slide_index: int = 1,
        total_slides: int = 1
    ) -> str:
        """Renders an individual 16:9 widescreen Bento slide (1920x1080)."""
        p_primary = brand.colorPalette.primary if brand else "#38bdf8"
        p_bg = brand.colorPalette.backgroundDark if brand else "#090d16"
        p_surface = brand.colorPalette.surfaceCard if brand else "#131b2e"
        p_text_high = brand.colorPalette.textHighContrast if brand else "#ffffff"
        p_text_muted = brand.colorPalette.textMuted if brand else "#94a3b8"
        p_border = brand.colorPalette.borderSubtle if brand else "#1e293b"
        p_success = brand.colorPalette.accentSuccess if brand else "#10b981"
        font_header = brand.typography.headingFont if brand else "Plus Jakarta Sans"
        font_body = brand.typography.bodyFont if brand else "Inter"

        # Cards markup
        cards_html = []
        l_type = getattr(slide, "layout_type", "")

        if l_type == "roadmap_timeline" and slide.bento_cards:
            # Semantic Component: Horizontal Roadmap Timeline
            step_cards = []
            for idx, c in enumerate(slide.bento_cards, start=1):
                accent = c.accent_color or p_primary
                step_cards.append(f"""
                <div class="bento-card col-4 timeline-step" style="border-left: 4px solid {accent};">
                  <div class="step-num" style="color: {accent};">STEP 0{idx}</div>
                  <div class="card-title">{c.title}</div>
                  <div class="card-desc">{c.description}</div>
                </div>
                """)
            cards_body = "\n".join(step_cards)

        elif l_type == "comparison_matrix" and len(slide.bento_cards) >= 2:
            # Semantic Component: Side-by-Side Comparison Matrix
            old_card = slide.bento_cards[0]
            new_card = slide.bento_cards[1]
            cards_body = f"""
            <div class="bento-card col-6 comparison-legacy" style="border-top: 4px solid #ef4444; background: rgba(239, 68, 68, 0.05);">
              <div class="matrix-badge" style="color: #ef4444;">THE LEGACY WAY</div>
              <div class="card-title" style="color: #fca5a5;">{old_card.title}</div>
              <div class="card-desc">{old_card.description}</div>
            </div>
            <div class="bento-card col-6 comparison-modern" style="border-top: 4px solid {p_primary}; background: rgba(56, 189, 248, 0.08);">
              <div class="matrix-badge" style="color: {p_primary};">THE OPENGEN WAY</div>
              <div class="card-title" style="color: #ffffff;">{new_card.title}</div>
              <div class="card-desc">{new_card.description}</div>
            </div>
            """

        elif slide.bento_cards:
            for c in slide.bento_cards:
                accent = c.accent_color or p_primary
                metric_div = f'<div class="card-metric" style="color: {accent};">{c.value}</div>' if c.value else ""
                trend_div = f'<div class="card-trend" style="color: {p_success};">{c.trend_badge}</div>' if c.trend_badge else ""
                col_cls = f"col-{c.col_span}"
                cards_html.append(f"""
                <div class="bento-card {col_cls}" style="border-top: 3px solid {accent};">
                  {metric_div}
                  <div class="card-title">{c.title}</div>
                  <div class="card-desc">{c.description}</div>
                  {trend_div}
                </div>
                """)
            cards_body = "\n".join(cards_html)
        elif slide.cards:
            # Fallback for standard cards
            span = max(3, 12 // max(1, len(slide.cards)))
            for c in slide.cards:
                b_text = "".join([f"<p>• {b}</p>" for b in c.body_bullets])
                cards_html.append(f"""
                <div class="bento-card col-{span}" style="border-top: 3px solid {p_primary};">
                  <div class="card-title">{c.title or 'Key Point'}</div>
                  <div class="card-desc">{b_text}</div>
                </div>
                """)
            cards_body = "\n".join(cards_html)
        else:
            cards_body = ""
        stage_badge = f'<span class="stage-badge">{slide.narrative_stage.upper()}</span>' if slide.narrative_stage else ""

        return f"""
        <div class="slide-container" id="slide-{slide.slide_number}">
          <div class="slide-header">
            <div class="header-top">
              {stage_badge}
              <span class="slide-counter">Slide {slide_index} of {total_slides}</span>
            </div>
            <h1 class="slide-title">{slide.title}</h1>
            {f'<p class="slide-subtitle">{slide.subtitle}</p>' if slide.subtitle else ''}
          </div>
          <div class="bento-grid">
            {cards_body}
          </div>
        </div>
        """

    @classmethod
    def render_deck_html(
        cls,
        deck: PresentationDeckSpec,
        brand: Optional[BrandKitSpec] = None
    ) -> str:
        """Renders the entire presentation as an interactive multi-slide HTML bundle."""
        p_bg = brand.colorPalette.backgroundDark if brand else "#090d16"
        p_surface = brand.colorPalette.surfaceCard if brand else "#131b2e"
        p_border = brand.colorPalette.borderSubtle if brand else "#1e293b"
        p_primary = brand.colorPalette.primary if brand else "#38bdf8"
        font_header = brand.typography.headingFont if brand else "Plus Jakarta Sans"
        font_body = brand.typography.bodyFont if brand else "Inter"

        slides_html = []
        total = len(deck.slides)
        for idx, slide in enumerate(deck.slides, start=1):
            slides_html.append(cls.render_slide_html(slide, brand, idx, total))

        deck_body = "\n".join(slides_html)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{deck.topic} — OpenGen Bento Presentation</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Plus+Jakarta+Sans:wght@700;800;900&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: {p_bg};
      color: #ffffff;
      font-family: '{font_body}', sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 40px;
      padding: 40px 0;
    }}
    .slide-container {{
      width: 1920px;
      height: 1080px;
      background: {p_bg};
      border: 1px solid {p_border};
      padding: 90px 100px;
      display: flex;
      flex-direction: column;
      position: relative;
      box-shadow: 0 20px 50px rgba(0,0,0,0.5);
    }}
    .slide-header {{
      margin-bottom: 50px;
    }}
    .header-top {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }}
    .stage-badge {{
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 1.5px;
      color: {p_primary};
      background: rgba(56, 189, 248, 0.1);
      padding: 4px 12px;
      border-radius: 6px;
      border: 1px solid rgba(56, 189, 248, 0.2);
    }}
    .slide-counter {{
      font-size: 14px;
      color: #64748b;
    }}
    .slide-title {{
      font-family: '{font_header}', sans-serif;
      font-size: 52px;
      font-weight: 800;
      color: #ffffff;
      line-height: 1.15;
      margin-bottom: 12px;
    }}
    .slide-subtitle {{
      font-size: 22px;
      color: #94a3b8;
      max-width: 1200px;
      line-height: 1.4;
    }}
    .bento-grid {{
      display: grid;
      grid-template-columns: repeat(12, 1fr);
      gap: 28px;
      flex-grow: 1;
    }}
    .bento-card {{
      background: {p_surface};
      border-radius: 16px;
      padding: 36px;
      border: 1px solid {p_border};
      display: flex;
      flex-direction: column;
      justify-content: flex-start;
      transition: transform 0.2s;
    }}
    .col-3 {{ grid-column: span 3; }}
    .col-4 {{ grid-column: span 4; }}
    .col-6 {{ grid-column: span 6; }}
    .col-8 {{ grid-column: span 8; }}
    .col-12 {{ grid-column: span 12; }}
    .card-metric {{
      font-family: '{font_header}', sans-serif;
      font-size: 56px;
      font-weight: 900;
      line-height: 1.0;
      margin-bottom: 12px;
    }}
    .card-title {{
      font-family: '{font_header}', sans-serif;
      font-size: 22px;
      font-weight: 700;
      color: #f8fafc;
      margin-bottom: 10px;
    }}
    .card-desc {{
      font-size: 16px;
      color: #94a3b8;
      line-height: 1.5;
      flex-grow: 1;
    }}
    .card-trend {{
      font-size: 14px;
      font-weight: 600;
      margin-top: 14px;
    }}
  </style>
</head>
<body>
  {deck_body}
</body>
</html>
"""

    @classmethod
    def compile_deck_to_html_file(
        cls,
        deck: PresentationDeckSpec,
        output_html_path: str,
        brand: Optional[BrandKitSpec] = None
    ) -> str:
        """Saves compiled Bento HTML deck to disk."""
        out_path = Path(output_html_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        html_content = cls.render_deck_html(deck, brand)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return str(out_path)
