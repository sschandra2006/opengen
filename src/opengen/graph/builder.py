"""
OpenGen Document Graphifier Engine.
Constructs typed semantic Knowledge Graphs from raw document extracts, tables, and text.
Runs 100% locally and deterministically with ZERO token consumption.
"""
import re
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from opengen.domain.document import ExtractedInformation, ExtractedField, ExtractedTable
from opengen.graph.models import KnowledgeGraph, GraphNode, GraphEdge, EntityType

# Heuristics for entity detection
SKU_PATTERN = re.compile(r'\b(?:[A-Z]{2,6}[-_][A-Z0-9]{2,10}|[A-Z0-9]{3,8}-[0-9]{2,5})\b')
PRICE_PATTERN = re.compile(r'(?:[\$€£₹]|\bUSD|\bEUR|\bINR)\s*[0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})?')
PERCENT_METRIC_PATTERN = re.compile(r'[-+]?\b\d+(?:\.\d+)?%\b')
METRIC_LABEL_PATTERN = re.compile(r'\b(growth|revenue|profit|margin|churn|retention|cagr|yoy|ebitda|arr|mrr|volume)\b', re.IGNORECASE)


def _slug(text: str) -> str:
    cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', str(text).strip().lower())
    return re.sub(r'_+', '_', cleaned).strip('_')


class DocumentGraphifier:
    """Local, deterministic Knowledge Graph constructor for documents, reports, and catalogs."""

    @classmethod
    def graphify(
        cls,
        extracted_info: ExtractedInformation,
        fallback_org_name: Optional[str] = None
    ) -> KnowledgeGraph:
        """
        Builds an interconnected KnowledgeGraph from ExtractedInformation.
        """
        doc_hash = extracted_info.file_hash or hashlib.sha256(extracted_info.raw_text.encode("utf-8")).hexdigest()
        kg = KnowledgeGraph(document_hash=doc_hash)

        # 1. Identify primary Organization / Issuer
        org_node = cls._identify_organization(extracted_info, fallback_org_name)
        if org_node:
            kg.add_node(org_node)

        # 2. Extract entities and properties from key-value fields
        field_nodes = cls._graphify_fields(extracted_info.fields)
        for node, edges in field_nodes:
            kg.add_node(node)
            if org_node and node.id != org_node.id:
                # Link org to field node if appropriate
                pred = cls._predicate_for(org_node.entity_type, node.entity_type)
                kg.add_edge(GraphEdge(source_id=org_node.id, target_id=node.id, predicate=pred))
            for edge in edges:
                kg.add_edge(edge)

        # 3. Graphify Tables (Crucial for Retail Catalogs, Invoices, Financial Tables)
        table_elements = cls._graphify_tables(extracted_info.tables, org_node.id if org_node else None)
        for n in table_elements["nodes"]:
            kg.add_node(n)
        for e in table_elements["edges"]:
            kg.add_edge(e)

        # 4. Extract free-text Metrics from raw paragraphs
        if extracted_info.raw_text:
            text_metric_nodes = cls._extract_metrics_from_text(extracted_info.raw_text, org_node.id if org_node else None)
            for n, e in text_metric_nodes:
                kg.add_node(n)
                if e:
                    kg.add_edge(e)

        return kg

    @classmethod
    def _identify_organization(
        cls,
        info: ExtractedInformation,
        fallback_name: Optional[str] = None
    ) -> Optional[GraphNode]:
        """Resolves the primary company or organization anchor."""
        candidates = []
        if fallback_name:
            candidates.append(fallback_name)

        # Check field keys
        for f in info.fields:
            fk = f.field.lower()
            if any(k in fk for k in ["company", "organization", "vendor", "client", "issuer", "brand", "business"]):
                candidates.append(str(f.value).strip())

        # Check headings
        for h in info.headings:
            h_text = h.get("text", str(h)) if isinstance(h, dict) else str(h)
            h_clean = h_text.strip()
            if len(h_clean) < 60 and not any(skip in h_clean.lower() for skip in ["table of contents", "appendix", "page"]):
                candidates.append(h_clean)

        if not candidates and info.filename:
            # Derive from filename
            base = info.filename.split(".")[0].replace("_", " ").replace("-", " ")
            candidates.append(base.title())

        org_name = candidates[0] if candidates else "Enterprise Organization"
        nid = f"ent_org_{_slug(org_name)[:24]}"
        return GraphNode(
            id=nid,
            entity_type=EntityType.ORGANIZATION,
            canonical_name=org_name,
            properties={"name": org_name},
            confidence=0.98,
            source_pages=[1]
        )

    @classmethod
    def _graphify_fields(cls, fields: List[ExtractedField]) -> List[Tuple[GraphNode, List[GraphEdge]]]:
        """Converts structured fields into typed entity nodes and cross-edges."""
        results = []
        for f in fields:
            val_str = str(f.value).strip()
            fk = f.field.lower()
            ft = f.field_type.lower()

            etype = EntityType.GENERAL
            if "price" in fk or "amount" in fk or ft == "currency" or PRICE_PATTERN.match(val_str):
                etype = EntityType.PRICE
            elif "sku" in fk or "item_no" in fk or "model" in fk or SKU_PATTERN.match(val_str):
                etype = EntityType.SKU
            elif "growth" in fk or "metric" in fk or "kpi" in fk or "%" in val_str:
                etype = EntityType.METRIC
            elif "date" in fk or ft == "date":
                etype = EntityType.DATE
            elif any(p in fk for p in ["name", "author", "signatory", "ceo", "director", "manager"]):
                etype = EntityType.PERSON
            elif any(c in fk for c in ["clause", "policy", "term", "warranty"]):
                etype = EntityType.CLAUSE
            elif any(p in fk for p in ["product", "item", "service", "offering"]):
                etype = EntityType.PRODUCT

            nid = f"ent_{etype.value}_{_slug(fk)}_{_slug(val_str)[:16]}"
            node = GraphNode(
                id=nid,
                entity_type=etype,
                canonical_name=val_str,
                properties={"field": f.field, "value": val_str, "context": f.context or ""},
                confidence=f.confidence,
                source_pages=[f.page] if f.page else [1]
            )
            results.append((node, []))
        return results

    @classmethod
    def _graphify_tables(
        cls,
        tables: List[Any],
        org_id: Optional[str] = None
    ) -> Dict[str, List[Any]]:
        """
        Parses structured table data into hierarchical Product -> SKU -> Price relations.
        """
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []

        for t_idx, table in enumerate(tables):
            headers = []
            rows = []
            if isinstance(table, ExtractedTable):
                headers = [str(h).lower() for h in table.headers]
                rows = table.rows
            elif isinstance(table, dict):
                headers = [str(h).lower() for h in table.get("headers", [])]
                rows = table.get("rows", [])

            # Identify column roles
            prod_col = next((i for i, h in enumerate(headers) if any(k in h for k in ["product", "item", "description", "title"])), None)
            sku_col = next((i for i, h in enumerate(headers) if any(k in h for k in ["sku", "code", "model", "variant", "size", "unit"])), None)
            price_col = next((i for i, h in enumerate(headers) if any(k in h for k in ["price", "cost", "amount", "mrp", "rate", "inr", "usd"])), None)
            metric_col = next((i for i, h in enumerate(headers) if any(k in h for k in ["metric", "change", "growth", "percentage", "qty", "quantity"])), None)

            for r_idx, row in enumerate(rows):
                if not row:
                    continue
                row_vals = [str(c).strip() for c in row]

                # Product Node
                p_name = row_vals[prod_col] if prod_col is not None and prod_col < len(row_vals) else f"Item {r_idx + 1}"
                if not p_name or p_name.lower() in ["total", "subtotal"]:
                    continue

                prod_id = f"ent_prod_t{t_idx}_r{r_idx}_{_slug(p_name)[:20]}"
                p_node = GraphNode(
                    id=prod_id,
                    entity_type=EntityType.PRODUCT,
                    canonical_name=p_name,
                    properties={"table_index": t_idx, "row_index": r_idx},
                    confidence=0.95
                )
                nodes.append(p_node)

                if org_id:
                    edges.append(GraphEdge(source_id=org_id, target_id=prod_id, predicate="PRODUCES"))

                # SKU / Variant Node
                sku_val = row_vals[sku_col] if sku_col is not None and sku_col < len(row_vals) else None
                sku_id = None
                if sku_val:
                    sku_id = f"ent_sku_t{t_idx}_r{r_idx}_{_slug(sku_val)[:16]}"
                    s_node = GraphNode(
                        id=sku_id,
                        entity_type=EntityType.SKU,
                        canonical_name=sku_val,
                        properties={"sku_code": sku_val, "product": p_name},
                        confidence=0.95
                    )
                    nodes.append(s_node)
                    edges.append(GraphEdge(source_id=prod_id, target_id=sku_id, predicate="HAS_VARIANT"))

                # Price Node
                price_val = row_vals[price_col] if price_col is not None and price_col < len(row_vals) else None
                if price_val:
                    price_id = f"ent_price_t{t_idx}_r{r_idx}_{_slug(price_val)[:16]}"
                    pr_node = GraphNode(
                        id=price_id,
                        entity_type=EntityType.PRICE,
                        canonical_name=price_val,
                        properties={"amount": price_val, "target": p_name},
                        confidence=0.98
                    )
                    nodes.append(pr_node)
                    # Link price to SKU if available, else directly to Product
                    src = sku_id if sku_id else prod_id
                    edges.append(GraphEdge(source_id=src, target_id=price_id, predicate="HAS_PRICE"))

                # Metric Node
                if metric_col is not None and metric_col < len(row_vals):
                    m_val = row_vals[metric_col]
                    if m_val:
                        m_id = f"ent_metric_t{t_idx}_r{r_idx}_{_slug(m_val)[:16]}"
                        m_node = GraphNode(
                            id=m_id,
                            entity_type=EntityType.METRIC,
                            canonical_name=m_val,
                            properties={"metric_value": m_val, "header": headers[metric_col]},
                            confidence=0.90
                        )
                        nodes.append(m_node)
                        edges.append(GraphEdge(source_id=prod_id, target_id=m_id, predicate="REPORTED_METRIC"))

        return {"nodes": nodes, "edges": edges}

    @classmethod
    def _extract_metrics_from_text(
        cls,
        text: str,
        org_id: Optional[str] = None
    ) -> List[Tuple[GraphNode, Optional[GraphEdge]]]:
        """Scans unstructured paragraphs for quantitative KPIs and metrics."""
        results = []
        for line in text.splitlines():
            line_s = line.strip()
            if not line_s or len(line_s) > 200:
                continue

            pct_match = PERCENT_METRIC_PATTERN.search(line_s)
            lbl_match = METRIC_LABEL_PATTERN.search(line_s)
            if pct_match or (lbl_match and any(ch.isdigit() for ch in line_s)):
                val = pct_match.group(0) if pct_match else line_s[:40]
                lbl = lbl_match.group(0).title() if lbl_match else "Performance Indicator"
                m_id = f"ent_metric_{_slug(lbl)}_{_slug(val)[:12]}"
                m_node = GraphNode(
                    id=m_id,
                    entity_type=EntityType.METRIC,
                    canonical_name=f"{lbl}: {val}",
                    properties={"metric": lbl, "value": val, "context": line_s},
                    confidence=0.92
                )
                edge = None
                if org_id:
                    edge = GraphEdge(source_id=org_id, target_id=m_id, predicate="REPORTED_METRIC")
                results.append((m_node, edge))
        return results

    @classmethod
    def _predicate_for(cls, src_type: EntityType, tgt_type: EntityType) -> str:
        """Determines the semantic predicate between two entity types."""
        if src_type == EntityType.ORGANIZATION and tgt_type == EntityType.PRODUCT:
            return "PRODUCES"
        elif src_type == EntityType.ORGANIZATION and tgt_type == EntityType.METRIC:
            return "REPORTED_METRIC"
        elif src_type == EntityType.PRODUCT and tgt_type == EntityType.SKU:
            return "HAS_VARIANT"
        elif (src_type in [EntityType.SKU, EntityType.PRODUCT]) and tgt_type == EntityType.PRICE:
            return "HAS_PRICE"
        elif tgt_type == EntityType.PERSON:
            return "MANAGED_BY"
        elif tgt_type == EntityType.DATE:
            return "RECORDED_ON"
        return "RELATES_TO"
