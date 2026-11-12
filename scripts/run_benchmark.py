import json
import os
import sys

# Ensure project root is on Python import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.evaluation_service import RAGEvaluationService


def main():
    print("Running Enterprise RAG Quality & Retrieval Benchmark...\n")
    service = RAGEvaluationService()
    report = service.run_benchmark(compare_baseline=True)

    print(f"{'Query':<45} | {'P@K':<6} | {'MRR':<6} | {'Faith':<6} | {'Latency'}")
    print("-" * 85)
    for item in report.case_results:
        q_short = (item.query[:42] + "...") if len(item.query) > 45 else item.query
        print(
            f"{q_short:<45} | {item.precision_at_k:<6.2f} | "
            f"{item.reciprocal_rank:<6.2f} | {item.faithfulness_score:<6.2f} | "
            f"{item.latency_ms:.1f} ms"
        )

    print("-" * 85)
    print(f"Mean Precision@K : {report.mean_precision_at_k:.4f}")
    print(f"Mean Reciprocal Rank (MRR): {report.mrr:.4f}")
    print(f"Mean Faithfulness: {report.mean_faithfulness:.4f}")
    print(f"Average Latency  : {report.avg_latency_ms:.2f} ms")

    if report.baseline_comparison:
        comp = report.baseline_comparison
        print("\nBaseline (Hybrid Only) vs. Advanced Pipeline (Hybrid + Rerank + Compress):")
        print(
            f"  Precision@K : {comp.baseline_precision_at_k:.4f} -> "
            f"{comp.advanced_precision_at_k:.4f} (Delta: {comp.precision_delta:+.4f})"
        )
        print(
            f"  MRR         : {comp.baseline_mrr:.4f} -> "
            f"{comp.advanced_mrr:.4f} (Delta: {comp.mrr_delta:+.4f})"
        )

    output_path = os.path.join(os.path.dirname(__file__), "benchmark_report.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, indent=2)
    print(f"\nSaved full JSON benchmark report to: {output_path}")


if __name__ == "__main__":
    main()