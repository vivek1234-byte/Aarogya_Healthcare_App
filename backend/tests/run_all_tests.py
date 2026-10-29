import sys
import os
import subprocess
import time

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)


def main():
    print("=" * 72)
    print("🏥 AROGYASAATHI BACKEND COMPREHENSIVE TEST & BENCHMARK SUITE")
    print("=" * 72)
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    print(f"Workspace: {backend_dir}\n")

    test_scripts = [
        ("Phase 1: Foundation & DPDP Security", "verify_phase1.py", "O1, O6"),
        ("Phase 2: Voice Triage & LangGraph Orchestration", "verify_phase2.py", "O1, O3, O5, O6"),
        ("Phase 3: Chronic Care Engine & Early Deterioration", "verify_phase3.py", "O2"),
        ("Phase 4: Syndromic Surveillance & Outbreak Warning", "verify_phase4.py", "O4"),
    ]

    all_passed = True
    start_total = time.time()
    results = []

    for name, script, objectives in test_scripts:
        script_path = os.path.join(current_dir, script)
        print(f"▶️  Executing [{name}] (Objectives: {objectives})...")
        t0 = time.time()
        res = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
        t_elapsed = round(time.time() - t0, 3)

        if res.returncode == 0:
            print(f"   ✅ PASSED ({t_elapsed}s)\n")
            results.append((name, objectives, "PASSED", t_elapsed))
        else:
            print(f"   ❌ FAILED ({t_elapsed}s)")
            print(res.stderr or res.stdout)
            all_passed = False
            results.append((name, objectives, "FAILED", t_elapsed))

    total_time = round(time.time() - start_total, 3)

    print("=" * 72)
    print("📋 SUMMARY CLINICAL BENCHMARK SCORECARD")
    print("=" * 72)
    print(f"{'Test Module':<50} | {'Target':<10} | {'Status':<8} | {'Time'}")
    print("-" * 72)
    for name, obj, status, elapsed in results:
        print(f"{name:<50} | {obj:<10} | {status:<8} | {elapsed}s")
    print("-" * 72)
    print(f"Total Execution Time: {total_time}s")
    print(f"Overall Result: {'🎯 ALL SUITES PASSED (100%)' if all_passed else '⚠️ SOME TESTS FAILED'}")
    print("=" * 72)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
