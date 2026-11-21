"""
ASSIGNMENT 3 - LAST TASK ONLY (Q7)
Design a Contact-Merging Program from First Principles

Stage 1 - Interpret the problem
Input: contacts imported from multiple phones/SIM, with names, phone numbers,
       and email addresses that may be missing or written in different formats.
Output: merged contacts, each grouping holding a name, a set of phone numbers,
        and a set of email addresses.
Identity rule: contacts are grouped by a normalized phone number. A contact
               without a usable phone number is retained separately.
Measurable requirements:
1. Normalize number formatting (spaces, hyphens, parentheses, plus sign).
2. Merge records with matching normalized numbers.
3. Preserve all distinct numbers and emails.
4. Handle missing fields without crashing.
5. Verify small sample manually and benchmark 1,000 and 100,000 records.

Stage 2 - Design
Normalization:
- Phone: keep digits only; for numbers beginning with country code 91 and
  containing 12 digits, remove 91 to use the 10-digit Indian number as key.
- Name: lowercase, remove punctuation, collapse whitespace for comparison.
- Emails: lowercase and trim surrounding spaces.

Pseudocode:
For each contact:
  normalize phone and email
  if normalized phone exists:
      use it as dictionary key
  else:
      assign a unique missing-number key
  create a merged record if key not present
  add name, original/normalized phone and email to sets
  choose a readable display name if available

Stage 3 - Implement and measure
The benchmark compares:
- Dictionary grouping by normalized phone number: average O(n)
- Pairwise comparison: O(n^2) comparisons in the worst case

Stage 4 - Defend
A dictionary avoids comparing every contact with every other contact.
Different people sharing a name are not merged unless their normalized phone
numbers match. Limitation: phone-number identity can be imperfect (shared,
recycled, or incorrectly entered numbers); contacts without phone numbers
cannot be reliably deduplicated.

This is standalone Q7 code, suitable to upload as the only Python source file.
"""

import time
import random
import string
import gc


def normalize_phone(phone):
    """Return a canonical phone key, or None when no digits are present."""
    if not phone:
        return None
    digits = "".join(ch for ch in str(phone) if ch.isdigit())
    if not digits:
        return None
    # Treat Indian country code +91 as equivalent to a local 10-digit number.
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    return digits


def normalize_name(name):
    """Normalize a name for display/comparison."""
    if not name:
        return ""
    cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in str(name))
    return " ".join(cleaned.split())


def normalize_email(email):
    return str(email).strip().lower() if email else ""


def merge_contacts(contacts):
    """Merge contacts using a dictionary keyed by normalized phone."""
    merged = {}
    missing_counter = 0

    for contact in contacts:
        name = str(contact.get("name") or "").strip()
        phone = str(contact.get("phone") or "").strip()
        email = normalize_email(contact.get("email"))

        phone_key = normalize_phone(phone)
        if phone_key is None:
            # Keep phone-less records separate because identity is uncertain.
            missing_counter += 1
            key = f"NO_PHONE_{missing_counter}"
        else:
            key = phone_key

        if key not in merged:
            merged[key] = {
                "name": name,
                "names": set(),
                "phones": set(),
                "emails": set(),
            }

        record = merged[key]
        if name:
            record["names"].add(name)
            # Prefer the first non-empty name, otherwise use the newly found one.
            if not record["name"]:
                record["name"] = name
        if phone:
            record["phones"].add(phone)
        if phone_key:
            record["phones"].add(phone_key)
        if email:
            record["emails"].add(email)

    # Return a readable list; sets are sorted for stable output.
    output = []
    for key, record in merged.items():
        output.append({
            "key": key,
            "name": record["name"] or "Unknown",
            "all_names": sorted(record["names"]),
            "phones": sorted(record["phones"]),
            "emails": sorted(record["emails"]),
        })
    return output


def merge_contacts_pairwise(contacts):
    """
    Baseline approach: compare each incoming record against all existing
    merged records. This is a simple pairwise-style baseline and can be O(n^2).
    """
    merged = []

    for contact in contacts:
        phone_key = normalize_phone(contact.get("phone"))
        name = str(contact.get("name") or "").strip()
        phone = str(contact.get("phone") or "").strip()
        email = normalize_email(contact.get("email"))

        match = None
        if phone_key:
            for record in merged:
                if phone_key in record["phone_keys"]:
                    match = record
                    break

        if match is None:
            merged.append({
                "name": name or "Unknown",
                "names": set([name]) if name else set(),
                "phones": set([phone]) if phone else set(),
                "phone_keys": set([phone_key]) if phone_key else set(),
                "emails": set([email]) if email else set(),
            })
        else:
            if name:
                match["names"].add(name)
                if not match["name"] or match["name"] == "Unknown":
                    match["name"] = name
            if phone:
                match["phones"].add(phone)
            if phone_key:
                match["phone_keys"].add(phone_key)
            if email:
                match["emails"].add(email)

    return merged


def print_contacts(contacts):
    print("Merged contacts:")
    for i, contact in enumerate(contacts, 1):
        print(f"{i}. {contact['name']}")
        print("   Names :", contact["all_names"] or ["(none)"])
        print("   Phones:", contact["phones"] or ["(none)"])
        print("   Emails:", contact["emails"] or ["(none)"])


def make_benchmark_contacts(n, duplicate_rate=0.25, seed=42):
    """Generate deterministic-ish synthetic contacts for timing."""
    rng = random.Random(seed + n)
    contacts = []
    unique_count = max(1, int(n * (1 - duplicate_rate)))

    for i in range(n):
        person_id = i if i < unique_count else rng.randrange(unique_count)
        phone = f"98400{person_id % 100000:05d}"
        # Vary formatting for some records.
        if i % 3 == 0:
            phone = "+91 " + phone
        elif i % 3 == 1:
            phone = phone[:5] + "-" + phone[5:]

        contacts.append({
            "name": f"Contact {person_id}",
            "phone": phone,
            "email": f"person{person_id}@example.com" if i % 4 != 0 else "",
        })
    return contacts


def benchmark(function, data, repeats=3):
    times = []
    result = None
    for _ in range(repeats):
        gc.collect()
        start = time.perf_counter()
        result = function(data)
        times.append(time.perf_counter() - start)
    return sum(times) / len(times), result


def main():
    print("=" * 70)
    print("Q7 - CONTACT MERGING: DESIGN, IMPLEMENTATION AND VALIDATION")
    print("=" * 70)

    sample = [
        {"name": "Dr. Ravi", "phone": "+91 98400 12345", "email": "RAVI@EXAMPLE.COM"},
        {"name": "ravi kumar", "phone": "98400-12345", "email": "ravi.alt@example.com"},
        {"name": "RAVI", "phone": "9840012345", "email": " ravi@example.com "},
        {"name": "Anita", "phone": "90000 11111", "email": "anita@example.com"},
        {"name": "Anita S", "phone": "", "email": "anita.s@example.com"},
        {"name": "Unknown contact", "phone": None, "email": ""},
        {"name": "Ravi Kumar", "phone": "+91 (98400) 12345", "email": ""},
    ]

    print("\nSMALL SAMPLE - HAND-VERIFIED")
    print("-" * 70)
    print("Input records:", len(sample))
    merged_sample = merge_contacts(sample)
    print("Merged groups:", len(merged_sample))
    print_contacts(merged_sample)

    # Validate the sample: Ravi's different formats merge into one record.
    ravi = next(c for c in merged_sample if c["key"] == "9840012345")
    assert len(ravi["emails"]) == 2
    assert len(ravi["phones"]) >= 2
    assert len(merged_sample) == 4  # Ravi, Anita, and two separate phone-less records

    print("\nVALIDATION")
    print("-" * 70)
    print("Different formats of Ravi's number merge into one contact.")
    print("Distinct emails are retained; missing-phone contact is kept separately.")
    print("Different people with different phone keys remain separate.")
    print("Small sample assertions: PASSED")

    print("\nPERFORMANCE COMPARISON (average of 3 runs)")
    print("-" * 70)
    print(f"{'Records':>12} {'Dictionary merge':>20} {'Pairwise baseline':>20} {'Speedup':>12}")
    print("-" * 70)

    # The pairwise baseline is deliberately limited to a manageable size,
    # since its worst-case growth is quadratic. Benchmark 100,000 only for
    # the dictionary method.
    for n in (1_000, 100_000):
        data = make_benchmark_contacts(n)

        dict_avg, dict_result = benchmark(merge_contacts, data, repeats=3)
        if n == 1_000:
            pair_avg, pair_result = benchmark(merge_contacts_pairwise, data, repeats=3)
            speedup = pair_avg / dict_avg if dict_avg else float("inf")
            print(f"{n:>12} {dict_avg:>19.6f}s {pair_avg:>19.6f}s {speedup:>11.2f}x")
            # Validate that both methods produce the same number of merged groups.
            assert len(dict_result) == len(pair_result)
        else:
            print(f"{n:>12} {dict_avg:>19.6f}s {'Skipped (O(n^2))':>20} {'—':>12}")

    print("\nCOMPLEXITY")
    print("-" * 70)
    print("Dictionary grouping: O(n) average time, O(n) space for merged records.")
    print("Pairwise comparisons: O(n^2) worst-case time, O(n) output space.")
    print("Dictionary lookup is average O(1), so each contact can be grouped")
    print("without scanning all previously merged contacts.")
    print("\nLIMITATION")
    print("-" * 70)
    print("Phone numbers may be shared, recycled, or entered incorrectly.")
    print("Phone-less records are retained separately and cannot be confidently")
    print("merged. A production system could add a review step or other identifiers.")
    print("\nFINAL DECISION")
    print("-" * 70)
    print("Use dictionary-based merging for large contact imports because it is")
    print("faster on average and scales better than comparing every pair.")
    print("The pairwise baseline is acceptable only for tiny lists or teaching.")


if __name__ == "__main__":
    main()
