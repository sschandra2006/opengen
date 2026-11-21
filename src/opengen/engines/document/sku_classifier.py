"""
Semantic SKU Classifier and Merchandising Hierarchy Engine for Engine 1 (Document Studio).
Applies the 80/20 merchandising rule to catalog generation:
- Top 10% Signature Products -> Hero Spotlight Bento Cards (photography, tasting notes, high price prominence)
- Routine Products -> Elegant Dot-Leader Menus (. . . . . . ₹373) instead of rigid tables.
- Strict Emoji Ban: Strips system emojis and replaces them with monochromatic vector icon tokens.
"""
import re
from typing import List, Dict, Any, Tuple


class StyleRedliner:
    """Enforces Tier 1 negative style constraints across generated document text."""

    BANNED_BUZZWORDS = [
        r"\bdelve\b",
        r"\btestament to\b",
        r"\bbeacon\b",
        r"\bunleash(?:ing|ed|es)?\b",
        r"\btapestry\b",
        r"\bgame-?changer\b",
        r"\bplethora\b",
        r"\bsynerg(?:y|ies|istic)\b",
        r"\btransformative\b",
        r"\bgroundbreaking\b",
        r"\bunlocking\b",
        r"\bpinnacle\b",
    ]

    BUZZWORD_PATTERN = re.compile("|".join(BANNED_BUZZWORDS), flags=re.IGNORECASE)

    @classmethod
    def audit_text(cls, text: str) -> List[str]:
        """Detects banned buzzwords in text."""
        return cls.BUZZWORD_PATTERN.findall(text)

    @classmethod
    def redline_text(cls, text: str, replacement: str = "") -> str:
        """Removes or cleanses banned buzzwords and emojis from text."""
        clean = SemanticSKUClassifier.EMOJI_PATTERN.sub("", text)
        clean = cls.BUZZWORD_PATTERN.sub(replacement, clean)
        return " ".join(clean.split())


class SemanticSKUClassifier:
    """Classifies catalog SKUs into merchandising tiers and sanitizes iconography."""

    EMOJI_PATTERN = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-a
        "]+",
        flags=re.UNICODE
    )

    CATEGORY_ICON_MAP = {
        "milk": "droplet",
        "curd": "bowl",
        "ghee": "flame",
        "butter": "sparkles",
        "paneer": "box",
        "sweets": "star",
        "bakery": "wheat",
        "beverage": "coffee",
        "default": "tag"
    }

    @classmethod
    def sanitize_title(cls, text: str) -> str:
        """Strips mobile OS emojis, banned buzzwords, and cleans extraneous whitespace."""
        return StyleRedliner.redline_text(text)

    @classmethod
    def resolve_vector_icon(cls, category_name: str) -> str:
        """Maps category name to an agency-grade Lucide/Phosphor monochromatic vector icon name."""
        cat_lower = category_name.lower()
        for k, icon in cls.CATEGORY_ICON_MAP.items():
            if k in cat_lower:
                return icon
        return cls.CATEGORY_ICON_MAP["default"]

    @classmethod
    def classify_catalog(
        cls,
        products: List[Dict[str, Any]],
        hero_ratio: float = 0.15
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Partitions raw product list into Hero Spotlight SKUs and Streamlined Dot-Leader SKUs.
        Heuristics:
        - Items explicitly marked 'is_hero' or 'signature'
        - Highest priced items within their category
        - Items with rich descriptions or tasting notes
        """
        if not products:
            return [], []

        heroes = []
        streamlined = []

        # Sort candidate products by price or explicit priority
        sorted_products = sorted(
            products,
            key=lambda x: (
                x.get("is_hero", False),
                x.get("price_val", 0.0) or cls._extract_numeric_price(x.get("price", "0"))
            ),
            reverse=True
        )

        hero_count = max(1, int(len(products) * hero_ratio))

        for idx, p in enumerate(sorted_products):
            clean_item = dict(p)
            clean_item["name"] = cls.sanitize_title(str(p.get("name", "")))
            clean_item["category"] = cls.sanitize_title(str(p.get("category", "General")))

            if idx < hero_count or p.get("is_hero", False):
                clean_item["is_hero"] = True
                heroes.append(clean_item)
            else:
                clean_item["is_hero"] = False
                streamlined.append(clean_item)

        return heroes, streamlined

    @staticmethod
    def _extract_numeric_price(price_str: Any) -> float:
        """Parses numeric price from strings like '₹775 / 1L Jar'."""
        if isinstance(price_str, (int, float)):
            return float(price_str)
        nums = re.findall(r"\d+(?:\.\d+)?", str(price_str).replace(",", ""))
        return float(nums[0]) if nums else 0.0
