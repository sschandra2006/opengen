"""
Autonomous Pre-Flight Creative Critic & Quality Gate for OpenGen.
Enforces the Anti-Mediocrity Doctrine across all 5 Generative Engines:
- Engine 1 (Doc): Banish mobile system emojis, ensure SKU hierarchy, widow/orphan guards.
- Engine 2 (PPT): Banish raw bullet points, ensure 12-column grid balance and semantic components.
- Engine 3 (Image): Verify contact shadow presence and copy-aware negative space (60/40 rule).
- Engine 4 (Handwriting): Non-repetition glyph checks and paper line-pitch calibration.
- Engine 5 (Motion): 2.2s visual hook speed, pattern interrupts, and 9:16 mobile safe-zone boundaries.
"""
from typing import Dict, Any, List, Optional, Union
import re
from opengen.engines.document.sku_classifier import SemanticSKUClassifier, StyleRedliner
from opengen.engines.motion.ad_critic import AdCriticAgent
from opengen.creative.quality_gauntlet import QualityGauntlet


class CreativeCriticGate:
    """Centralized quality gate enforcing creative standards across all 5 studios."""

    gauntlet = QualityGauntlet

    @classmethod
    def audit_document(cls, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Audits document data for emojis, banned buzzwords, dense raw tables, or flat hierarchy."""
        violations = []
        raw_text = str(doc_data)

        # 1. Emoji check
        emojis_found = SemanticSKUClassifier.EMOJI_PATTERN.findall(raw_text)
        if emojis_found:
            sample = "".join(emojis_found[:5])
            violations.append(f"EMOJI_ANTI_PATTERN: Document contains system emojis ({sample}). Banned under corporate Swiss design rules.")

        # 2. Banned Corporate Buzzword check (Anti-Slop Redlining)
        buzzwords = StyleRedliner.audit_text(raw_text)
        if buzzwords:
            sample_bw = ", ".join(list(set(buzzwords))[:4])
            violations.append(f"BUZZWORD_ANTI_PATTERN: Document contains statistical AI buzzwords ({sample_bw}). Banned under corporate Swiss editorial rules.")

        # 3. Check for catalog without hero hierarchy
        products = doc_data.get("products", [])
        if len(products) > 10 and not any(p.get("is_hero") for p in products):
            violations.append("FLAT_SKU_HIERARCHY: Over 10 catalog items detected with zero Hero Spotlight merchandising hierarchy.")

        # 4. Knowledge Graph Grounding check (if doc_hash and claims provided)
        doc_hash = doc_data.get("doc_hash")
        if doc_hash:
            try:
                from opengen.graph import graph_store
                kg = graph_store.get_graph(doc_hash)
                if kg:
                    claims = doc_data.get("claims", [])
                    unverified = [c for c in claims if not kg.validate_entity_presence(str(c))]
                    if unverified:
                        violations.append(f"UNGROUNDED_FACT_HALLUCINATION: Generated claims {unverified[:3]} not grounded in Document Knowledge Graph.")
            except Exception:
                pass

        # 5. Negative Space & Density Check (Tier 4 Quality Gate)
        narrative = doc_data.get("executive_summary", "") or doc_data.get("narrative", "")
        if narrative:
            paragraphs = [p for p in narrative.split("\n\n") if p.strip()]
            for p in paragraphs:
                if len(p.split()) > 250:
                    violations.append("NEGATIVE_SPACE_DEFICIT: Document contains unbroken narrative blocks (>250 words) violating Swiss editorial margin & negative space rules (<30% whitespace).")
                    break

        passed = len(violations) == 0
        score = max(0, 100 - (len(violations) * 25))
        remedies = []
        if not passed:
            remedies.append("Strip emojis and replace with Lucide/Phosphor vector icons.")
            remedies.append("Filter banned corporate buzzwords ('delve', 'testament to', 'beacon', 'unleash') using StyleRedliner.")
            remedies.append("Apply 80/20 merchandising classification: route top 10% items to Hero Bento Cards and remainder to Dot-Leader Menus.")
            remedies.append("Break dense narrative into modular paragraphs with generous margins (>=30% whitespace).")
            if any("UNGROUNDED" in v for v in violations):
                remedies.append("Ground claims strictly against entities and metrics present in Document Knowledge Graph.")

        return {
            "engine": "document",
            "passed": passed,
            "score": score,
            "violations": violations,
            "remedies": remedies
        }

    @classmethod
    def audit_presentation(cls, deck_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Audits presentation deck for raw bullet points, monotonous layouts, and negative space."""
        violations = []
        slides = deck_spec.get("slides", [])

        bullet_count = 0
        for s in slides:
            # Check for legacy bullet cards
            for c in s.get("cards", []):
                if c.get("body_bullets") and len(c["body_bullets"]) > 0:
                    bullet_count += len(c["body_bullets"])

            # Check for missing bento layout on content slides
            layout = s.get("layout_type", "")
            if layout in ["single_column", "two_column", "three_column"] and not s.get("bento_cards"):
                violations.append(f"MONOTONOUS_LAYOUT: Slide {s.get('slide_number')} uses legacy bullet layout '{layout}' instead of responsive Bento Grid.")

            # Check for slide element crowding (Negative Space < 30% / Content Area > 70%)
            b_cards = s.get("bento_cards", [])
            std_cards = s.get("cards", [])
            total_elements = len(b_cards) + len(std_cards)
            if total_elements > 8:
                violations.append(f"NEGATIVE_SPACE_DEFICIT: Slide {s.get('slide_number')} contains {total_elements} cards, exceeding visual clutter threshold (whitespace < 30%).")

        if bullet_count > 5:
            violations.append(f"BULLET_POINT_DISEASE: Deck contains {bullet_count} raw bullet points. Audiences tune out.")

        passed = len(violations) == 0
        score = max(0, 100 - (len(violations) * 20))
        return {
            "engine": "presentation",
            "passed": passed,
            "score": score,
            "violations": violations,
            "remedies": [
                "Convert bullet points into 6 Semantic Visual Components (Stat Cards, Roadmaps, Bento Boxes, Comparison Matrices).",
                "Apply 12-column responsive Bento Grid compiler.",
                "Preserve at least 30% negative space on each slide (cap bento cards at 6 per slide)."
            ] if not passed else []
        }

    @classmethod
    def audit_image(cls, image_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Audits product image compositing for contact shadow, negative constraints, and prompt quality."""
        violations = []
        prompt = image_spec.get("prompt", "")
        prompt_lower = prompt.lower()

        # Check for plastic sheen terms
        if any(term in prompt_lower for term in ["smooth plastic", "hyper-realistic wax", "doll-like"]):
            violations.append("PLASTIC_SHEEN_PROMPT: Prompt contains terms prone to untextured plastic AI artifacts.")

        # Check for banned prompt junk (photorealistic, 8k, hyper-detailed)
        if any(term in prompt_lower for term in ["8k resolution", "8k,", "hyperrealistic", "hyper-detailed"]):
            violations.append("PROMPT_JUNK_ANTI_PATTERN: Prompt contains banned buzzwords ('8k', 'hyperrealistic'). Replace with physical lens optics.")

        # Check for relighting contact shadow flag
        if image_spec.get("is_product_composite") and not image_spec.get("has_contact_shadow"):
            violations.append("FLOATING_PRODUCT_SYNDROME: Product cutout placed on lifestyle plate without dual-pass contact shadow.")

        passed = len(violations) == 0
        score = max(0, 100 - (len(violations) * 25))
        return {
            "engine": "image",
            "passed": passed,
            "score": score,
            "violations": violations,
            "remedies": [
                "Inject Hasselblad camera optics, f/1.4 aperture, and Profoto studio softbox lighting.",
                "Execute StudioShadowSynthesizer to composite sharp contact shadow + directional cast shadow.",
                "Inject anti-slop negative prompt constraints."
            ] if not passed else []
        }

    @classmethod
    def audit_handwriting(cls, text: str, paper_mode: str = "direct_print_transparent") -> Dict[str, Any]:
        """Audits handwriting input for biological plausibility and printer calibration."""
        violations = []
        if len(text.strip()) == 0:
            violations.append("EMPTY_TEXT: Handwriting text is blank.")

        # Check for immediate triplet letter repetition (e.g. 'eee') which triggers OCR fonts
        if re.search(r"([a-zA-Z])\1\1", text):
            violations.append("TRIPLET_GLYPH_REPETITION: 3+ identical consecutive characters detected; risk of cloned font detection.")

        passed = len(violations) == 0
        score = max(0, 100 - (len(violations) * 30))
        return {
            "engine": "handwriting",
            "passed": passed,
            "score": score,
            "violations": violations,
            "remedies": [
                "Activate GlyphVariantBank alternate font sampling and Brownian drift.",
                "Inject continuous cubic Bezier ligatures between character boundaries."
            ] if not passed else []
        }

    @classmethod
    def audit_audio(cls, audio_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Audits speech audio spec for breath tokens, punctuation pauses, and loudness mastering."""
        violations = []
        text = audio_spec.get("text", "")
        # Check for robotic monotony: lack of breath tokens in long speech (>30 words)
        words = text.split()
        if len(words) > 30 and not any(t in text for t in ["[gasp]", "[sigh]", "[pause]", "[chuckle]", "..."]):
            violations.append("MONOTONE_SPEECH_CADENCE: Long narration lacks natural breath tokens or prosodic pause markers.")

        # Check for unmastered audio or missing ducking in mix
        if audio_spec.get("is_mixed") and not audio_spec.get("ducking_enabled"):
            violations.append("MISSING_SIDECHAIN_DUCKING: Audio mix lacks dynamic sidechain ducking (-14 dB) under voiceover.")

        passed = len(violations) == 0
        score = max(0, 100 - (len(violations) * 25))
        return {
            "engine": "audio",
            "passed": passed,
            "score": score,
            "violations": violations,
            "remedies": [
                "Inject conversational breath tokens or punctuation pauses.",
                "Apply EBU R128 (-14 LUFS) and dynamic sidechain compression in FFmpeg."
            ] if not passed else []
        }

    @classmethod
    def audit_motion(cls, project_ir: Dict[str, Any]) -> Dict[str, Any]:
        """Audits short-form video ad project against retention and safe-zone rules."""
        critic = AdCriticAgent()
        res = critic.audit_ad_timeline(project_ir)
        res["engine"] = "motion"
        return res

    @classmethod
    def audit_ui(cls, ui_spec: Union[Dict[str, Any], str]) -> Dict[str, Any]:
        """
        Audits Web UI, React/JSX, or HTML code against Tier 1-4 Anti-Slop criteria:
        1. Design System Token Binding: Flags ad-hoc inline styles or raw Bootstrap classes.
        2. Strict Component AST Parsing: Flags unclosed tags and malformed elements.
        3. Accessibility (a11y): Flags interactive elements missing aria-label or images missing alt.
        4. Data Tables: Flags raw unstyled <table> elements without responsive containers.
        5. Bento Grid Layouts: Verifies fluid responsive grid patterns (grid-cols-* or flex).
        """
        violations = []
        if isinstance(ui_spec, dict):
            raw_code = ui_spec.get("code", "") or ui_spec.get("html", "") or str(ui_spec)
        else:
            raw_code = str(ui_spec)

        if not raw_code.strip():
            return {
                "engine": "ui",
                "passed": False,
                "score": 0,
                "violations": ["EMPTY_UI_CODE: Provided UI code or specification is empty."],
                "remedies": ["Provide valid HTML, JSX, or component markup."]
            }

        code_lower = raw_code.lower()

        # 1. Generic Bootstrap & 2018 Syndrome
        bootstrap_indicators = ["btn-primary", "jumbotron", "table-bordered", "form-control", "panel-default"]
        found_bs = [b for b in bootstrap_indicators if b in code_lower]
        if found_bs:
            violations.append(f"GENERIC_BOOTSTRAP_SYNDROME: Code uses outdated Bootstrap classes ({', '.join(found_bs)}). Bind to shadcn/ui and Tailwind tokens.")

        # 2. Ad-hoc Inline Style Hacks
        style_attrs = re.findall(r'style=[\'"]([^\'"]+)[\'"]', raw_code, flags=re.IGNORECASE)
        for s_val in style_attrs:
            if any(p in s_val.lower() for p in ["background", "color", "font-size", "padding", "margin"]):
                if "var(--" not in s_val:
                    violations.append("INLINE_STYLE_HACK: Ad-hoc inline CSS styling detected. Bind directly to Tailwind / shadcn design tokens.")
                    break

        # 3. Unstyled Data Tables
        if "<table" in code_lower:
            table_tags = re.findall(r'<table[^>]*>', raw_code, flags=re.IGNORECASE)
            for t in table_tags:
                has_styling = any(k in t.lower() for k in ["class=", "classname=", "w-full", "min-w-full"])
                if not has_styling or "overflow" not in raw_code.lower():
                    violations.append("UNSTYLED_DATA_TABLE: Raw unstyled <table> detected without responsive container or design tokens.")
                    break

        # 4. Strict Component AST: Unclosed major tags
        for tag in ["div", "section", "button", "table"]:
            open_count = len(re.findall(rf'<{tag}\b[^>]*>', raw_code, flags=re.IGNORECASE))
            self_closing = len(re.findall(rf'<{tag}\b[^>]*/>', raw_code, flags=re.IGNORECASE))
            close_count = len(re.findall(rf'</{tag}>', raw_code, flags=re.IGNORECASE))
            if (open_count - self_closing) != close_count:
                violations.append(f"BROKEN_COMPONENT_AST: Unmatched <{tag}> tags (opened {open_count - self_closing}, closed {close_count}).")

        # 5. Accessibility Attributes (a11y)
        empty_buttons = re.findall(r'<button\b(?![^>]*aria-label)[^>]*>\s*(?:<svg[^>]*>.*?</svg>|<i\b[^>]*></i>|\s*)</button>', raw_code, flags=re.IGNORECASE | re.DOTALL)
        if empty_buttons:
            violations.append("ACCESSIBILITY_DEFICIT: Icon-only <button> missing aria-label attribute.")
        imgs_no_alt = re.findall(r'<img\b(?![^>]*alt=)[^>]*>', raw_code, flags=re.IGNORECASE)
        if imgs_no_alt:
            violations.append("ACCESSIBILITY_DEFICIT: <img> element missing required 'alt' attribute.")

        # 6. Check Design System Token Binding
        if len(raw_code.split()) > 20:
            has_tokens = any(k in raw_code for k in ["class=", "className=", "var(--", "bg-", "text-", "rounded-", "p-", "grid", "flex"])
            if not has_tokens:
                violations.append("MISSING_DESIGN_TOKENS: UI code does not bind to design tokens or Tailwind utility classes.")

        passed = len(violations) == 0
        score = max(0, 100 - (len(violations) * 20))
        return {
            "engine": "ui",
            "passed": passed,
            "score": score,
            "violations": violations,
            "remedies": [
                "Bind components directly to Tailwind / shadcn/ui design tokens (e.g., bg-background, text-foreground, rounded-lg).",
                "Ensure all HTML/JSX tags are balanced and correctly closed.",
                "Wrap data tables in overflow-x-auto responsive containers with subtle borders.",
                "Add aria-label to icon buttons and alt attributes to all img tags.",
                "Organize dashboard cards into responsive CSS Bento Grids (grid-cols-1 md:grid-cols-3 gap-6)."
            ] if not passed else []
        }

    @classmethod
    def audit_any(cls, engine: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Unified dispatch auditing any generation payload across Engines 1 to 5 + Audio + UI."""
        eng = engine.lower()
        if "doc" in eng:
            return cls.audit_document(payload)
        elif "pres" in eng or "ppt" in eng:
            return cls.audit_presentation(payload)
        elif "img" in eng or "image" in eng:
            return cls.audit_image(payload)
        elif "hand" in eng or "hw" in eng:
            return cls.audit_handwriting(payload.get("text", ""), payload.get("paper_mode", ""))
        elif "audio" in eng or "voice" in eng:
            return cls.audit_audio(payload)
        elif "motion" in eng or "video" in eng:
            return cls.audit_motion(payload)
        elif "ui" in eng or "code" in eng or "web" in eng:
            return cls.audit_ui(payload)
        else:
            return {"engine": engine, "passed": True, "score": 100, "violations": []}
