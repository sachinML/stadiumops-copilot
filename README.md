## StadiumOps Copilot (FIFA World Cup 2026)

GenAI-enabled copilot that enhances stadium operations and the tournament experience for **fans, organizers, volunteers, and venue staff** during FIFA World Cup 2026-style match days.

### Problem statement → feature mapping

| Challenge pillar | How this app addresses it |
|---|---|
| **Navigation** | Step-free/fastest route engine over a stadium graph (`copilot/routing.py`), turned into plain-language directions by the LLM |
| **Crowd management** | Simulated real-time gate density/queue/incident telemetry + risk scoring, surfaced in the Ops Dashboard |
| **Accessibility** | Step-free routing, accessible-queue timing, Sensory Relief Room + Guest Services routing, plus a WCAG-oriented UI (high-contrast/large-text modes, focus outlines) |
| **Transportation** | Transit / Park & Ride / Rideshare-aware routing and last-mile guidance |
| **Sustainability** | Live arrival-mode split (transit/park & ride/rideshare) and estimated CO2 avoided, shown in the Ops Dashboard; refill/waste-sorting guidance for fans |
| **Multilingual assistance** | Fan responses in English/Spanish/French/Arabic; Ops responses in English/Spanish/French |
| **Operational intelligence** | Per-gate risk scoring, incident counts, and prioritized heuristic actions feeding the GenAI layer |
| **Real-time decision support** | GenAI-generated 15-minute action plans and shift briefings grounded in the live telemetry snapshot |
| **Audience coverage** | **Fans** (Fan Assistant) and **Organizers / Volunteers / Venue Staff** (Ops Dashboard, with a "Viewing as" role selector) |

### What it delivers

- **Fan Assistant**
  - **Multilingual** help (English/Spanish/French/Arabic)
  - **Accessibility-aware navigation** (step-free routing, accessible queues, sensory support)
  - **Crowd-aware reroutes** using real-time (simulated) gate congestion/queue telemetry
  - **Transportation + sustainability nudges** (transit/park&ride, refill + waste sorting guidance)
- **Ops Dashboard**
  - **Real-time decision support**: gate risk ranking, queues, incidents (simulated telemetry)
  - **Sustainability snapshot**: arrival-mode split and estimated CO2 avoided
  - **Role-aware GenAI action plans**: 15-minute congestion reduction plan + push/PA comms snippet, tailored for Venue Staff / Volunteer / Organizer
  - **Shift briefing generation**: 60-second briefing from telemetry + playbook context



### How GenAI is used

- A **live LLM** generates natural-language guidance and operations recommendations.
- A lightweight **RAG layer** retrieves relevant playbook/venue policy excerpts from `data/knowledge/*.md` and injects them into the prompt.
- A small **routing engine** computes step-free vs fastest routes over a sample stadium graph (`data/stadium_map.json`) and feeds that route to the LLM for user-friendly directions.
- **Resilient by design**: if the LLM provider times out, rate-limits, or is unreachable, the app returns a clear fallback message instead of crashing (see `tests/test_llm_resilience.py`).



### Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```



### Run tests

```bash
source .venv/bin/activate
python -m unittest discover -s tests -p "test_*.py" -v
```



### Enable GenAI (choose one)



#### Option A: Ollama (recommended for local demo, no API key)

```bash
ollama serve
ollama pull llama3.1
export LLM_PROVIDER=ollama
export OLLAMA_MODEL=llama3.1
```



#### Option B: OpenAI-compatible

```bash
export LLM_PROVIDER=openai
export OPENAI_API_KEY="..."
export OPENAI_MODEL="gpt-4o-mini"
```

If no live LLM is reachable, the app runs in **mock mode** (UI still works, but responses won’t be genuinely generative).

### Deploy to Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. **New app** → repository `sachinML/stadiumops-copilot`, branch `main`, main file `app.py`.
3. In **Advanced settings → Secrets**, paste (optional, enables live GenAI on the cloud since Ollama isn't reachable there):

```toml
LLM_PROVIDER = "openai"
OPENAI_API_KEY = "sk-..."
OPENAI_MODEL = "gpt-4o-mini"
```

4. Click **Deploy**. You'll get a public URL to use as your "live preview" link.

### Accessibility & inclusive design

The app implements accessibility on two levels:

**1. Domain-level (stadium accessibility for fans)**
- Step-free routing engine (`copilot/routing.py`) that avoids stairs when a fan indicates a mobility need
- Accessible-queue timing surfaced alongside standard queue times in the Ops Dashboard
- Guest Services & Accessibility Desk, Sensory Relief Room routing and guidance
- Multilingual assistance (English/Spanish/French/Arabic)

**2. UI-level (WCAG-oriented interface design)**
- Sidebar **"High-contrast mode"** toggle (black/white/yellow palette, targets AAA-level contrast)
- Sidebar **"Large text mode"** toggle (WCAG 1.4.4 Resize Text)
- Always-visible, high-contrast keyboard focus outlines app-wide (WCAG 2.4.7 Focus Visible)
- No color-only indicators: status badges (e.g. "Live"/"Mock") always pair color with explicit text
- All interactive controls (buttons, selects, inputs) have explicit visible text labels — no icon-only controls
- Configured via `.streamlit/config.toml` with a WCAG AA-oriented default theme

### Suggested demo prompts

- Fan: “How do I get from Central Station to Section 120? I need a step-free route.”
- Fan: “Where is the sensory room and how crowded is the nearest gate right now?”
- Ops: “What should we do in the next 15 minutes to reduce congestion safely?”
- Ops: “Generate a short push notification to redirect fans away from the most congested gate.”

