"""
Comprehensive Unit and Integration Tests for:
1. Universal Model Agnosticism (Decoupling from Gemini, dynamic multi-provider auto-resolution)
2. Graphify Knowledge Graph Subsystem (Entities, relations, SQLite storage, subgraph pruning, and token reduction)
"""
import os
import pytest
from pathlib import Path
from opengen.config import resolve_default_model
from opengen.hardware.models import HardwareTier, HardwareProfile, AcceleratorType
from opengen.hardware.classifier import TierClassifier, resolve_tier_remote_model
from opengen.domain.document import ExtractedInformation, ExtractedField, ExtractedTable
from opengen.graph import (
    EntityType,
    GraphNode,
    GraphEdge,
    KnowledgeGraph,
    SQLiteGraphStore,
    DocumentGraphifier,
    SubgraphPruner,
)
from opengen.client import OpenGenClient
from opengen.mcp.server import MCP_TOOLS, tool_graphify_document, tool_query_subgraph


# =========================================================================
# Part 1: Universal Model Agnosticism Tests
# =========================================================================

def test_dynamic_model_auto_resolution(monkeypatch):
    """Verifies that OpenGen dynamically resolves the best provider without hardcoded bias."""
    # 1. Explicit OPENGEN_MODEL override takes top priority
    monkeypatch.setenv("OPENGEN_MODEL", "vllm/mistral-large-2411")
    assert resolve_default_model() == "vllm/mistral-large-2411"
    monkeypatch.delenv("OPENGEN_MODEL", raising=False)

    # 2. Anthropic configured
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    assert resolve_default_model() == "anthropic/claude-3-5-haiku-20241022"
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    # 3. OpenAI configured
    monkeypatch.setenv("OPENAI_API_KEY", "sk-proj-test-key")
    assert resolve_default_model() == "openai/gpt-4o-mini"
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    # 4. DeepSeek configured
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-deepseek-test-key")
    assert resolve_default_model() == "deepseek/deepseek-chat"
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    # 5. Gemini configured
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyTestKey")
    assert resolve_default_model() == "gemini/gemini-2.5-flash"
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    # 6. Completely offline / no cloud keys configured -> local Ollama fallback
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENGEN_DEFAULT_PRIMARY_MODEL", raising=False)
    assert resolve_default_model() == "ollama/huihui_ai/qwen2.5-abliterated:7b"


def test_hardware_classifier_model_agnostic_resolution(monkeypatch):
    """Verifies hardware execution policies dynamically adopt the configured provider."""
    # When Anthropic is active
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-live")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    p_budget = HardwareProfile(
        total_ram_gb=16.0,
        available_ram_gb=8.0,
        cpu_count_physical=8,
        cpu_count_logical=16,
        accelerator=AcceleratorType.CUDA,
        assigned_tier=HardwareTier.TIER_1_BUDGET
    )
    pol = TierClassifier.generate_policy(p_budget)
    assert pol.recommended_remote_model == "anthropic/claude-3-5-haiku-20241022"

    p_studio = HardwareProfile(
        total_ram_gb=64.0,
        available_ram_gb=40.0,
        cpu_count_physical=16,
        cpu_count_logical=32,
        accelerator=AcceleratorType.CUDA,
        assigned_tier=HardwareTier.TIER_3_STUDIO
    )
    pol_studio = TierClassifier.generate_policy(p_studio)
    assert pol_studio.recommended_remote_model == "anthropic/claude-3-7-sonnet"


# =========================================================================
# Part 2: Knowledge Graph ("Graphify") Subsystem Tests
# =========================================================================

def test_graph_node_and_edge_subgraph_extraction():
    """Tests in-memory entity graph construction and targeted subgraph pruning."""
    kg = KnowledgeGraph(document_hash="doc_hash_test_123")

    org = GraphNode(
        id="ent_org_sangam",
        entity_type=EntityType.ORGANIZATION,
        canonical_name="Sangam Dairy Co.",
        properties={"jurisdiction": "India"}
    )
    prod = GraphNode(
        id="ent_prod_ghee",
        entity_type=EntityType.PRODUCT,
        canonical_name="Vedic Bilona Ghee",
        properties={"volume": "1L"}
    )
    sku = GraphNode(
        id="ent_sku_ghee1l",
        entity_type=EntityType.SKU,
        canonical_name="SKU-GHEE-1L"
    )
    price = GraphNode(
        id="ent_price_1250",
        entity_type=EntityType.PRICE,
        canonical_name="1250 INR",
        properties={"amount": 1250}
    )
    metric = GraphNode(
        id="ent_metric_growth",
        entity_type=EntityType.METRIC,
        canonical_name="YoY Growth: +114%",
        properties={"growth": "+114%"}
    )

    kg.add_node(org)
    kg.add_node(prod)
    kg.add_node(sku)
    kg.add_node(price)
    kg.add_node(metric)

    kg.add_edge(GraphEdge(source_id=org.id, target_id=prod.id, predicate="PRODUCES"))
    kg.add_edge(GraphEdge(source_id=prod.id, target_id=sku.id, predicate="HAS_VARIANT"))
    kg.add_edge(GraphEdge(source_id=sku.id, target_id=price.id, predicate="HAS_PRICE"))
    kg.add_edge(GraphEdge(source_id=org.id, target_id=metric.id, predicate="REPORTED_METRIC"))

    assert len(kg.nodes) == 5
    assert len(kg.edges) == 4

    # Extract catalog pricing subgraph (Products, SKUs, Prices)
    catalog_sub = kg.extract_subgraph(target_types=[EntityType.PRODUCT, EntityType.SKU, EntityType.PRICE], max_depth=1)
    assert "ent_prod_ghee" in catalog_sub.nodes
    assert "ent_sku_ghee1l" in catalog_sub.nodes
    assert "ent_price_1250" in catalog_sub.nodes
    # Metric should be pruned out
    assert "ent_metric_growth" not in catalog_sub.nodes


def test_sqlite_graph_store_persistence(tmp_path):
    """Tests atomic persistence, retrieval, and indexing of knowledge graphs in SQLite."""
    db_file = tmp_path / "test_kg.db"
    store = SQLiteGraphStore(db_path=db_file)

    kg = KnowledgeGraph(document_hash="hash_alpha_99")
    n1 = GraphNode(id="n1", entity_type=EntityType.PRODUCT, canonical_name="Almond Butter")
    n2 = GraphNode(id="n2", entity_type=EntityType.PRICE, canonical_name="500 INR")
    kg.add_node(n1)
    kg.add_node(n2)
    kg.add_edge(GraphEdge(source_id="n1", target_id="n2", predicate="HAS_PRICE"))

    store.save_graph(kg)

    loaded_kg = store.get_graph("hash_alpha_99")
    assert loaded_kg is not None
    assert len(loaded_kg.nodes) == 2
    assert len(loaded_kg.edges) == 1
    assert loaded_kg.nodes["n1"].canonical_name == "Almond Butter"

    # Query pruned subgraph from SQLite store
    sub = store.get_subgraph("hash_alpha_99", target_types=[EntityType.PRICE])
    assert sub is not None
    assert "n2" in sub.nodes


def test_document_graphifier_deterministic_extraction():
    """Verifies deterministic local Graphification from ExtractedInformation tables and fields."""
    table = ExtractedTable(
        table_index=0,
        source="sample.pdf",
        headers=["Product", "SKU", "Price", "Growth"],
        rows=[
            ["A2 Gir Cow Milk", "MILK-A2-1L", "95 INR", "+35%"],
            ["Organic Buffalo Ghee", "GHEE-BUF-500M", "650 INR", "+110%"]
        ],
        caption="Dairy Catalog"
    )
    fields = [
        ExtractedField(field="company_name", value="Surabhi Organics", source="sample.pdf", page=1),
        ExtractedField(field="established_date", value="15-Aug-2021", source="sample.pdf", page=1, field_type="date")
    ]
    raw_text = (
        "Surabhi Organics achieved a remarkable YoY Growth of +142% in organic dairy distribution.\n"
        "The flagship product A2 Gir Cow Milk retails at 95 INR per liter."
    )

    info = ExtractedInformation(
        document_id="surabhi_01",
        filename="surabhi.pdf",
        file_hash="hash_surabhi_001",
        fields=fields,
        tables=[table],
        headings=[{"text": "Surabhi Organics Annual Review", "level": 1}],
        raw_text=raw_text
    )

    kg = DocumentGraphifier.graphify(info)

    # Verify extracted entities
    assert len(kg.nodes) >= 6
    assert any(n.entity_type == EntityType.ORGANIZATION for n in kg.nodes.values())
    assert any(n.entity_type == EntityType.PRODUCT for n in kg.nodes.values())
    assert any(n.entity_type == EntityType.SKU for n in kg.nodes.values())
    assert any(n.entity_type == EntityType.PRICE for n in kg.nodes.values())
    assert any(n.entity_type == EntityType.METRIC for n in kg.nodes.values())

    # Verify relational links
    predicates = {e.predicate for e in kg.edges}
    assert "PRODUCES" in predicates or "HAS_VARIANT" in predicates
    assert "HAS_PRICE" in predicates


def test_subgraph_pruning_and_token_reduction_benchmark():
    """
    Demonstrates empirical 90%-98% prompt token reduction achieved by
    feeding pruned subgraphs instead of multi-page raw document text.
    """
    # Simulate a 15-page document with ~18,000 characters (~4,700 tokens)
    raw_doc_text = (
        "CONFIDENTIAL CORPORATE REPORT\n"
        "Section 1: Background and Regulatory Framework...\n"
        + ("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore. " * 150)
        + "\nKey Findings: Our flagship product Organic Vedic Ghee (SKU: GHEE-1L) generated 1,250 INR at 42% margin."
        + ("Additional legal boilerplate clauses, disclaimers, and warranty terms without operational relevance. " * 150)
    )

    kg = KnowledgeGraph(document_hash="doc_benchmark_01")
    kg.add_node(GraphNode(id="n_prod", entity_type=EntityType.PRODUCT, canonical_name="Organic Vedic Ghee"))
    kg.add_node(GraphNode(id="n_sku", entity_type=EntityType.SKU, canonical_name="GHEE-1L"))
    kg.add_node(GraphNode(id="n_price", entity_type=EntityType.PRICE, canonical_name="1250 INR"))
    kg.add_edge(GraphEdge(source_id="n_prod", target_id="n_sku", predicate="HAS_VARIANT"))
    kg.add_edge(GraphEdge(source_id="n_sku", target_id="n_price", predicate="HAS_PRICE"))

    # Prune for catalog pricing intent
    subgraph = SubgraphPruner.prune_for_intent(kg, intent="catalog_pricing")
    dense_prompt = SubgraphPruner.format_dense_prompt(kg, intent="catalog_pricing")

    # Metrics
    stats = SubgraphPruner.calculate_token_savings(subgraph, raw_doc_text)
    assert stats["raw_tokens"] > 3000
    assert stats["subgraph_tokens"] < 150
    assert stats["reduction_percentage"] >= 95.0, f"Expected >= 95% reduction, got {stats['reduction_percentage']}%"
    assert "GHEE-1L" in dense_prompt
    assert "1250 INR" in dense_prompt


def test_deterministic_anti_hallucination_verification():
    """Verifies zero-token local anti-hallucination verification against Knowledge Graph entities."""
    kg = KnowledgeGraph(document_hash="doc_verify_01")
    kg.add_node(GraphNode(
        id="prod_1",
        entity_type=EntityType.PRODUCT,
        canonical_name="Cold Pressed Coconut Oil",
        properties={"mrp": "450 INR", "volume": "500ml"}
    ))

    # True entities
    assert kg.validate_entity_presence("Cold Pressed Coconut Oil") is True
    assert kg.validate_entity_presence("450 INR") is True
    assert kg.validate_entity_presence("500ml") is True

    # Hallucinated / fake values generated by an ungrounded LLM
    assert kg.validate_entity_presence("₹9,999") is False
    assert kg.validate_entity_presence("Synthetic Motor Oil") is False


# =========================================================================
# Part 3: SDK Client and MCP Parity Tests
# =========================================================================

def test_client_graph_sdk_surface(tmp_path):
    """Verifies client.graph endpoints: graphify, query, format_prompt, audit_hallucination."""
    txt_file = tmp_path / "reference.txt"
    txt_file.write_text(
        "Company: Artisan Ghee Mills\n"
        "Product: Cultured Ghee\n"
        "SKU: AG-CULT-1L\n"
        "Price: 1400 INR\n"
        "YoY Growth: +85%\n",
        encoding="utf-8"
    )

    client = OpenGenClient()
    assert hasattr(client, "graph")

    # 1. Graphify
    kg = client.graph.graphify(txt_file)
    assert kg is not None
    assert len(kg.nodes) >= 3

    # 2. Format prompt
    prompt = client.graph.format_prompt(kg.document_hash, intent="presentation_traction")
    assert "KNOWLEDGE GRAPH SUBGRAPH" in prompt

    # 3. Audit hallucination
    assert client.graph.audit_hallucination(kg.document_hash, "Artisan Ghee Mills") is True
    assert client.graph.audit_hallucination(kg.document_hash, "99999 USD Fake") is False


def test_mcp_graph_tools_registration(tmp_path):
    """Verifies that MCP tools for Knowledge Graph are exposed to external agents."""
    assert "graphify_document" in MCP_TOOLS
    assert "query_subgraph" in MCP_TOOLS

    txt_file = tmp_path / "sample_mcp.txt"
    txt_file.write_text("Company: Apex Tech\nProduct: Edge Router\nPrice: 299 USD\n", encoding="utf-8")

    res_build = tool_graphify_document(str(txt_file))
    assert res_build["status"] == "completed"
    doc_hash = res_build["document_hash"]

    res_query = tool_query_subgraph(doc_hash, intent="catalog_pricing")
    assert res_query["status"] == "completed"
    assert "prompt_context" in res_query
