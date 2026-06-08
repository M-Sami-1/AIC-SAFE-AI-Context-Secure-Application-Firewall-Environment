from __future__ import annotations

import argparse
import csv

import config
from aic_safe.middleware import AICSafePipeline, run_unprotected
from aic_safe.middleware.logger import SecurityLogger
from aic_safe.runtime import enforce_project_venv, log_run
from dataset.build_dataset import build_dataset
from evaluation.metrics import calculate_metrics, write_metrics


def run(limit: int | None = None, runtime_mode: str | None = None) -> tuple[list[dict], dict]:
    enforce_project_venv()
    dataset_path = config.DATASET_DIR / "dataset.csv"
    if not dataset_path.exists():
        build_dataset()

    logger = SecurityLogger()
    pipeline = AICSafePipeline(logger=logger) if runtime_mode is None else _pipeline_for_mode(runtime_mode, logger)
    rows: list[dict] = []
    with dataset_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for index, sample in enumerate(reader):
            if limit is not None and index >= limit:
                break
            raw = run_unprotected(
                sample["prompt"],
                llm_client=pipeline.llm_client,
                logger=logger,
                attack_class=sample["attack_class"],
            )
            rule_only = pipeline.run_rule_only(sample["prompt"], attack_class=sample["attack_class"])
            full = pipeline.run_full_middleware(sample["prompt"], attack_class=sample["attack_class"])
            mapped_class = config.ATTACK_CLASS_LABELS.get(sample["attack_class"], sample["attack_class"])
            row = {
                "prompt": sample["prompt"],
                "attack_class": sample["attack_class"],
                "attack_class_label": mapped_class,
                "label": sample["label"],
                "runtime_tested": sample["runtime_tested"],
                "llm_model": config.MODEL_SELECTION["ollama_model"],
                "rag_runtime_note": "classifier-only; no RAG runtime path in this prototype"
                if sample["attack_class"] == "indirect_rag_injection"
                else "",
            }
            row.update(_result_columns("raw_llm", raw))
            row.update(_result_columns("rule_only", rule_only))
            row.update(_result_columns("full_middleware", full))
            rows.append(row)

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
    parser.add_argument("--runtime-mode", choices=["mock", "ollama"], default=None)
    args = parser.parse_args()
    rows, metrics = run(args.limit, args.runtime_mode)
    print(f"Evaluated {len(rows)} samples")
    for mode, values in metrics["baselines"].items():
        print(f"{mode}_attack_success_rate: {values['attack_success_rate']}")
        print(f"{mode}_false_positive_rate: {values['false_positive_rate']}")
        print(f"{mode}_true_positive_detection_rate: {values['true_positive_detection_rate']}")
        print(f"{mode}_tool_misuse_success_rate: {values['tool_misuse_success_rate']}")


def _result_columns(prefix: str, result) -> dict:
    return {
        f"{prefix}_decision": result.event["decision"],
        f"{prefix}_attack_class": result.prompt_scan.attack_class,
        f"{prefix}_classifier_label": result.prompt_scan.label,
        f"{prefix}_classifier_confidence": result.prompt_scan.confidence,
        f"{prefix}_risk_score": result.prompt_scan.risk_score,
        f"{prefix}_risk_level": result.event["risk_level"],
        f"{prefix}_tool_intent": result.intent.tool_intent,
        f"{prefix}_sensitive_output": result.verification.sensitive_output
        or bool(result.tool_result and result.tool_result.sensitive_output),
        f"{prefix}_harmful_action": bool(result.tool_result and result.tool_result.harmful_action_executed),
        f"{prefix}_attack_success": result.event["attack_success"],
        f"{prefix}_latency_ms": result.latency_ms,
    }


def _pipeline_for_mode(runtime_mode: str, logger: SecurityLogger) -> AICSafePipeline:
    from aic_safe.llm import build_llm_client

    client, _ = build_llm_client(runtime_mode, start_ollama=runtime_mode == "ollama")
    return AICSafePipeline(llm_client=client, logger=logger)


if __name__ == "__main__":
    main()
