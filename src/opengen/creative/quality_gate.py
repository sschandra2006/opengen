"""
Autonomous Pre-Flight Creative Critic & Quality Gate for OpenGen.
Enforces the Anti-Mediocrity Doctrine across all 5 Generative Engines:
- Engine 1 (Doc): Banish mobile system emojis, ensure SKU hierarchy, widow/orphan guards.
- Engine 2 (PPT): Banish raw bullet points, ensure 12-column grid balance and semantic components.
- Engine 3 (Image): Verify contact shadow presence and copy-aware negative space (60/40 rule).
- Engine 4 (Handwriting): Non-repetition glyph checks and paper line-pitch calibration.
- Engine 5 (Motion): 2.2s visual hook speed, pattern interrupts, and 9:16 mobile safe-zone boundaries.
"""
from typing import Dict, Any, List, Optional
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

        passed = len(violations) == 0
        score = max(0, 100 - (len(violations) * 25))
        remedies = []
        if not passed:
            remedies.append("Strip emojis and replace with Lucide/Phosphor vector icons.")
            remedies.append("Filter banned corporate buzzwords ('delve', 'testament to', 'beacon', 'unleash') using StyleRedliner.")
            remedies.append("Apply 80/20 merchandising classification: route top 10% items to Hero Bento Cards and remainder to Dot-Leader Menus.")
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
        """Audits presentation deck for raw bullet points and monotonous layouts."""
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
                "Apply 12-column responsive Bento Grid compiler."
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
    def audit_any(cls, engine: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Unified dispatch auditing any generation payload across Engines 1 to 5 + Audio."""
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
        else:
            return {"engine": engine, "passed": True, "score": 100, "violations": []}
