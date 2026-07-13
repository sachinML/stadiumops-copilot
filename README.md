## StadiumOps Copilot (FIFA World Cup 2026)

GenAI-enabled copilot that improves **stadium navigation + crowd operations** for FIFA World Cup 2026-style match days.

### What it delivers

- **Fan Assistant**
  - **Multilingual** help (English/Spanish/French/Arabic)
  - **Accessibility-aware navigation** (step-free routing, accessible queues, sensory support)
  - **Crowd-aware reroutes** using real-time (simulated) gate congestion/queue telemetry
  - **Transportation + sustainability nudges** (transit/park&ride, refill + waste sorting guidance)
- **Ops Dashboard**
  - **Real-time decision support**: gate risk ranking, queues, incidents (simulated telemetry)
  - **GenAI action plans**: 15-minute congestion reduction plan + push/PA comms snippet
  - **Shift briefing generation**: 60-second briefing from telemetry + playbook context



### How GenAI is used

- A **live LLM** generates natural-language guidance and operations recommendations.
- A lightweight **RAG layer** retrieves relevant playbook/venue policy excerpts from `data/knowledge/*.md` and injects them into the prompt.
- A small **routing engine** computes step-free vs fastest routes over a sample stadium graph (`data/stadium_map.json`) and feeds that route to the LLM for user-friendly directions.



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

### Suggested demo prompts

- Fan: “How do I get from Central Station to Section 120? I need a step-free route.”
- Fan: “Where is the sensory room and how crowded is the nearest gate right now?”
- Ops: “What should we do in the next 15 minutes to reduce congestion safely?”
- Ops: “Generate a short push notification to redirect fans away from the most congested gate.”
