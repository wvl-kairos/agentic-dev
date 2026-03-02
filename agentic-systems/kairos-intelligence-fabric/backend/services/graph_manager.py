from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Protocol

from models.graph_models import EdgeModel, GraphMetadata, GraphResponse, NodeModel

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent.parent / "data"
_SAMPLE_PATH = _DATA_DIR / "sample_ontology.json"
_STATE_PATH = _DATA_DIR / "graph_state.json"


class GraphStore(Protocol):
    def get_graph(self) -> GraphResponse: ...
    def update_graph(self, graph: GraphResponse) -> None: ...


class InMemoryGraphManager:
    """In-memory graph store with disk persistence.

    On startup, loads from graph_state.json if it exists (previous session),
    otherwise falls back to sample_ontology.json (factory default).
    Implements the GraphStore protocol so it can be swapped for Neo4jGraphManager.
    """

    def __init__(self) -> None:
        self._graph: GraphResponse | None = None
        self._baseline: GraphResponse | None = None
        self._load()

    def _load(self) -> None:
        # Prefer persisted state from a previous session
        if _STATE_PATH.exists():
            try:
                raw = json.loads(_STATE_PATH.read_text(encoding="utf-8"))
                nodes = [NodeModel(**n) for n in raw["nodes"]]
                edges = [EdgeModel(**e) for e in raw["edges"]]
                meta = raw.get("metadata", {})
                self._graph = GraphResponse(
                    nodes=nodes,
                    edges=edges,
                    metadata=GraphMetadata(
                        total_nodes=len(nodes),
                        total_edges=len(edges),
                        ontology_version=meta.get("ontology_version", "persisted"),
                        last_updated=meta.get("last_updated", ""),
                    ),
                )
                self.save_baseline()
                logger.info(
                    "Loaded persisted graph state: %d nodes, %d edges",
                    len(nodes), len(edges),
                )
                return
            except (json.JSONDecodeError, KeyError, OSError) as e:
                logger.warning("Failed to load graph_state.json, falling back to sample: %s", e)

        # Fall back to sample ontology (factory default)
        try:
            raw = json.loads(_SAMPLE_PATH.read_text(encoding="utf-8"))
        except FileNotFoundError:
            raise RuntimeError(f"Required data file not found: {_SAMPLE_PATH}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON in {_SAMPLE_PATH}: {e}")

        nodes = [NodeModel(**n) for n in raw["nodes"]]
        edges = [EdgeModel(**e) for e in raw["edges"]]

        self._graph = GraphResponse(
            nodes=nodes,
            edges=edges,
            metadata=GraphMetadata(
                total_nodes=len(nodes),
                total_edges=len(edges),
                ontology_version="1.0",
                last_updated="2026-02-19T00:00:00Z",
            ),
        )
        self.save_baseline()
        logger.info(
            "Loaded sample graph: %d nodes, %d edges (baseline saved)",
            len(nodes), len(edges),
        )

    def get_graph(self) -> GraphResponse:
        if self._graph is None:
            raise RuntimeError(
                "Graph data failed to initialize. Check sample_ontology.json."
            )
        return self._graph

    def update_graph(self, graph: GraphResponse) -> None:
        """Replace the in-memory graph with a newly constructed ontology."""
        self._graph = graph
        logger.info(
            "Graph updated: %d nodes, %d edges",
            len(graph.nodes),
            len(graph.edges),
        )

    def save_to_disk(self) -> None:
        """Persist current graph state to graph_state.json."""
        if not self._graph:
            return
        data = {
            "nodes": [n.model_dump() for n in self._graph.nodes],
            "edges": [e.model_dump() for e in self._graph.edges],
            "metadata": self._graph.metadata.model_dump(),
        }
        _STATE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info(
            "Graph persisted to disk: %d nodes, %d edges",
            len(self._graph.nodes), len(self._graph.edges),
        )

    def save_baseline(self) -> None:
        """Snapshot current graph as the baseline for reset."""
        if self._graph:
            self._baseline = GraphResponse(
                nodes=list(self._graph.nodes),
                edges=list(self._graph.edges),
                metadata=self._graph.metadata,
            )
            logger.info(
                "Baseline saved: %d nodes, %d edges",
                len(self._baseline.nodes),
                len(self._baseline.edges),
            )

    def restore_baseline(self) -> GraphResponse | None:
        """Restore graph to the saved baseline snapshot."""
        if self._baseline:
            self._graph = GraphResponse(
                nodes=list(self._baseline.nodes),
                edges=list(self._baseline.edges),
                metadata=self._baseline.metadata,
            )
            logger.info(
                "Baseline restored: %d nodes, %d edges",
                len(self._graph.nodes),
                len(self._graph.edges),
            )
            return self._graph
        return None

    def reset_to_factory(self) -> GraphResponse:
        """Delete persisted state and reload from sample_ontology.json."""
        if _STATE_PATH.exists():
            _STATE_PATH.unlink()
            logger.info("Deleted graph_state.json")
        self._load()
        return self.get_graph()

    @property
    def has_baseline(self) -> bool:
        return self._baseline is not None


# Singleton instance
graph_manager = InMemoryGraphManager()
