from __future__ import annotations

from dataclasses import dataclass
import heapq
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MapNode:
    id: str
    label: str
    kind: str
    level: str | None = None


@dataclass(frozen=True)
class MapEdge:
    src: str
    dst: str
    minutes: float
    accessible: bool
    instructions: str


@dataclass(frozen=True)
class StadiumMap:
    nodes: dict[str, MapNode]
    edges_out: dict[str, list[MapEdge]]


def load_stadium_map(data_dir: str | Path) -> StadiumMap:
    p = Path(data_dir) / "stadium_map.json"
    raw = json.loads(p.read_text(encoding="utf-8"))
    nodes = {
        n["id"]: MapNode(
            id=n["id"],
            label=n["label"],
            kind=n.get("kind", "waypoint"),
            level=n.get("level"),
        )
        for n in raw["nodes"]
    }
    edges_out: dict[str, list[MapEdge]] = {nid: [] for nid in nodes}
    for e in raw["edges"]:
        edge = MapEdge(
            src=e["src"],
            dst=e["dst"],
            minutes=float(e["minutes"]),
            accessible=bool(e.get("accessible", True)),
            instructions=e.get("instructions", f"Walk to {e['dst']}."),
        )
        edges_out.setdefault(edge.src, []).append(edge)
    return StadiumMap(nodes=nodes, edges_out=edges_out)


def shortest_path(
    smap: StadiumMap,
    *,
    start: str,
    goal: str,
    require_accessible: bool,
) -> tuple[list[str], float]:
    if start not in smap.nodes or goal not in smap.nodes:
        return ([], float("inf"))

    dist: dict[str, float] = {start: 0.0}
    prev: dict[str, str] = {}
    pq: list[tuple[float, str]] = [(0.0, start)]

    while pq:
        d, u = heapq.heappop(pq)
        if u == goal:
            break
        if d != dist.get(u):
            continue
        for e in smap.edges_out.get(u, []):
            if require_accessible and not e.accessible:
                continue
            nd = d + e.minutes
            if nd < dist.get(e.dst, float("inf")):
                dist[e.dst] = nd
                prev[e.dst] = u
                heapq.heappush(pq, (nd, e.dst))

    if goal not in dist:
        return ([], float("inf"))

    path = [goal]
    while path[-1] != start:
        path.append(prev[path[-1]])
    path.reverse()
    return (path, dist[goal])


def explain_path(smap: StadiumMap, path: list[str]) -> list[str]:
    if len(path) < 2:
        return []
    steps: list[str] = []
    for a, b in zip(path, path[1:]):
        edge = next((e for e in smap.edges_out.get(a, []) if e.dst == b), None)
        if edge is None:
            steps.append(f"Go from {smap.nodes[a].label} to {smap.nodes[b].label}.")
        else:
            steps.append(edge.instructions)
    return steps


def resolve_start_goal(
    *,
    smap: StadiumMap,
    from_hint: str,
    to_hint: str,
    poi_index: dict[str, Any],
) -> tuple[str | None, str | None]:
    def lookup(h: str) -> str | None:
        if h in smap.nodes:
            return h
        key = h.strip().lower()
        # POI lookup
        for poi in poi_index.values():
            if key in {str(poi.get("id", "")).lower(), str(poi.get("name", "")).lower()}:
                nid = poi.get("node_id")
                if isinstance(nid, str) and nid in smap.nodes:
                    return nid
        # fuzzy substring on node label
        for nid, n in smap.nodes.items():
            if key and key in n.label.lower():
                return nid
        return None

    return lookup(from_hint), lookup(to_hint)

