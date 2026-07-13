from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import streamlit as st

from copilot.assistant import FanAssistant, FanProfile, OpsAssistant
from copilot.config import get_settings
from copilot.llm import build_llm
from copilot.telemetry import snapshot as telemetry_snapshot


DATA_DIR = Path(__file__).parent / "data"


def _init_state():
    if "fan_messages" not in st.session_state:
        st.session_state.fan_messages = []
    if "ops_messages" not in st.session_state:
        st.session_state.ops_messages = []

def _rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


def _llm_banner(llm):
    cols = st.columns([2, 1])
    cols[0].markdown(f"**LLM provider**: `{llm.name()}`")
    if llm.is_live():
        cols[1].success("Live")
    else:
        cols[1].warning("Mock")
        st.info(
            "To enable GenAI locally, install Ollama and run a model, e.g.\n\n"
            "- `ollama serve`\n"
            "- `ollama pull llama3.1`\n\n"
            "Or set `LLM_PROVIDER=openai` and export `OPENAI_API_KEY`."
        )


def _fan_page(*, llm, tournament: str, venue: str):
    st.subheader("Fan Assistant")
    st.caption("Multilingual, accessibility-aware navigation + crowd-aware reroutes (demo with simulated telemetry).")

    language = st.sidebar.selectbox("Language", ["English", "Spanish", "French", "Arabic"])
    accessibility = st.sidebar.selectbox(
        "Accessibility needs",
        ["None", "Wheelchair / mobility", "Hearing support", "Vision support", "Sensory-friendly"],
    )
    arriving_via = st.sidebar.selectbox("Arriving via", ["Transit", "Park & Ride", "Rideshare/Taxi"])
    from_location = st.sidebar.selectbox("Starting point", ["Central Station", "Park & Ride (Lot P)", "Rideshare / Taxi Drop-off"])
    destination = st.sidebar.selectbox(
        "Destination",
        [
            "My seat",
            "Section 120",
            "Guest Services & Accessibility Desk",
            "First Aid",
            "Sensory Relief Room",
            "Water Refill Station",
            "Waste Sorting / Recycling",
            "Gate A",
            "Gate B",
            "Gate C",
            "Gate D",
        ],
    )
    seat_section = st.sidebar.text_input("Seat section (if applicable)", value="120")

    profile = FanProfile(
        language=language,
        accessibility_needs=accessibility,
        arriving_via=arriving_via,
        from_location=from_location,
        destination=destination,
        seat_section=seat_section,
    )

    assistant = FanAssistant(llm=llm, data_dir=DATA_DIR, tournament=tournament, venue=venue)

    st.markdown("**Chat**")
    for m in st.session_state.fan_messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    user_text = st.chat_input("Ask for directions, accessible help, transport, or venue info…")
    if user_text:
        st.session_state.fan_messages.append({"role": "user", "content": user_text})
        with st.chat_message("user"):
            st.markdown(user_text)

        with st.chat_message("assistant"):
            with st.spinner("Generating guidance…"):
                reply = assistant.respond(user_text, profile)
                st.markdown(reply)
        st.session_state.fan_messages.append({"role": "assistant", "content": reply})

    with st.expander("Fan context (debug)"):
        st.json(asdict(profile))


def _ops_page(*, llm, tournament: str, venue: str):
    st.subheader("Ops Dashboard")
    st.caption("Crowd-risk snapshot + GenAI decision support (demo with simulated telemetry).")

    language = st.sidebar.selectbox("Response language", ["English", "Spanish", "French"], index=0)

    telem = telemetry_snapshot()
    gates = telem["gates"]
    gates_sorted = sorted(gates, key=lambda g: g["risk"], reverse=True)
    top = gates_sorted[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Highest risk gate", top["gate_label"])
    c2.metric("Risk score", f'{top["risk"]:.2f}')
    c3.metric("Queue (min)", f'{top["queue_min"]} (acc {top["accessible_queue_min"]})')

    st.markdown("**Gate telemetry**")
    st.dataframe(gates_sorted, use_container_width=True)

    st.markdown("**Heuristic suggested actions (input to GenAI)**")
    st.json(telem["heuristic_actions"])

    assistant = OpsAssistant(llm=llm, data_dir=DATA_DIR, tournament=tournament, venue=venue)

    st.markdown("**Ops Copilot**")
    for m in st.session_state.ops_messages:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    colA, colB = st.columns([3, 1])
    ops_text = colA.text_input("Ask an ops question", value="What should we do in the next 15 minutes to reduce congestion safely?")
    if colB.button("Generate plan"):
        st.session_state.ops_messages.append({"role": "user", "content": ops_text})
        reply = assistant.respond(ops_text, language=language)
        st.session_state.ops_messages.append({"role": "assistant", "content": reply})
        _rerun()

    if st.button("Generate shift briefing (last 30m)"):
        prompt = "Create a 60-second shift briefing from telemetry: top risks, actions, and comms. Include accessibility considerations."
        st.session_state.ops_messages.append({"role": "user", "content": prompt})
        reply = assistant.respond(prompt, language=language)
        st.session_state.ops_messages.append({"role": "assistant", "content": reply})
        _rerun()


def main():
    settings = get_settings()
    llm = build_llm(settings)

    st.set_page_config(page_title=settings.app_title, layout="wide")
    _init_state()

    st.title(settings.app_title)
    st.caption(f"Venue: **{settings.demo_venue_name}** • Tournament: **{settings.demo_tournament_name}**")
    _llm_banner(llm)

    mode = st.sidebar.radio("Mode", ["Fan Assistant", "Ops Dashboard"], index=0)

    if st.sidebar.button("Clear chat"):
        st.session_state.fan_messages = []
        st.session_state.ops_messages = []
        _rerun()

    if mode == "Fan Assistant":
        _fan_page(llm=llm, tournament=settings.demo_tournament_name, venue=settings.demo_venue_name)
    else:
        _ops_page(llm=llm, tournament=settings.demo_tournament_name, venue=settings.demo_venue_name)


if __name__ == "__main__":
    main()

