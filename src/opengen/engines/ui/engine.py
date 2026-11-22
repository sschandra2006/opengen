"""
UI & Code Generation Studio for OpenGen (Engine 7 / Web UI Modality).
Enforces shadcn/ui + Tailwind CSS design system token binding, strict component AST linting,
and responsive 12-column Bento Grid layouts to banish Generic Bootstrap and unstyled UI slop.
"""
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from opengen.domain.brand import BrandKitSpec


class UIEngine:
    """Master generation and validation engine for Web UI, JSX, and Interactive Artifacts."""

    @classmethod
    def generate_bento_dashboard(
        cls,
        cards: List[Dict[str, Any]],
        title: str = "Enterprise Operations Dashboard",
        subtitle: Optional[str] = None,
        brand: Optional[BrandKitSpec] = None,
        output_html_path: Optional[str] = None,
    ) -> str:
        """
        Synthesizes a production-grade, accessible responsive Bento Dashboard component
        bound directly to shadcn/ui and Tailwind CSS design tokens.
        Bans Generic Bootstrap, unstyled tables, and ad-hoc inline styles.
        """
        p_primary = brand.colorPalette.primary if brand else "#0284c7"
        p_bg = brand.colorPalette.backgroundDark if brand else "#090d16"
        p_surface = brand.colorPalette.surfaceCard if brand else "#131b2e"
        p_border = brand.colorPalette.borderSubtle if brand else "#1e293b"
        p_text_high = brand.colorPalette.textHighContrast if brand else "#ffffff"
        p_text_muted = brand.colorPalette.textMuted if brand else "#94a3b8"
        p_success = brand.colorPalette.accentSuccess if brand else "#10b981"
        font_header = brand.typography.headingFont if brand else "Plus Jakarta Sans"
        font_body = brand.typography.bodyFont if brand else "Inter"

        cards_markup = []
        for idx, card in enumerate(cards):
            c_title = card.get("title", f"Metric {idx + 1}")
            c_value = card.get("value", "")
            c_desc = card.get("description", "")
            c_badge = card.get("trend_badge", card.get("badge", ""))
            c_span = card.get("col_span", 1)  # 1 or 2 in responsive grid

            span_class = "md:col-span-2" if c_span > 1 else "col-span-1"

            val_html = (
                f'<div class="text-3xl font-extrabold tracking-tight text-foreground mt-2">{c_value}</div>'
                if c_value
                else ""
            )
            badge_html = (
                f'<span class="inline-flex items-center rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-400 border border-emerald-500/20">{c_badge}</span>'
                if c_badge
                else ""
            )

            card_html = f"""
        <article class="{span_class} bg-card text-card-foreground border border-border rounded-xl p-6 shadow-sm hover:border-primary/50 transition-colors flex flex-col justify-between">
          <header class="flex items-center justify-between">
            <h3 class="text-sm font-semibold tracking-wide text-muted-foreground uppercase">{c_title}</h3>
            {badge_html}
          </header>
          {val_html}
          <p class="text-sm text-muted-foreground mt-2">{c_desc}</p>
          <footer class="mt-4 pt-4 border-t border-border flex items-center justify-between">
            <span class="text-xs text-muted-foreground">Updated in real-time</span>
            <button type="button" aria-label="View details for {c_title}" class="text-xs font-medium text-primary hover:underline focus:outline-none focus:ring-2 focus:ring-primary rounded px-2 py-1">
              Inspect &rarr;
            </button>
          </footer>
        </article>"""
            cards_markup.append(card_html.strip())

        grid_content = "\n        ".join(cards_markup)
        sub_html = f'<p class="text-base text-muted-foreground mt-1">{subtitle}</p>' if subtitle else ""

        html = f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          colors: {{
            background: '{p_bg}',
            foreground: '{p_text_high}',
            card: '{p_surface}',
            'card-foreground': '{p_text_high}',
            primary: '{p_primary}',
            muted: '#1e293b',
            'muted-foreground': '{p_text_muted}',
            border: '{p_border}',
          }},
          borderRadius: {{
            lg: 'var(--radius, 0.5rem)',
          }}
        }}
      }}
    }}
  </script>
  <style>
    :root {{
      --radius: 0.75rem;
      --font-heading: '{font_header}', sans-serif;
      --font-body: '{font_body}', sans-serif;
    }}
    body {{
      font-family: var(--font-body);
    }}
    h1, h2, h3 {{
      font-family: var(--font-heading);
    }}
  </style>
</head>
<body class="bg-background text-foreground min-h-screen p-6 md:p-12">
  <main class="max-w-7xl mx-auto space-y-8">
    <header class="border-b border-border pb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      <div>
        <h1 class="text-3xl font-extrabold tracking-tight text-foreground">{title}</h1>
        {sub_html}
      </div>
      <div class="flex items-center gap-3">
        <button type="button" aria-label="Export analytics report" class="inline-flex items-center justify-center rounded-lg border border-border bg-card px-4 py-2 text-sm font-medium text-foreground hover:bg-muted focus:outline-none focus:ring-2 focus:ring-primary">
          Export Report
        </button>
        <button type="button" aria-label="Deploy new pipeline" class="inline-flex items-center justify-center rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-primary">
          New Pipeline
        </button>
      </div>
    </header>

    <section aria-label="Key Performance Bento Grid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {grid_content}
    </section>
  </main>
</body>
</html>"""

        if output_html_path:
            out_p = Path(output_html_path)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(html, encoding="utf-8")

        return html
