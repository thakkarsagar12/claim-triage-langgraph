"""Claim triage agent — LangGraph 3-node pipeline.

Runs against any OpenAI-compatible LLM endpoint (LM Studio, Ollama, vLLM, etc.).
Defaults to a local server on http://localhost:1234/v1 (LM Studio default).

Nodes:
    severity_classifier   -> low | medium | high
    fraud_signal_detector -> fraud_flags[] + fraud_score (0-1)
    route_decision        -> fast_track | standard | fraud_review

Run:
    python triage.py
"""

import json
import os
import re
import sys
from typing import Literal, Optional, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from claims import CLAIMS

load_dotenv()

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:1234/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "google/gemma-2-9b-it")
LLM_API_KEY = os.getenv("LLM_API_KEY", "local-no-key-needed")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))

LLM = ChatOpenAI(
    base_url=LLM_BASE_URL,
    api_key=LLM_API_KEY,
    model=LLM_MODEL,
    temperature=LLM_TEMPERATURE,
)


class TriageState(TypedDict):
    claim_id: str
    claim_text: str
    claim_amount: float
    severity: Optional[Literal["low", "medium", "high"]]
    fraud_flags: list[str]
    fraud_score: Optional[float]
    decision: Optional[Literal["fast_track", "standard", "fraud_review"]]
    reasoning_trace: list[str]


def _ask_json(prompt: str) -> dict:
    """One-shot LLM call that expects a JSON object back."""
    response = LLM.invoke([HumanMessage(content=prompt)])
    return _parse_json(response.content)


def _parse_json(raw: str) -> dict:
    """Strip optional code fences / prose and parse a JSON object."""
    s = raw.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", s, re.DOTALL)
    if fence_match:
        s = fence_match.group(1)
    else:
        obj_match = re.search(r"\{.*\}", s, re.DOTALL)
        if obj_match:
            s = obj_match.group(0)
    return json.loads(s)


def severity_classifier(state: TriageState) -> TriageState:
    prompt = f"""You are an insurance claim triager for an Indian health insurer.
Classify this claim's severity.

Claim ID    : {state['claim_id']}
Claim text  : {state['claim_text']}
Amount (INR): {state['claim_amount']:,.2f}

Severity rubric:
- low    : routine, low amount, low complexity, no urgency
- medium : moderate amount or complexity, multi-step processing
- high   : large amount, complex, urgent, or life-threatening

Respond ONLY with a JSON object of the shape:
{{"severity": "low|medium|high", "reason": "<one short sentence>"}}
"""
    data = _ask_json(prompt)
    state["severity"] = data["severity"]
    state["reasoning_trace"].append(
        f"[severity] {data['severity']} - {data['reason']}"
    )
    return state


def fraud_signal_detector(state: TriageState) -> TriageState:
    prompt = f"""You are an insurance fraud analyst.
Identify fraud signals in this claim.

Claim ID    : {state['claim_id']}
Claim text  : {state['claim_text']}
Amount (INR): {state['claim_amount']:,.2f}

Look for: documentation gaps, repeated claim patterns, inconsistent records,
unverifiable line items, vague descriptions, and suspicious timing.

Respond ONLY with a JSON object of the shape:
{{"fraud_flags": ["<flag1>", "<flag2>"], "fraud_score": 0.0, "reason": "<one short sentence>"}}

fraud_score must be a float between 0.0 (clean) and 1.0 (very suspicious).
Use [] for fraud_flags if none.
"""
    data = _ask_json(prompt)
    state["fraud_flags"] = data["fraud_flags"]
    state["fraud_score"] = float(data["fraud_score"])
    state["reasoning_trace"].append(
        f"[fraud] score={data['fraud_score']} flags={data['fraud_flags']} - {data['reason']}"
    )
    return state


def route_decision(state: TriageState) -> TriageState:
    prompt = f"""You are an insurance claim router.
Decide the routing queue using the inputs below.

Severity   : {state['severity']}
Fraud score: {state['fraud_score']}
Fraud flags: {state['fraud_flags']}
Amount     : {state['claim_amount']:,.2f}

Routing rules:
- fraud_review : fraud_score >= 0.6, OR multiple serious fraud flags
- fast_track   : low severity, fraud_score < 0.2, complete documentation, no flags
- standard     : everything else

Respond ONLY with a JSON object of the shape:
{{"decision": "fast_track|standard|fraud_review", "reason": "<one short sentence>"}}
"""
    data = _ask_json(prompt)
    state["decision"] = data["decision"]
    state["reasoning_trace"].append(
        f"[decision] {data['decision']} - {data['reason']}"
    )
    return state


def build_graph():
    g = StateGraph(TriageState)
    g.add_node("severity", severity_classifier)
    g.add_node("fraud", fraud_signal_detector)
    g.add_node("route", route_decision)
    g.add_edge(START, "severity")
    g.add_edge("severity", "fraud")
    g.add_edge("fraud", "route")
    g.add_edge("route", END)
    return g.compile()


def initial_state(claim: dict) -> TriageState:
    return {
        "claim_id": claim["claim_id"],
        "claim_text": claim["claim_text"],
        "claim_amount": claim["claim_amount"],
        "severity": None,
        "fraud_flags": [],
        "fraud_score": None,
        "decision": None,
        "reasoning_trace": [],
    }


def run_one(claim: dict) -> TriageState:
    return build_graph().invoke(initial_state(claim))


def main() -> None:
    print(f"LLM base URL : {LLM_BASE_URL}")
    print(f"LLM model    : {LLM_MODEL}")
    print(f"Claims to run: {len(CLAIMS)}")
    print()

    graph = build_graph()
    for claim in CLAIMS:
        print(f"=== {claim['claim_id']} ===")
        print(f"Amount: INR {claim['claim_amount']:,.2f}")
        print(f"Text  : {claim['claim_text'][:110]}...")

        try:
            result = graph.invoke(initial_state(claim))
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR: {exc}")
            print()
            continue

        print(f"  severity   : {result['severity']}")
        print(f"  fraud_score: {result['fraud_score']}")
        print(f"  fraud_flags: {result['fraud_flags']}")
        print(f"  DECISION   : {(result['decision'] or '').upper()}")
        print("  trace:")
        for line in result["reasoning_trace"]:
            print(f"    - {line}")
        print()


if __name__ == "__main__":
    sys.exit(main())
