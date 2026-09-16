"""Prints the acceptance table for every seeded user. `python -m backend.verify`"""
import sys

from backend.data.repository import get_repository
from backend.pipeline.engine import run_pipeline

HEADER = (
    "USER            ROLE     ENTRY POINT     BFS  +Z2   C1   C2   C3   C4   C5  FINAL   ms"
)


def main() -> int:
    source = get_repository()
    print("backend: {} | nodes: {} | LLM calls: 0\n".format(
        source.backend_name, source.count_nodes("supra")))
    print(HEADER)
    print("-" * len(HEADER))
    for user in source.list_users():
        r = run_pipeline(source, user.id)
        f = r["funnel"]
        print(
            "{:<15} {:<8} {:<15} {:>3} {:>4} {:>4} {:>4} {:>4} {:>4} {:>4} {:>6} {:>5.1f}".format(
                r["user_name"][:15], r["role"], r["entry_point"],
                f["after_bfs"], f["after_zone2"], f["after_check1"], f["after_check2"],
                f["after_check3"], f["after_check4"], f["after_check5"],
                f["candidate_set"], r["pipeline_timing"]["total_ms"],
            )
        )
    print()
    priya = {c["id"] for c in run_pipeline(source, "U-PRIYA")["candidate_set"]}
    checks = [
        ("no other-department nodes", priya.isdisjoint(
            {"N-M01", "N-M02", "N-C01", "N-C04", "N-P01", "N-P03"})),
        ("no MNPI nodes", priya.isdisjoint({"N-O11", "N-O12", "N-A01", "N-A02"})),
        ("no superseded nodes", "N-M08" not in priya),
        ("no derivable nodes", priya.isdisjoint({"N-D01", "N-D02", "N-D03", "N-D04", "N-D05"})),
        ("global drug safety present", "N-G01" in priya),
        ("patient constraint present", "N-O14" in priya),
    ]
    for label, ok in checks:
        print("  [{}] Priya: {}".format("PASS" if ok else "FAIL", label))
    return 0 if all(ok for _, ok in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
