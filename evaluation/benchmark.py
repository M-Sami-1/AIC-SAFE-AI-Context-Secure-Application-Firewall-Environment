from __future__ import annotations

import argparse
import csv

import config
from aic_safe.llm import MockLLM
from aic_safe.middleware import AICSafePipeline, run_unprotected
from aic_safe.middleware.logger import SecurityLogger
from aic_safe.runtime import enforce_project_venv, log_run
from dataset.build_dataset import build_dataset
from evaluation.metrics import calculate_metrics, write_metrics


def run(limit: int | None = None) -> tuple[list[dict], dict]:
    enforce_project_venv()
    dataset_path = config.DATASET_DIR / "dataset.csv"
    if not dataset_path.exists():
        build_dataset()

    logger = SecurityLogger()
    pipeline = AICSafePipeline(llm_client=MockLLM(), logger=logger)
    rows: list[dict] = []
    with dataset_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for index, sample in enumerate(reader):
            if limit is not None and index >= limit:
                break
            protected = pipeline.run_protected(sample["prompt"], attack_class=sample["attack_class"])
            unprotected = run_unprotected(
                sample["prompt"],
                llm_client=pipeline.llm_client,
                logger=logger,
                attack_class=sample["attack_class"],
            )
            mapped_class = config.ATTACK_CLASS_LABELS.get(sample["attack_class"], sample["attack_class"])
            rows.append(
                {
                    "prompt": sample["prompt"],
                    "attack_class": sample["attack_class"],
                    "attack_class_label": mapped_class,
                    "label": sample["label"],
                    "runtime_tested": sample["runtime_tested"],
                    "tool_intent": protected.intent.tool_intent,
                    "protected_decision": protected.event["decision"],
                    "protected_risk_level": protected.event["risk_level"],
                    "protected_sensitive_output": protected.verification.sensitive_output,
                    "protected_harmful_action": bool(protected.tool_result and protected.tool_result.harmful_action_executed),
                    "protected_latency_ms": protected.latency_ms,
                    "unprotected_decision": unprotected.event["decision"],
                    "unprotected_sensitive_output": unprotected.verification.sensitive_output
                    or bool(unprotected.tool_result and unprotected.tool_result.sensitive_output),
                    "unprotected_harmful_action": bool(unprotected.tool_result and unprotected.tool_result.harmful_action_executed),
                    "unprotected_latency_ms": unprotected.latency_ms,
                    "rag_runtime_note": "classifier-only; Phase 2 runtime path"
                    if sample["attack_class"] == "indirect_rag_injection"
                    else "",
                }
            )

    output = config.EVALUATION_RESULTS_DIR / "benchmark_results.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    if rows:
        with output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    metrics = calculate_metrics(rows)
    write_metrics(metrics)
    log_run(
        "evaluation.benchmark",
        "success",
        {
            "limit": limit,
            "evaluated_rows": len(rows),
            "results_path": str(output),
            "metrics_path": str(config.EVALUATION_RESULTS_DIR / "metrics.json"),
            "metrics": metrics,
        },
    )
    return rows, metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    rows, metrics = run(args.limit)
    print(f"Evaluated {len(rows)} samples")
    for key, value in metrics.items():
        if key != "notes":
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
