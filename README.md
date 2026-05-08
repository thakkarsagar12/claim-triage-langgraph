# Claim Triage Agent

A LangGraph agent that triages InsurTech health insurance claims into one of three queues: **fast-track**, **standard**, or **fraud-review**.

Built as a small, focused demonstration of multi-node agent orchestration with LangGraph. Single LLM call per node. CLI-driven. No web UI, no database, no auth.

## Why

Most insurance claim systems route on rigid rules. This agent uses an LLM at each decision point — severity assessment, fraud signal detection, final routing — and produces a transparent reasoning trace alongside the decision.

## Architecture

```
input claim
   ↓
[ severity_classifier ]      → low | medium | high
   ↓
[ fraud_signal_detector ]    → fraud_flags[] + fraud_score (0–1)
   ↓
[ route_decision ]           → fast_track | standard | fraud_review
   ↓
output (decision + reasoning_trace)
```

3 nodes. 1 LLM call per node. State carried as a `TypedDict`.

## State Schema

```python
class TriageState(TypedDict):
    claim_id: str
    claim_text: str
    claim_amount: float
    severity: Literal["low", "medium", "high"] | None
    fraud_flags: list[str]
    fraud_score: float | None
    decision: Literal["fast_track", "standard", "fraud_review"] | None
    reasoning_trace: list[str]
```

## Quick Start

```bash
git clone git@github.com:thakkarsagar12/claim-triage-langgraph.git
cd claim-triage-langgraph
python3 -m venv .venv && source .venv/bin/activate
pip install langgraph langchain-anthropic python-dotenv

# set your Anthropic key
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

python triage.py
```

## Sample Output

(Coming once `triage.py` is wired up — May 9.)

## Status

Sprint in progress. Hard ship date: **2026-05-10 23:59 IST**.

- [x] Repo scaffolded
- [ ] State schema + 3 nodes wired
- [ ] 5 synthetic claims running end-to-end
- [ ] Mermaid architecture diagram
- [ ] Blog post on sagarthakkar.com

## License

MIT
