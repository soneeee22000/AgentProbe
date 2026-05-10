"""Render a static SVG of the Decision Graph for the README.

Uses the same layout logic as ``frontend/src/components/runs/decision-graph.tsx``
so the rendered file matches what users see in the live UI. Output is
``docs/screenshots/decision-graph-fail.svg`` and ``decision-graph-happy.svg``
at the repo root.

Usage:
    cd backend
    python -m scripts.render_demo_graph
"""

from __future__ import annotations

import asyncio
import os
import sys
import xml.sax.saxutils as xs
from dataclasses import dataclass
from pathlib import Path

from agentprobe.domain.entities import AgentRun, AgentStep
from agentprobe.infrastructure.persistence.models import (
    DEFAULT_DATABASE_URL,
    get_engine,
    get_session_factory,
)
from agentprobe.infrastructure.persistence.repositories.run_repository import (
    SQLAlchemyRunRepository,
)


# Mirrors decision-graph.tsx constants exactly.
COL_X = {
    "query": 40,
    "thought": 220,
    "action": 420,
    "observation": 620,
    "final": 820,
}
NODE_WIDTH = 170
NODE_HEIGHT = 64
ROW_GAP = 100
TOP_PAD = 32

NODE_COLORS = {
    "query": ("#1e2530", "#6b7a8d", "#c9d4e0"),
    "thought": ("#0d1f2a", "#4fc3f7", "#4fc3f7"),
    "action": ("#0d2010", "#81c784", "#81c784"),
    "observation": ("#2a1c08", "#ffb74d", "#ffb74d"),
    "final": ("#241627", "#ce93d8", "#ce93d8"),
    "error": ("#2a0d0d", "#ef5350", "#ef5350"),
}

NODE_LABEL = {
    "query": "QUERY",
    "thought": "THOUGHT",
    "action": "ACTION",
    "observation": "OBSERVATION",
    "final": "DECISION",
    "error": "ACTION",
}


@dataclass
class Node:
    id: str
    x: int
    y: int
    type: str
    label: str
    detail: str
    tool_name: str | None = None
    failure_type: str | None = None
    latency_ms: float | None = None
    token_count: int | None = None


@dataclass
class Edge:
    src: str
    dst: str
    failed: bool = False


def _truncate(s: str, n: int) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1] + "…"


def build_graph(run: AgentRun) -> tuple[list[Node], list[Edge], int, int]:
    visible: list[AgentStep] = [
        s
        for s in run.steps
        if not (s.step_type.value == "system" and s.content.startswith("{"))
    ]

    nodes: list[Node] = []
    edges: list[Edge] = []

    nodes.append(
        Node(
            id="query",
            x=COL_X["query"],
            y=TOP_PAD,
            type="query",
            label=NODE_LABEL["query"],
            detail=run.query,
        )
    )

    # Group into ReAct cycles (one row each).
    rows: list[dict] = []
    current: dict | None = None
    for step in visible:
        st = step.step_type.value
        if st == "thought":
            if current:
                rows.append(current)
            current = {"idx": len(rows), "thought": step}
        elif st == "action":
            if not current:
                current = {"idx": len(rows)}
            current["action"] = step
        elif st == "observation":
            if not current:
                current = {"idx": len(rows)}
            current["observation"] = step
        elif st == "final_answer":
            if not current:
                current = {"idx": len(rows)}
            current["final"] = step
    if current:
        rows.append(current)

    for idx, row in enumerate(rows):
        y = TOP_PAD + idx * ROW_GAP
        prev_id: str | None = None
        if idx == 0:
            prev_id = "query"
        else:
            p = rows[idx - 1]
            for k in ("observation", "action", "thought"):
                if k in p:
                    prev_id = f"{k[:5]}-{p['idx']}"
                    break

        if "thought" in row:
            t = row["thought"]
            nid = f"thoug-{row['idx']}"
            nodes.append(
                Node(
                    id=nid,
                    x=COL_X["thought"],
                    y=y,
                    type="thought",
                    label=NODE_LABEL["thought"],
                    detail=t.content,
                    failure_type=t.failure_type.value
                    if t.failure_type.value != "none"
                    else None,
                    latency_ms=t.latency_ms,
                    token_count=t.token_count,
                )
            )
            if prev_id:
                edges.append(Edge(prev_id, nid))
            prev_id = nid

        if "action" in row:
            a = row["action"]
            nid = f"actio-{row['idx']}"
            is_fail = a.failure_type.value != "none"
            label_text = (
                f"{NODE_LABEL['action']} · {a.tool_name.upper()}"
                if a.tool_name
                else NODE_LABEL["action"]
            )
            nodes.append(
                Node(
                    id=nid,
                    x=COL_X["action"],
                    y=y,
                    type="error" if is_fail else "action",
                    label=label_text,
                    detail=a.tool_args or a.content,
                    tool_name=a.tool_name,
                    failure_type=a.failure_type.value if is_fail else None,
                    latency_ms=a.latency_ms,
                    token_count=a.token_count,
                )
            )
            if prev_id:
                edges.append(Edge(prev_id, nid, failed=is_fail))
            prev_id = nid

        if "observation" in row:
            o = row["observation"]
            nid = f"obser-{row['idx']}"
            is_fail = o.failure_type.value != "none"
            nodes.append(
                Node(
                    id=nid,
                    x=COL_X["observation"],
                    y=y,
                    type="error" if is_fail else "observation",
                    label=NODE_LABEL["observation"],
                    detail=o.content,
                    failure_type=o.failure_type.value if is_fail else None,
                    latency_ms=o.latency_ms,
                    token_count=o.token_count,
                )
            )
            if prev_id:
                edges.append(Edge(prev_id, nid, failed=is_fail))
            prev_id = nid

        if "final" in row:
            f = row["final"]
            nid = f"final-{row['idx']}"
            is_fail = f.failure_type.value != "none"
            nodes.append(
                Node(
                    id=nid,
                    x=COL_X["final"],
                    y=y,
                    type="final",
                    label=NODE_LABEL["final"],
                    detail=f.content or run.final_answer or "(no final)",
                    failure_type=f.failure_type.value if is_fail else None,
                    latency_ms=f.latency_ms,
                    token_count=f.token_count,
                )
            )
            if prev_id:
                edges.append(Edge(prev_id, nid, failed=is_fail))

    width = COL_X["final"] + NODE_WIDTH + 60
    height = TOP_PAD + max(len(rows), 1) * ROW_GAP + 60
    return nodes, edges, width, height


def edge_path(a: Node, b: Node) -> str:
    """Mirror of edgePath in decision-graph.tsx — forward + backward routing."""
    source_right = a.x + NODE_WIDTH
    source_mid_y = a.y + NODE_HEIGHT // 2
    target_left = b.x
    target_mid_y = b.y + NODE_HEIGHT // 2

    if target_left >= source_right:
        dx = target_left - source_right
        cx1 = source_right + dx * 0.5
        cx2 = target_left - dx * 0.5
        return (
            f"M {source_right} {source_mid_y} C {cx1} {source_mid_y}, "
            f"{cx2} {target_mid_y}, {target_left} {target_mid_y}"
        )

    source_bottom_x = a.x + NODE_WIDTH // 2
    source_bottom_y = a.y + NODE_HEIGHT
    dy = target_mid_y - source_bottom_y
    cy1 = source_bottom_y + dy * 0.6
    cx2 = max(target_left - 60, 0)
    return (
        f"M {source_bottom_x} {source_bottom_y} C {source_bottom_x} {cy1}, "
        f"{cx2} {target_mid_y}, {target_left} {target_mid_y}"
    )


def render_svg(nodes: list[Node], edges: list[Edge], w: int, h: int) -> str:
    by_id = {n.id: n for n in nodes}
    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}" style="background:#070a0e;font-family:'
        f'ui-sans-serif,system-ui,sans-serif">'
    )
    parts.append(
        '<defs>'
        '<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="6" markerHeight="6" orient="auto">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#6b7a8d"/></marker>'
        '<marker id="arrow-fail" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="6" markerHeight="6" orient="auto">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#ef5350"/></marker>'
        '<pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">'
        '<path d="M 24 0 L 0 0 0 24" fill="none" stroke="#1a2030" '
        'stroke-width="0.5"/></pattern>'
        "</defs>"
    )
    parts.append(f'<rect width="{w}" height="{h}" fill="url(#grid)"/>')

    for e in edges:
        a, b = by_id.get(e.src), by_id.get(e.dst)
        if not a or not b:
            continue
        stroke = "#ef5350" if e.failed else "#6b7a8d"
        sw = 2 if e.failed else 1.5
        dash = ' stroke-dasharray="6 3"' if e.failed else ""
        marker = "arrow-fail" if e.failed else "arrow"
        parts.append(
            f'<path d="{edge_path(a, b)}" fill="none" stroke="{stroke}" '
            f'stroke-width="{sw}"{dash} marker-end="url(#{marker})" '
            f'opacity="0.85"/>'
        )

    for n in nodes:
        fill, stroke, text = NODE_COLORS[n.type]
        has_fail = bool(n.failure_type)
        border = "#ef5350" if has_fail else stroke
        parts.append(
            f'<g transform="translate({n.x},{n.y})">'
            f'<rect width="{NODE_WIDTH}" height="{NODE_HEIGHT}" rx="6" ry="6" '
            f'fill="{fill}" stroke="{border}" stroke-width="1.5" opacity="0.95"/>'
            f'<text x="10" y="18" fill="{"#ef5350" if has_fail else text}" '
            f'font-size="11" font-weight="600" letter-spacing="0.4">'
            f"{xs.escape(n.label)}</text>"
            f'<text x="10" y="36" fill="#c9d4e0" font-size="11" '
            f'font-family="ui-monospace,SFMono-Regular,monospace">'
            f"{xs.escape(_truncate(n.detail, 26))}</text>"
        )
        meta_parts: list[str] = []
        if n.latency_ms is not None:
            meta_parts.append(f"{n.latency_ms:.0f}ms")
        if n.token_count is not None:
            meta_parts.append(f"{n.token_count} tok")
        if meta_parts:
            parts.append(
                f'<text x="10" y="54" fill="#6b7a8d" font-size="10">'
                f"{xs.escape('  ·  '.join(meta_parts))}</text>"
            )
        if has_fail:
            parts.append(
                f'<g transform="translate({NODE_WIDTH - 8},0)">'
                f'<circle r="5" fill="#ef5350"/>'
                f'<text y="3" text-anchor="middle" fill="#fff" font-size="8" '
                f'font-weight="700">!</text></g>'
            )
        parts.append("</g>")

    parts.append("</svg>")
    return "\n".join(parts)


async def render_run(run_id: str, out_path: Path) -> None:
    database_url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    engine = get_engine(database_url)
    sf = get_session_factory(engine)
    repo = SQLAlchemyRunRepository(sf)
    run = await repo.get_by_id(run_id)
    await engine.dispose()
    if run is None:
        print(f"  ! run {run_id} not found in {database_url}", file=sys.stderr)
        return
    nodes, edges, w, h = build_graph(run)
    svg = render_svg(nodes, edges, w, h)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(svg, encoding="utf-8")
    print(f"  - wrote {out_path}  ({w}x{h}, {len(nodes)} nodes, {len(edges)} edges)")


async def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    out_dir = repo_root / "docs" / "screenshots"
    print("Rendering Decision Graph SVGs:")
    await render_run("demo-fail-001", out_dir / "decision-graph-fail.svg")
    await render_run("demo-happy-001", out_dir / "decision-graph-happy.svg")
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
