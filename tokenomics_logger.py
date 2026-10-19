"""
tokenomics_logger.py -- structured logging and full-chain tracing for the
orchestrator, kept separate from orchestrator.py itself, the same way
bedrock_client.py stays separate from every agent that calls it.
"""
import json
import uuid
from datetime import datetime
from orchestrator import route_question

# Claude Sonnet 4.6 on Amazon Bedrock (us-east-1, on-demand pricing)
# https://aws.amazon.com/bedrock/pricing/
INPUT_COST_PER_1M  = 3.00
OUTPUT_COST_PER_1M = 15.00

_query_log = []


def cost_usd(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens / 1_000_000) * INPUT_COST_PER_1M + \
           (output_tokens / 1_000_000) * OUTPUT_COST_PER_1M


def log_decision(stage: str, question: str, details: dict):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "stage": stage,
        "question": question,
        "details": details
    }
    print(f"[LOG] {stage}: {json.dumps(details)}")
    with open("/tmp/agent_decisions.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")


def route_question_logged(state):
    result = route_question(state)
    log_decision("routing", state["question"], {"route": result["route"]})
    return result


def run_traced_query(orchestrator, question: str) -> dict:
    trace_id = str(uuid.uuid4())[:8]
    log_decision("query_start", question, {"trace_id": trace_id})

    result = orchestrator.invoke({
        "question": question, "route": None, "sql_result": None,
        "retrieval_result": None, "final_answer": None, "token_usage": None
    })

    sql_usage      = result.get("sql_result", {}).get("metadata", {}).get("token_usage") if result.get("sql_result") else None
    ret_usage      = result.get("retrieval_result", {}).get("metadata", {}).get("token_usage") if result.get("retrieval_result") else None
    synth_usage    = result.get("token_usage") or {"input": 0, "output": 0}

    components = {}
    if sql_usage:
        components["sql"] = {**sql_usage, "cost_usd": cost_usd(sql_usage["input"], sql_usage["output"])}
    if ret_usage:
        components["retrieval"] = {**ret_usage, "cost_usd": cost_usd(ret_usage["input"], ret_usage["output"])}
    components["synthesis"] = {**synth_usage, "cost_usd": cost_usd(synth_usage["input"], synth_usage["output"])}

    total_input  = sum(c["input"]  for c in components.values())
    total_output = sum(c["output"] for c in components.values())
    total_cost   = cost_usd(total_input, total_output)

    print(f"\n--- Token usage for: {question[:60]} ---")
    for name, c in components.items():
        print(f"  {name:12s}  in={c['input']:5d}  out={c['output']:5d}  cost=${c['cost_usd']:.6f}")
    print(f"  {'TOTAL':12s}  in={total_input:5d}  out={total_output:5d}  cost=${total_cost:.6f}")

    log_decision("query_complete", question, {
        "trace_id": trace_id,
        "route": result["route"],
        "sql_validation": result.get("sql_result", {}).get("metadata", {}).get("validation") if result.get("sql_result") else None,
        "components": components,
        "total_cost_usd": total_cost,
    })

    _query_log.append({
        "question": question,
        "route": result["route"],
        "components": components,
        "total_cost_usd": total_cost,
    })

    return result


def print_cost_summary():
    if not _query_log:
        print("No queries logged yet.")
        return

    print("\n" + "=" * 70)
    print(f"{'TOKENOMICS SUMMARY':^70}")
    print("=" * 70)
    print(f"{'#':<3} {'Route':<12} {'SQL in/out':>12} {'Ret in/out':>12} {'Synth in/out':>14} {'Total $':>10}")
    print("-" * 70)

    component_totals = {"sql": {"input": 0, "output": 0, "cost_usd": 0},
                        "retrieval": {"input": 0, "output": 0, "cost_usd": 0},
                        "synthesis": {"input": 0, "output": 0, "cost_usd": 0}}
    grand_total = 0.0

    for i, q in enumerate(_query_log, 1):
        c = q["components"]
        sql_str   = f"{c['sql']['input']}/{c['sql']['output']}"         if "sql"       in c else "-/-"
        ret_str   = f"{c['retrieval']['input']}/{c['retrieval']['output']}" if "retrieval" in c else "-/-"
        syn_str   = f"{c['synthesis']['input']}/{c['synthesis']['output']}"
        print(f"{i:<3} {q['route']:<12} {sql_str:>12} {ret_str:>12} {syn_str:>14} ${q['total_cost_usd']:>9.6f}")
        grand_total += q["total_cost_usd"]
        for name in component_totals:
            if name in c:
                component_totals[name]["input"]    += c[name]["input"]
                component_totals[name]["output"]   += c[name]["output"]
                component_totals[name]["cost_usd"] += c[name]["cost_usd"]

    print("-" * 70)
    print(f"{'GRAND TOTAL':>53}  ${grand_total:>9.6f}")

    top = max(component_totals, key=lambda k: component_totals[k]["cost_usd"])
    print(f"\nHighest-cost component: {top} (${component_totals[top]['cost_usd']:.6f})")
    print("=" * 70)
