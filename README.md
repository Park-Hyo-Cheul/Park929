# CDSS Project

Clinical Decision Support System for physicians.

## Minimal Reasoning Engine Prototype

This repo includes a minimal working prototype in `reasoning_engine.py` with:
- input validation (`validate_facts`, `validate_rules`)
- rule evaluation (`evaluate_rules`)
- explanation output (`EvaluationResult.explanation`)

## Streamlit UI

A clinician-facing UI is provided in `app.py` with two tabs:
- **Reasoning Engine** (rule-based CDSS)
- **Medical Q&A** (physician-facing structured EBM answers)

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### Optional environment variables (`.env`)

```bash
OPENAI_API_KEY=...
NCBI_EMAIL=you@example.com
NCBI_TOOL=cdss-medqna
```

### Quick run (engine only)

```bash
python reasoning_engine.py
```

### Run tests

```bash
pytest -q
```
