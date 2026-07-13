from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math
import random
from typing import Any


GATES = [
    {"id": "GATE_A", "label": "Gate A (North Plaza)"},
    {"id": "GATE_B", "label": "Gate B (East Transit)"},
    {"id": "GATE_C", "label": "Gate C (South Drop-off)"},
    {"id": "GATE_D", "label": "Gate D (West Parking)"},
]


@dataclass(frozen=True)
class GateMetric:
    gate_id: str
    gate_label: str
    density: float  # 0..1
    queue_min: int
    accessible_queue_min: int
    incidents_last_30m: int

    @property
    def risk(self) -> float:
        # Simple blended risk score; in production this would be a learned model.
        return min(1.0, 0.55 * self.density + 0.35 * (self.queue_min / 45.0) + 0.10 * (self.incidents_last_30m / 6.0))


def _time_bucket(now: datetime, minutes: int = 2) -> int:
    epoch = int(now.replace(tzinfo=timezone.utc).timestamp())
    return epoch // (minutes * 60)


def get_gate_metrics(now: datetime) -> list[GateMetric]:
    bucket = _time_bucket(now, minutes=2)
    rng = random.Random(2026_000_000 + bucket)

    # Match-day arrival wave (peaks ~60-20 minutes before kickoff)
    minute_of_hour = now.minute + now.second / 60.0
    wave = 0.5 + 0.5 * math.sin((minute_of_hour / 60.0) * 2 * math.pi)

    out: list[GateMetric] = []
    for i, g in enumerate(GATES):
        base = 0.35 + 0.25 * wave + rng.random() * 0.15
        gate_bias = (i - 1.5) * 0.05  # different attractiveness
        density = max(0.0, min(1.0, base + gate_bias + rng.random() * 0.10))
        queue = int(round(5 + 38 * density + rng.random() * 4))
        acc_queue = int(round(queue * (0.75 + rng.random() * 0.20)))
        incidents = int(rng.random() * (1 + 5 * max(0.0, density - 0.7)))
        out.append(
            GateMetric(
                gate_id=g["id"],
                gate_label=g["label"],
                density=density,
                queue_min=queue,
                accessible_queue_min=acc_queue,
                incidents_last_30m=incidents,
            )
        )

    return out


def recommend_ops_actions(metrics: list[GateMetric]) -> list[dict[str, Any]]:
    """
    Heuristic action suggestions to feed the GenAI summarizer.
    """
    actions: list[dict[str, Any]] = []
    for m in sorted(metrics, key=lambda x: x.risk, reverse=True):
        if m.risk >= 0.80:
            actions.append(
                {
                    "gate": m.gate_label,
                    "priority": "P1",
                    "suggestion": "Redeploy 2–3 volunteers for wayfinding + queue splitting; open overflow screening lane if available; push app notification to redirect arrivals.",
                }
            )
        elif m.risk >= 0.65:
            actions.append(
                {
                    "gate": m.gate_label,
                    "priority": "P2",
                    "suggestion": "Increase signage, start 'arrive prepared' messaging, and coordinate with transit/parking stewards to stagger flows.",
                }
            )
        elif m.risk >= 0.50:
            actions.append(
                {
                    "gate": m.gate_label,
                    "priority": "P3",
                    "suggestion": "Monitor for surges; ensure accessible queue is clearly marked and staffed.",
                }
            )
    return actions


def snapshot(now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(tz=timezone.utc)
    gates = get_gate_metrics(now)
    return {
        "ts": now.isoformat(),
        "gates": [
            {
                "gate_id": g.gate_id,
                "gate_label": g.gate_label,
                "density": round(g.density, 3),
                "queue_min": g.queue_min,
                "accessible_queue_min": g.accessible_queue_min,
                "incidents_last_30m": g.incidents_last_30m,
                "risk": round(g.risk, 3),
            }
            for g in gates
        ],
        "heuristic_actions": recommend_ops_actions(gates),
    }

