# CDSS Project

Clinical Decision Support System for physicians.

## Minimal Reasoning Engine Prototype

This repo now includes a minimal working prototype in `reasoning_engine.py` with:
- input validation (`validate_facts`, `validate_rules`)
- rule evaluation (`evaluate_rules`)
- explanation output (`EvaluationResult.explanation`)

### Quick run

```bash
python reasoning_engine.py
```

### Run tests

```bash
pytest -q
```
