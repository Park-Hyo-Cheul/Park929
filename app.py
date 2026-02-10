"""Streamlit UI for the CDSS reasoning engine (clinician-facing)."""

from __future__ import annotations

import importlib
import inspect
from typing import Any

import streamlit as st
from dotenv import load_dotenv

from cdss.medqna.composer import compose_answer
from cdss.medqna.query_router import route_query
from cdss.medqna.retriever import retrieve_evidence
from reasoning_engine import Rule, run_engine

load_dotenv()


def _import_build_facts():
    """Return build_facts callable if the project provides one."""

    candidates = (
        "build_facts",
        "fact_builder",
        "facts",
        "reasoning_engine",
    )
    for module_name in candidates:
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue
        build_facts = getattr(module, "build_facts", None)
        if callable(build_facts):
            return build_facts
    return None


def _load_rules_from_registry(
    selected_packs: list[str],
    guideline_name: str | None,
    guideline_version: str | None,
) -> list[Rule]:
    """Load rules using registry.load_packs when available."""

    try:
        registry = importlib.import_module("registry")
    except ImportError:
        return []

    load_packs = getattr(registry, "load_packs", None)
    if not callable(load_packs):
        return []

    kwargs = {}
    if guideline_name:
        kwargs["guideline_name"] = guideline_name
    if guideline_version:
        kwargs["guideline_version"] = guideline_version

    try:
        packs = load_packs(selected_packs, **kwargs)
    except TypeError:
        try:
            packs = load_packs(selected_packs)
        except Exception:
            return []
    except Exception:
        return []

    if packs is None:
        return []

    if isinstance(packs, list) and all(isinstance(rule, Rule) for rule in packs):
        return packs

    rules: list[Rule] = []
    if isinstance(packs, dict):
        for pack in packs.values():
            if isinstance(pack, dict) and isinstance(pack.get("rules"), list):
                rules.extend([rule for rule in pack["rules"] if isinstance(rule, Rule)])
    return rules


def _fallback_rules() -> list[Rule]:
    return [
        Rule(
            id="htn_stage2",
            description="Detect blood pressure pattern suggestive of stage 2 hypertension",
            condition=lambda f: f.get("systolic_bp", 0) >= 140 or f.get("diastolic_bp", 0) >= 90,
            outcome={
                "category": "hypertension",
                "suggestion": "Consider confirming elevated blood pressure with repeat measurements and guideline-based assessment.",
                "severity": "moderate",
            },
        ),
        Rule(
            id="htn_pregnancy_flag",
            description="Flag elevated blood pressure in pregnancy",
            condition=lambda f: bool(f.get("pregnancy"))
            and (f.get("systolic_bp", 0) >= 140 or f.get("diastolic_bp", 0) >= 90),
            outcome={
                "category": "maternal-safety",
                "suggestion": "Use pregnancy-specific hypertension pathways and local obstetric protocols.",
                "severity": "high",
            },
        ),
    ]


def _normalize_labs(facts: dict[str, Any], normalize: bool) -> dict[str, Any]:
    if not normalize:
        return facts

    normalized = dict(facts)
    creatinine = facts.get("creatinine")
    if creatinine is not None and facts.get("creatinine_unit") == "µmol/L":
        normalized["creatinine_mg_dl"] = round(creatinine / 88.4, 3)
    elif creatinine is not None:
        normalized["creatinine_mg_dl"] = creatinine

    glucose = facts.get("glucose")
    if glucose is not None and facts.get("glucose_unit") == "mmol/L":
        normalized["glucose_mg_dl"] = round(glucose * 18.0, 2)
    elif glucose is not None:
        normalized["glucose_mg_dl"] = glucose

    return normalized


def _build_facts(raw_facts: dict[str, Any]) -> dict[str, Any]:
    build_facts = _import_build_facts()
    if not build_facts:
        return raw_facts

    try:
        signature = inspect.signature(build_facts)
        if len(signature.parameters) == 1:
            return build_facts(raw_facts)
        return build_facts(**raw_facts)
    except Exception:
        return raw_facts


def _warning_messages(facts: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if facts.get("systolic_bp", 0) >= 180 or facts.get("diastolic_bp", 0) >= 120:
        warnings.append(
            "Marked blood pressure elevation detected. This output is an informational clinical signal; perform urgent clinician assessment per protocol."
        )
    if facts.get("ckd_stage") in {"4", "5"}:
        warnings.append(
            "Advanced CKD context detected; consider renal dosing, nephrology guidance, and local pathway constraints when interpreting suggestions."
        )
    return warnings


def _render_reasoning_engine_tab() -> None:
    with st.form("cdss_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            age = st.number_input("Age", min_value=0, max_value=130, step=1, value=45)
            sex = st.selectbox("Sex", options=["female", "male", "intersex", "other", "unknown"], index=0)
            diabetes = st.checkbox("Diabetes", value=False)
            pregnancy = st.checkbox("Pregnancy", value=False)

        with c2:
            systolic_bp = st.number_input("Systolic BP (mmHg)", min_value=50, max_value=300, value=130)
            diastolic_bp = st.number_input("Diastolic BP (mmHg)", min_value=30, max_value=200, value=80)
            ckd_stage = st.selectbox("CKD stage", options=["None", "1", "2", "3", "4", "5"], index=0)

        with c3:
            creatinine = st.number_input("Creatinine (optional)", min_value=0.0, step=0.1, value=0.0)
            creatinine_unit = st.selectbox("Creatinine unit", options=["mg/dL", "µmol/L"], index=0)
            glucose = st.number_input("Glucose (optional)", min_value=0.0, step=0.1, value=0.0)
            glucose_unit = st.selectbox("Glucose unit", options=["mg/dL", "mmol/L"], index=0)

        st.subheader("Pack selection")
        packs = st.multiselect(
            "Select pack(s)",
            options=["hypertension", "diabetes", "ckd", "pregnancy"],
            default=["hypertension"],
        )

        g1, g2, g3 = st.columns(3)
        with g1:
            guideline_name = st.selectbox(
                "Guideline name (optional)", options=["", "ACC/AHA", "ESC/ESH", "NICE", "KDIGO"], index=0
            )
        with g2:
            guideline_name_custom = st.text_input("Or enter guideline name")
        with g3:
            guideline_version = st.text_input("Guideline version (optional)", placeholder="e.g., 2024")

        normalize = st.toggle("Normalize lab units", value=True)
        run_clicked = st.form_submit_button("Run")

    if not run_clicked:
        return

    selected_guideline = guideline_name_custom.strip() or guideline_name.strip() or None
    version = guideline_version.strip() or None
    raw_facts: dict[str, Any] = {
        "age": int(age),
        "sex": sex,
        "systolic_bp": int(systolic_bp),
        "diastolic_bp": int(diastolic_bp),
        "diabetes": diabetes,
        "ckd_stage": None if ckd_stage == "None" else ckd_stage,
        "pregnancy": pregnancy,
    }

    if creatinine > 0:
        raw_facts["creatinine"] = float(creatinine)
        raw_facts["creatinine_unit"] = creatinine_unit
    if glucose > 0:
        raw_facts["glucose"] = float(glucose)
        raw_facts["glucose_unit"] = glucose_unit

    facts = _normalize_labs(_build_facts(raw_facts), normalize)
    rules = _load_rules_from_registry(packs or ["hypertension"], selected_guideline, version)
    if not rules:
        st.info("Using built-in fallback pack because no registry packs were loaded.")
        rules = _fallback_rules()

    try:
        result = run_engine(facts, rules, required_fields=["age", "sex", "systolic_bp", "diastolic_bp"])
    except Exception as exc:
        st.error(f"Engine execution failed: {exc}")
        return

    st.subheader("Clinical suggestions (matched outcomes)")
    st.table(result.matched_outcomes) if result.matched_outcomes else st.write("No suggestions matched current facts.")

    st.subheader("Explanations")
    for item in result.explanation:
        with st.expander(f"{item.rule_id} — {'matched' if item.matched else 'not matched'}", expanded=False):
            st.write(item.description)
            st.json({"matched": item.matched, "outcome": item.outcome})

    st.subheader("Warnings")
    for warning in _warning_messages(facts) or ["No additional warning-tier signals detected."]:
        st.info(warning)


def _render_medical_qna_tab() -> None:
    st.caption("Medical reference only. Not patient-specific medical advice.")

    with st.form("medqna_form"):
        question = st.text_area("Question", placeholder="e.g., Initial management of new-onset HFrEF?")
        specialty = st.selectbox(
            "Specialty",
            options=["general", "cardiology", "endocrinology", "nephrology", "oncology", "rheumatology", "all"],
            index=0,
        )
        mcq_mode = st.checkbox("MCQ mode", value=False)
        choices_raw = st.text_area("Choices (one per line, optional)", placeholder="A) ...\nB) ...")
        user_links_raw = st.text_area("Guideline links (optional, one per line)")
        ask_clicked = st.form_submit_button("Answer")

    if not ask_clicked or not question.strip():
        return

    choices = [line.strip() for line in choices_raw.splitlines() if line.strip()]
    user_links = [line.strip() for line in user_links_raw.splitlines() if line.strip()]
    query_type = route_query(question, mcq_mode=mcq_mode, choices=choices)

    with st.spinner("Retrieving PubMed and guideline evidence..."):
        evidence = retrieve_evidence(question=question, specialty=specialty, user_guideline_links=user_links)
        answer = compose_answer(question, query_type, evidence, specialty=specialty, mcq_choices=choices)

    st.markdown("### Pathophysiology")
    st.write(answer.pathophysiology)
    st.markdown("### Clinical Features")
    st.write(answer.clinical_features)
    st.markdown("### Diagnosis")
    st.write(answer.diagnosis)
    st.markdown("### Treatment")
    st.write(answer.treatment)
    st.markdown("### Latest Evidence")
    st.write(answer.latest_evidence)
    st.markdown("### Confidence")
    st.write(answer.confidence_statement)

    if answer.mcq_explanations:
        st.markdown("### MCQ Option Review")
        for option in answer.mcq_explanations:
            verdict = "✅ Correct" if option.is_correct else "• Not selected"
            st.write(f"**{option.option}** — {verdict}: {option.explanation}")

    st.markdown("### Citations")
    for citation in answer.citations:
        label = f"{citation.source} — {citation.title}"
        if citation.year:
            label += f" ({citation.year})"
        if citation.note:
            label += f" [{citation.note}]"
        st.write(f"- {label}")
        if citation.url:
            st.write(citation.url)

    if answer.notes:
        st.warning("; ".join(answer.notes))


st.set_page_config(page_title="CDSS Reasoning UI", layout="wide")
st.title("CDSS Reasoning Engine")
st.caption("For clinician use only (not patient advice).")
st.info(
    "Outputs are clinical suggestions with rationale and metadata. They are not direct patient instructions and do not replace clinician judgment."
)

reasoning_tab, medqna_tab = st.tabs(["Reasoning Engine", "Medical Q&A"])
with reasoning_tab:
    _render_reasoning_engine_tab()
with medqna_tab:
    _render_medical_qna_tab()

st.caption(
    "These outputs are for clinician interpretation only. Apply local protocols, confirmatory evaluation, and patient-specific context before acting."
)
