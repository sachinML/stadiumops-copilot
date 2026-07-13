from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re

from .llm import ChatMessage, LLM
from .rag import format_retrieved
from .routing import explain_path, load_stadium_map, resolve_start_goal, shortest_path
from .telemetry import snapshot as telemetry_snapshot
from .data import load_kb, load_pois


@dataclass(frozen=True)
class FanProfile:
    language: str = "English"
    accessibility_needs: str = "None"
    arriving_via: str = "Transit"
    from_location: str = "Central Station"
    destination: str = "My seat"
    seat_section: str = "120"


def _fan_system_prompt(*, tournament: str, venue: str, language: str) -> str:
    return f"""You are StadiumOps Copilot, a GenAI assistant for the {tournament}.
You help fans inside and around {venue} with:
- navigation/wayfinding and reroutes based on gate congestion
- accessibility-aware guidance (step-free routes, accessible queues, sensory-friendly options)
- transportation and last-mile guidance
- multilingual assistance
- sustainability nudges (low-carbon options, refill stations, waste sorting)

Rules:
- Respond in {language}.
- Be concise and action-oriented.
- If you provide directions, give numbered steps and include estimated minutes.
- If the user mentions accessibility needs, prioritize step-free routes and accessible queues.
- If you’re missing a key detail, ask 1 clarifying question at the end (only if necessary).
"""


def _ops_system_prompt(*, tournament: str, venue: str, language: str, role: str) -> str:
    return f"""You are StadiumOps Copilot, a GenAI operations assistant advising a {role} during {tournament} at {venue}.
You turn real-time telemetry into decisions for crowd management, safety, accessibility, transport, and sustainability.

Rules:
- Respond in {language}.
- Tailor tone and level of detail to a {role} (e.g. Volunteers need simple, immediate actions; Organizers may want the "why" behind a decision too).
- Use short headings and bullet points.
- Be specific (which gate, what action, who should do it, within what time).
- If risks are high, propose a 15-minute action plan and a comms snippet for push notifications + PA.
"""


class FanAssistant:
    def __init__(self, *, llm: LLM, data_dir: str | Path, tournament: str, venue: str):
        self._llm = llm
        self._data_dir = Path(data_dir)
        self._tournament = tournament
        self._venue = venue
        self._poi = load_pois(self._data_dir)
        self._smap = load_stadium_map(self._data_dir)
        self._kb_index, self._kb_chunks = load_kb(self._data_dir)

    def respond(self, user_text: str, profile: FanProfile) -> str:
        telem = telemetry_snapshot()
        retrieved = self._kb_index.search(user_text, k=4)
        kb_context = format_retrieved([c for c, _s in retrieved])

        # Try to compute a route if user asks for directions.
        route_block = ""
        if any(k in user_text.lower() for k in ["where", "how do i get", "directions", "route", "navigate", "way to"]):
            from_hint, to_hint = self._extract_route_hints(user_text)
            from_hint = from_hint or profile.from_location
            to_hint = to_hint or (
                profile.destination if profile.destination != "My seat" else f"Section {profile.seat_section}"
            )
            start_node, goal_node = resolve_start_goal(
                smap=self._smap,
                from_hint=from_hint,
                to_hint=to_hint,
                poi_index=self._poi,
            )
            if start_node and goal_node:
                require_accessible = profile.accessibility_needs.strip().lower() not in {"none", "no", "n/a"}
                path, minutes = shortest_path(
                    self._smap, start=start_node, goal=goal_node, require_accessible=require_accessible
                )
                steps = explain_path(self._smap, path)
                if steps:
                    route_block = json.dumps(
                        {
                            "from": self._smap.nodes[start_node].label,
                            "to": self._smap.nodes[goal_node].label,
                            "estimated_minutes": round(minutes, 1),
                            "steps": steps,
                            "accessible": require_accessible,
                        },
                        indent=2,
                    )

        messages = [
            ChatMessage(
                role="system",
                content=_fan_system_prompt(
                    tournament=self._tournament, venue=self._venue, language=profile.language
                ),
            ),
            ChatMessage(
                role="user",
                content=(
                    "Fan context:\n"
                    + json.dumps(
                        {
                            "accessibility_needs": profile.accessibility_needs,
                            "arriving_via": profile.arriving_via,
                            "from_location": profile.from_location,
                            "destination": profile.destination,
                            "seat_section": profile.seat_section,
                            "llm_provider": self._llm.name(),
                        },
                        indent=2,
                    )
                    + "\n\n"
                    "Real-time telemetry snapshot (simulated):\n"
                    + json.dumps(telem, indent=2)
                    + "\n\n"
                    + ("Candidate route (computed):\n" + route_block + "\n\n" if route_block else "")
                    + ("Relevant venue knowledge:\n" + kb_context + "\n\n" if kb_context else "")
                    + "User message:\n"
                    + user_text
                ),
            ),
        ]
        return self._llm.chat(messages, temperature=0.2).strip()

    @staticmethod
    def _extract_route_hints(user_text: str) -> tuple[str | None, str | None]:
        # Very lightweight parsing. The LLM still decides the final response.
        m = re.search(r"\bfrom\s+(.+?)\s+\bto\s+(.+)$", user_text.strip(), flags=re.IGNORECASE)
        if m:
            return m.group(1).strip().strip(".,"), m.group(2).strip().strip(".,")
        m = re.search(r"\bto\s+(.+)$", user_text.strip(), flags=re.IGNORECASE)
        if m:
            return None, m.group(1).strip().strip(".,")
        return None, None


class OpsAssistant:
    def __init__(self, *, llm: LLM, data_dir: str | Path, tournament: str, venue: str):
        self._llm = llm
        self._data_dir = Path(data_dir)
        self._tournament = tournament
        self._venue = venue
        self._kb_index, self._kb_chunks = load_kb(self._data_dir)

    def respond(self, user_text: str, *, language: str = "English", role: str = "Venue Staff") -> str:
        telem = telemetry_snapshot()
        retrieved = self._kb_index.search(user_text, k=4)
        kb_context = format_retrieved([c for c, _s in retrieved])

        messages = [
            ChatMessage(
                role="system",
                content=_ops_system_prompt(
                    tournament=self._tournament, venue=self._venue, language=language, role=role
                ),
            ),
            ChatMessage(
                role="user",
                content=(
                    "Real-time telemetry snapshot (simulated):\n"
                    + json.dumps(telem, indent=2)
                    + "\n\n"
                    + ("Relevant playbook excerpts:\n" + kb_context + "\n\n" if kb_context else "")
                    + "Ops question:\n"
                    + user_text
                ),
            ),
        ]
        return self._llm.chat(messages, temperature=0.2).strip()

