"""
DAY-4 DESIGN CHALLENGE - Q7
Diagnose, Redesign and Validate

Selected limitation from Q4:
Repeated string concatenation using += while building a large monthly
statement can require repeated copying of accumulated text.

Original: repeatedly append each line to one string using +=.
Redesign: collect the lines and combine them once using str.join().

Objective:
For identical inputs (1,000, 10,000, and 200,000 lines), produce exactly
the same statement while reducing average construction time.

Prediction:
join() is expected to be faster for large inputs because it joins the
parts in one operation, avoiding repeated creation/copying of intermediate
strings. Actual timings vary by Python version and system.

Pseudocode:
1. Create the same list of statement lines.
2. Time the original += implementation three times.
3. Time the redesigned join() implementation three times.
4. Check both results are identical.
5. Report average times and speedup.
6. Explain the trade-off (join needs a list of parts in memory).
"""

import time
import gc

REPEATS = 3
SIZES = (1_000, 10_000, 200_000)


def build_original(parts):
    """Original approach: repeated += concatenation."""
    statement = ""
    for part in parts:
        statement += part + "\n"
    return statement


def build_redesigned(parts):
    """Redesigned approach: join all lines in one operation."""
    return "\n".join(parts) + "\n"


def benchmark(function, parts, repeats=REPEATS):
    """Return the average elapsed time and the last result."""
    elapsed_times = []
    result = None

    for _ in range(repeats):
        gc.collect()
        start = time.perf_counter()
        result = function(parts)
        elapsed = time.perf_counter() - start
        elapsed_times.append(elapsed)

    average = sum(elapsed_times) / len(elapsed_times)
    return average, result, elapsed_times


def main():
    print("=" * 72)
    print("Q7 - DIAGNOSE, REDESIGN AND VALIDATE: STRING BUILDING")
    print("=" * 72)
    print("Objective: identical output, lower average construction time.")
    print(f"Each method is measured {REPEATS} times per input size.")
    print()

    print(f"{'Lines':>10} {'Original += (avg)':>20} "
          f"{'Redesigned join (avg)':>23} {'Speedup':>12} {'Same text':>12}")
    print("-" * 82)

    results = []

    for n in SIZES:
        items = [f"Item{i}:Rs{i % 50}" for i in range(n)]

        original_avg, original_text, original_runs = benchmark(
            build_original, items
        )
        redesigned_avg, redesigned_text, redesigned_runs = benchmark(
            build_redesigned, items
        )

        same_text = original_text == redesigned_text
        speedup = (
            original_avg / redesigned_avg
            if redesigned_avg > 0
            else float("inf")
        )

        results.append((n, original_avg, redesigned_avg, speedup, same_text))

        print(f"{n:>10} {original_avg:>19.6f}s "
              f"{redesigned_avg:>22.6f}s {speedup:>11.2f}x "
              f"{str(same_text):>12}")

        if not same_text:
            raise AssertionError("The original and redesigned outputs differ!")

    print()
    print("VALIDATION")
    print("-" * 72)
    print("All test sizes produced identical statement text.")
    print("The redesigned implementation uses join() to combine the lines.")
    print()

    print("DIAGNOSIS")
    print("-" * 72)
    print("The original spends time repeatedly extending an immutable string.")
    print("As the statement grows, concatenation can repeatedly copy existing")
    print("characters. The amount of work may approach quadratic growth in")
    print("unfavourable implementations/conditions.")
    print()

    print("REDESIGN AND TRADE-OFF")
    print("-" * 72)
    print("join() combines the string parts in one operation and is generally")
    print("linear in the total number of characters (O(n) for n total chars).")
    print("It requires storing the parts list and the final string in memory.")
    print("Repeated += may be convenient for small strings, and CPython can")
    print("sometimes optimize it, so timings should be measured on the target")
    print("system rather than assumed.")
    print()

    print("FINAL EVALUATION")
    print("-" * 72)
    for n, original_avg, redesigned_avg, speedup, same_text in results:
        if redesigned_avg < original_avg:
            outcome = f"join() faster by about {speedup:.2f}x"
        elif redesigned_avg > original_avg:
            outcome = f"join() slower in this test ({speedup:.2f}x)"
        else:
            outcome = "equal average time"
        print(f"{n:>7} lines: {outcome}; identical output = {same_text}")

    print()
    print("Conclusion: choose join() for building large statements from many")
    print("pieces, after validating output and measuring on the target system.")


if __name__ == "__main__":
    main()
