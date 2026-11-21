"""
OpenGen Knowledge Graph SQLite Storage Engine.
Provides persistent, indexed storage for document entity graphs across all generation studios.
Replaces repeated multi-modal extraction with zero-token cross-studio graph retrieval.
"""
import json
import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Union, Set
from opengen.config import settings
from opengen.graph.models import KnowledgeGraph, GraphNode, GraphEdge, EntityType

logger = logging.getLogger(__name__)


class SQLiteGraphStore:
    """Persistent SQLite-backed repository for Knowledge Graphs."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        self.db_path = Path(db_path or settings.DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes tables and high-performance relational indices."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS kg_nodes (
                    node_id TEXT NOT NULL,
                    doc_hash TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    canonical_name TEXT NOT NULL,
                    properties_json TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    source_pages_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (doc_hash, node_id)
                );
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS kg_edges (
                    edge_id TEXT NOT NULL,
                    doc_hash TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    predicate TEXT NOT NULL,
                    properties_json TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (doc_hash, edge_id)
                );
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_kg_nodes_doc ON kg_nodes(doc_hash, entity_type);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_kg_edges_lookup ON kg_edges(doc_hash, source_id, predicate);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_kg_edges_target ON kg_edges(doc_hash, target_id);")
            conn.commit()

    def save_graph(self, graph: KnowledgeGraph) -> None:
        """Persists or updates a complete KnowledgeGraph atomically."""
        if not graph.document_hash:
            return

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Insert or replace nodes
            for node in graph.nodes.values():
                cursor.execute("""
                    INSERT OR REPLACE INTO kg_nodes (
                        node_id, doc_hash, entity_type, canonical_name,
                        properties_json, confidence, source_pages_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    node.id,
                    graph.document_hash,
                    node.entity_type.value,
                    node.canonical_name,
                    json.dumps(node.properties, ensure_ascii=False),
                    node.confidence,
                    json.dumps(node.source_pages)
                ))

            # Insert or replace edges
            for edge in graph.edges:
                edge_id = f"{edge.source_id}__{edge.predicate}__{edge.target_id}"
                cursor.execute("""
                    INSERT OR REPLACE INTO kg_edges (
                        edge_id, doc_hash, source_id, target_id,
                        predicate, properties_json, weight
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    edge_id,
                    graph.document_hash,
                    edge.source_id,
                    edge.target_id,
                    edge.predicate,
                    json.dumps(edge.properties, ensure_ascii=False),
                    edge.weight
                ))
            conn.commit()
            logger.info(f"Persisted KnowledgeGraph for '{graph.document_hash[:12]}' ({len(graph.nodes)} nodes, {len(graph.edges)} edges)")

    def get_graph(self, doc_hash: str) -> Optional[KnowledgeGraph]:
        """Loads the full stored KnowledgeGraph for a document hash."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM kg_nodes WHERE doc_hash = ?", (doc_hash,))
            node_rows = cursor.fetchall()
            if not node_rows:
                return None

            nodes = {}
            for r in node_rows:
                props = json.loads(r["properties_json"])
                pages = json.loads(r["source_pages_json"])
                nodes[r["node_id"]] = GraphNode(
                    id=r["node_id"],
                    entity_type=EntityType.from_str(r["entity_type"]),
                    canonical_name=r["canonical_name"],
                    properties=props,
                    confidence=float(r["confidence"]),
                    source_pages=pages
                )

            cursor.execute("SELECT * FROM kg_edges WHERE doc_hash = ?", (doc_hash,))
            edge_rows = cursor.fetchall()
            edges = []
            for er in edge_rows:
                eprops = json.loads(er["properties_json"])
                edges.append(GraphEdge(
                    source_id=er["source_id"],
                    target_id=er["target_id"],
                    predicate=er["predicate"],
                    properties=eprops,
                    weight=float(er["weight"])
                ))

            return KnowledgeGraph(
                document_hash=doc_hash,
                nodes=nodes,
                edges=edges
            )

    def get_subgraph(
        self,
        doc_hash: str,
        target_types: List[Union[EntityType, str]],
        max_depth: int = 1
    ) -> Optional[KnowledgeGraph]:
        """Directly retrieves a targeted, pruned subgraph for a document hash."""
        full_graph = self.get_graph(doc_hash)
        if not full_graph:
            return None
        return full_graph.extract_subgraph(target_types=target_types, max_depth=max_depth)

    def delete_graph(self, doc_hash: str) -> None:
        """Deletes all graph entities and relations for a document hash."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM kg_nodes WHERE doc_hash = ?", (doc_hash,))
            cursor.execute("DELETE FROM kg_edges WHERE doc_hash = ?", (doc_hash,))
            conn.commit()


# Default singleton instance
graph_store = SQLiteGraphStore()
