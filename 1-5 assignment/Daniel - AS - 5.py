"""
TASK B4 - FINAL ENGINEERING DECISION
Standalone implementation:
1. Lexicon-based sentiment scoring with simple negation handling.
2. Extractive complaint summarisation using frequent important words.
3. Evaluation against 50 manually assigned reference labels.
4. Comparison with a first-two-sentences summary baseline.
5. SQLite composite-index timing experiment on (station, day).
6. Evidence-based production recommendation.

Run:
    py task_b4_final.py

Only Python standard-library modules are required.
"""

import re
import sqlite3
import statistics
import time
from collections import Counter


POSITIVE = {
    "good", "clean", "fast", "helpful", "improved", "better",
    "excellent", "resolved", "safe", "thankful", "working",
    "reduced", "quick", "friendly", "clear"
}

NEGATIVE = {
    "bad", "dirty", "slow", "rude", "smoke", "broken",
    "worse", "polluted", "unhealthy", "delay", "delayed",
    "noise", "overflow", "unsafe", "failed", "problem",
    "complaint", "dust", "blocked", "unresponsive"
}

NEGATORS = {"not", "never", "no", "isn't", "wasn't", "weren't", "don't", "didn't"}
STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were",
    "to", "of", "in", "on", "at", "for", "from", "with", "this", "that",
    "it", "my", "our", "their", "i", "we", "you", "they", "he", "she",
    "has", "have", "had", "be", "been", "being", "as", "by", "after",
    "before", "today", "yesterday", "very", "there", "here", "near"
}


def tokenize(text):
    """Return lowercase words while retaining apostrophes inside contractions."""
    return re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower())


def score(text):
    """+1 for a positive word, -1 for a negative word; a preceding negator flips it."""
    words = tokenize(text)
    total = 0

    for index, word in enumerate(words):
        value = 1 if word in POSITIVE else -1 if word in NEGATIVE else 0

        if value != 0 and index > 0 and words[index - 1] in NEGATORS:
            value *= -1

        total += value

    return total


def label(text):
    value = score(text)
    if value > 0:
        return "positive"
    if value < 0:
        return "negative"
    return "neutral"


def extractive_summary(text, sentence_count=2):
    """
    Select sentences containing the most frequent important words.
    The selected sentences are returned in their original order.
    """
    sentences = [
        part.strip()
        for part in re.split(r"(?<=[.!?])\s+", text.strip())
        if part.strip()
    ]

    if len(sentences) <= sentence_count:
        return " ".join(sentences)

    all_words = [
        word for sentence in sentences
        for word in tokenize(sentence)
        if word not in STOP_WORDS and len(word) > 2
    ]
    frequencies = Counter(all_words)

    if not frequencies:
        return " ".join(sentences[:sentence_count])

    sentence_scores = []
    for position, sentence in enumerate(sentences):
        words = [
            word for word in tokenize(sentence)
            if word not in STOP_WORDS and len(word) > 2
        ]
        value = sum(frequencies[word] for word in words)
        sentence_scores.append((value, position, sentence))

    chosen = sorted(
        sentence_scores,
        key=lambda item: (-item[0], item[1])
    )[:sentence_count]

    chosen.sort(key=lambda item: item[1])
    return " ".join(item[2] for item in chosen)


def first_sentence_summary(text, sentence_count=2):
    """Simple baseline: take the first k sentences."""
    sentences = [
        part.strip()
        for part in re.split(r"(?<=[.!?])\s+", text.strip())
        if part.strip()
    ]
    return " ".join(sentences[:sentence_count])


# Complaint text and manually assigned reference sentiment after reading each item.
COMPLAINTS = [
    ("The road is clean and the collection team is helpful.", "positive"),
    ("Smoke is coming from the factory and the air is bad.", "negative"),
    ("The staff were not helpful and my complaint is unresolved.", "negative"),
    ("Not bad, the service improved and the road is clean.", "positive"),
    ("The bus is fast but the waiting area is dirty.", "negative"),
    ("The water overflow problem was resolved quickly.", "positive"),
    ("Dust levels are high and the road is unsafe.", "negative"),
    ("The officers were friendly and gave a clear answer.", "positive"),
    ("The garbage truck is delayed and the smell is unhealthy.", "negative"),
    ("Air quality is good today and smoke has reduced.", "positive"),
    ("The street light is broken and the road is dark.", "negative"),
    ("The team was not rude and they were helpful.", "positive"),
    ("There is no improvement in the polluted street.", "negative"),
    ("The blocked drain was cleaned and the area is safe.", "positive"),
    ("The noise is bad and continues every night.", "negative"),
    ("The response was quick and the issue is resolved.", "positive"),
    ("The air is not clean near the construction site.", "negative"),
    ("The new bus service is fast and working well.", "positive"),
    ("The complaint system is slow and often failed.", "negative"),
    ("The officer was not unhelpful and explained the process.", "positive"),
    ("Factory smoke makes the air unhealthy for children.", "negative"),
    ("The waste was removed and the street looks clean.", "positive"),
    ("The road is broken and traffic is delayed.", "negative"),
    ("The staff gave helpful updates and resolved the issue.", "positive"),
    ("The drainage is dirty and the smell is bad.", "negative"),
    ("The air quality improved after the dust was controlled.", "positive"),
    ("The service is not good and the response is slow.", "negative"),
    ("The park is clean and the lights are working.", "positive"),
    ("The factory smoke is worse today and causes problems.", "negative"),
    ("The team arrived quickly and fixed the broken pipe.", "positive"),
    ("The street is polluted and garbage collection failed.", "negative"),
    ("The new schedule is clear and helpful.", "positive"),
    ("The water supply is delayed and the service is poor.", "negative"),
    ("The officers were helpful but the road remains dirty.", "negative"),
    ("The smoke has reduced and the air feels better.", "positive"),
    ("The complaint received no response and the drain is blocked.", "negative"),
    ("The repair was completed and the road is safe.", "positive"),
    ("The bus was not fast and the service was delayed.", "negative"),
    ("The staff were friendly and the issue was resolved.", "positive"),
    ("The air is bad, but the road cleaning is improved.", "negative"),
    ("The garbage was removed, but smoke remains near the factory.", "negative"),
    ("The water is clean and the supply is working.", "positive"),
    ("The road is unsafe because dust and noise continue.", "negative"),
    ("The response was not slow and the team was helpful.", "positive"),
    ("The street light failed and the area is unsafe.", "negative"),
    ("The air quality is better and pollution has reduced.", "positive"),
    ("The drain is overflowing and the smell is unhealthy.", "negative"),
    ("The staff explained the delay clearly and were helpful.", "positive"),
    ("The factory is releasing smoke and the air is polluted.", "negative"),
    ("The broken street light was repaired quickly.", "positive"),
]


def evaluate_sentiment():
    print("\nB4.1 - SENTIMENT EVALUATION (50 COMPLAINTS)")
    print("-" * 72)

    correct = 0
    for number, (complaint, expected) in enumerate(COMPLAINTS, start=1):
        predicted = label(complaint)
        if predicted == expected:
            correct += 1
        print(
            f"{number:02d}. expected={expected:8} "
            f"predicted={predicted:8} score={score(complaint):3} | {complaint}"
        )

    accuracy = correct / len(COMPLAINTS) * 100
    print(f"\nAgreement with manual reading: {correct}/{len(COMPLAINTS)} "
          f"({accuracy:.1f}%)")

    wrong = [
        (text, expected, label(text))
        for text, expected in COMPLAINTS
        if label(text) != expected
    ]
    if wrong:
        print("\nExamples where the simple lexicon scorer disagrees:")
        for text, expected, predicted in wrong[:3]:
            print(f"- Text: {text}")
            print(f"  Manual: {expected}; scorer: {predicted}")
    else:
        print("\nNo disagreement in this small test set. This does not prove")
        print("the lexicon will work on unseen complaints.")

    return correct, accuracy


def evaluate_summaries():
    print("\nB4.1 - EXTRACTIVE SUMMARY VS FIRST-TWO-SENTENCE BASELINE")
    print("-" * 72)

    sample = (
        "I am reporting repeated smoke near the factory. "
        "The smoke makes the air polluted and unhealthy. "
        "Residents have complained about the smoke for several weeks. "
        "Please inspect the factory and reduce the pollution."
    )

    selected = extractive_summary(sample, 2)
    baseline = first_sentence_summary(sample, 2)

    print("Original complaint:")
    print(sample)
    print("\nFrequency-based summary:")
    print(selected)
    print("\nFirst-two-sentences summary:")
    print(baseline)
    print("\nInterpretation: the frequency-based method selects sentences around")
    print("repeated key terms such as smoke and pollution. The first-sentence")
    print("baseline is faster but may miss the main repeated issue if it appears later.")


def benchmark_index():
    print("\nB4.2 - SQLITE INDEX EXPERIMENT")
    print("-" * 72)

    connection = sqlite3.connect(":memory:")
    connection.execute("""
        CREATE TABLE readings (
            id INTEGER PRIMARY KEY,
            station TEXT NOT NULL,
            day TEXT NOT NULL,
            pm25 REAL NOT NULL
        )
    """)

    # 200,000 deterministic rows provide enough data for a simple timing test.
    rows = []
    station_count = 100
    days = 30
    rows_per_station = 2000

    for station_number in range(station_count):
        station_name = f"Station_{station_number:03d}"
        for reading_number in range(rows_per_station):
            day_number = (reading_number % days) + 1
            day = f"2026-10-{day_number:02d}"
            pm25 = float(20 + ((station_number * 7 + reading_number) % 180))
            rows.append((station_name, day, pm25))

    connection.executemany(
        "INSERT INTO readings (station, day, pm25) VALUES (?, ?, ?)",
        rows
    )
    connection.commit()

    query = """
        SELECT AVG(pm25)
        FROM readings
        WHERE station = ? AND day = ?
    """
    parameters = ("Station_050", "2026-10-15")
    repetitions = 200

    def measure_query():
        start = time.perf_counter()
        result = None
        for _ in range(repetitions):
            result = connection.execute(query, parameters).fetchone()[0]
        elapsed = time.perf_counter() - start
        return elapsed, result

    # Run once before measurement to reduce one-time effects.
    connection.execute(query, parameters).fetchone()
    before_time, before_result = measure_query()

    connection.execute(
        "CREATE INDEX idx_readings_station_day ON readings(station, day)"
    )
    connection.commit()

    connection.execute(query, parameters).fetchone()
    after_time, after_result = measure_query()

    print(f"Rows inserted: {len(rows):,}")
    print(f"Query repetitions: {repetitions}")
    print(f"Average before index: {before_result:.2f}")
    print(f"Average after index:  {after_result:.2f}")
    print(f"Time without index: {before_time:.6f} seconds")
    print(f"Time with index:    {after_time:.6f} seconds")

    if after_time > 0:
        improvement = before_time / after_time
        print(f"Observed speed ratio (before / after): {improvement:.2f}x")

    plan = connection.execute(
        "EXPLAIN QUERY PLAN " + query, parameters
    ).fetchall()
    print("Query plan after index:")
    for item in plan:
        print(item)

    print("\nNote: timings depend on the computer, SQLite version, cache and data size.")
    print("An index speeds up matching station/day lookups but uses extra disk space")
    print("and adds work when rows are inserted or updated.")

    connection.close()


def production_decision():
    print("\nB4.3 - FINAL PRODUCTION DECISION")
    print("-" * 72)
    print("1. Store station details and readings in SQLite for a small deployment.")
    print("   For sustained multi-user, multi-million-row operation, use a managed")
    print("   relational/time-series database with backups and retention policies.")
    print("2. Validate CSV/API input, standardise station IDs and timestamps, reject")
    print("   impossible PM2.5 values, record missing data and keep an audit trail.")
    print("3. Use batch inserts, indexes on (station, day), and SQL aggregation for")
    print("   daily reports. The index experiment above measures the lookup benefit.")
    print("4. At 100 stations reporting every 15 minutes, the system receives about")
    print("   100 x 96 = 9,600 readings per day (about 3.50 million per year).")
    print("5. At 50,000 complaints per month, the lexicon is useful as a fast baseline")
    print("   and for urgent keyword flags, but it is not reliable enough alone.")
    print("   Sarcasm, context, double negatives and mixed opinions can cause errors.")
    print("6. Build a manually labelled local-language and English complaint dataset,")
    print("   evaluate a trained classifier, monitor precision/recall by class, and")
    print("   keep human review for uncertain or high-impact complaints.")
    print("7. A trained model generally needs more memory and inference time than a")
    print("   word list, but can improve context handling when trained on representative")
    print("   local data. A pre-trained language model may be more expensive still.")
    print("   Model choice must be based on measured accuracy, latency and cost.")


def main():
    print("=" * 72)
    print("SIMATS ENGINEERING - PART B, TASK B4")
    print("FINAL ENGINEERING DECISION")
    print("=" * 72)

    evaluate_sentiment()
    evaluate_summaries()
    benchmark_index()
    production_decision()

    print("\nTASK B4 execution completed.")


if __name__ == "__main__":
    main()
