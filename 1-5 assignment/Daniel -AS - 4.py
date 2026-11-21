"""
ASSIGNMENT 4 - LAST TASK ONLY (TASK 6)
DESIGN CHALLENGE: COLLEGE FEST REGISTRATION DESK

Stage 1 - Requirements
Inputs: five department CSV-like text files. Each record contains:
register number, name, department, email, event1;event2;...
Outputs:
- master_list.csv: one valid record per register number
- event_<name>.txt: participant list for each event
- summary_report.txt: registration and event counts
- error_log.txt: missing files and rejected records with source and line number

Validation rules:
- Exactly 5 comma-separated fields
- Register number, name, department, email, and events are required
- Email is checked using string methods (must contain one @, nonempty
  local/domain parts, and a dot in the domain)
- Event names are separated by semicolons, trimmed and normalized
- Duplicate register numbers: first valid registration retained; later
  registrations logged as duplicates
- A missing department file is logged; processing continues

Stage 2 - Processing flow (text flowchart)
Input department files
       |
       v
Open each file safely -> Missing file? -> Log missing, continue
       |
       v
Read line by line -> Parse and validate?
       |                         |
       | valid                   | invalid
       v                         v
Check register number in seen set   Log source + line + reason
       |
       v
Duplicate? -> log duplicate / skip
       |
       v
Add to seen set + master records + event groups
       |
       v
Write master, event lists, summary, and error log

Stage 3 - Decisions
- Set of register numbers: average O(1) membership; avoids list scan.
- Email validation uses string methods rather than regular expressions.
- ValueError is used for malformed records; file exceptions are handled
  per-file so a missing file does not stop processing other departments.

Stage 4 - Package design (conceptual)
fest_registration/
    __init__.py
    reader.py       -> read_department_file(path)
    validator.py    -> parse_and_validate(line)
    merger.py       -> merge_unique(records, seen)
    report.py       -> write_master(), write_events(), write_summary()
    errors.py       -> append_error()
main.py            -> process all department files and orchestrate reports

Pseudocode:
seen = set()
master = []
event_groups = dictionary of event -> list of students
for department file:
    try open:
        for each line:
            parse and validate
            if invalid: log it and continue
            if register number in seen: log duplicate and continue
            add register number to seen
            append record to master and event groups
    except file errors: log and continue
write all reports

Stage 5 - Demonstration
This standalone script creates a temporary demo folder with five department
files (four present and one intentionally missing), including valid records,
a duplicate, an invalid email, and a damaged line. It processes the folder,
prints results, and removes the temporary test folder afterwards.

Alternative complexity:
List-based duplicate checking: O(n^2) worst case because each new record
may scan all earlier records.
Set-based checking: O(n) average total because membership and insertion
are average O(1) per record.
Both retain O(n) records/seen information; the set-based design uses extra
hash-table space for seen register numbers but scales better.
"""

import os
import tempfile
import time
import gc
import random


DEPARTMENTS = ("CSE", "ECE", "EEE", "MECH", "CIVIL")


def valid_email(email):
    """Basic email validation using string methods only (not full RFC rules)."""
    email = email.strip()
    if email.count("@") != 1:
        return False
    local, domain = email.split("@")
    if not local or not domain:
        return False
    if "." not in domain:
        return False
    if domain.startswith(".") or domain.endswith("."):
        return False
    if " " in email:
        return False
    return True


def parse_record(line):
    """Parse one input row and return a normalized record dictionary."""
    parts = line.strip().split(",")
    if len(parts) != 5:
        raise ValueError(f"expected 5 fields, found {len(parts)}")

    reg_no, name, department, email, event_text = [p.strip() for p in parts]
    if not reg_no:
        raise ValueError("missing register number")
    if not name:
        raise ValueError("missing name")
    if not department:
        raise ValueError("missing department")
    if not email:
        raise ValueError("missing email")
    if not valid_email(email):
        raise ValueError(f"invalid email {email!r}")

    events = [event.strip().title() for event in event_text.split(";") if event.strip()]
    if not events:
        raise ValueError("no events selected")

    return {
        "register_number": reg_no,
        "name": name,
        "department": department.upper(),
        "email": email.lower(),
        "events": sorted(set(events)),
    }


def process_files(input_dir, department_files, output_dir):
    """Process files independently; errors are recorded and processing continues."""
    os.makedirs(output_dir, exist_ok=True)

    seen = set()
    master = []
    event_groups = {}
    error_entries = []
    files_found = 0

    for filename in department_files:
        path = os.path.join(input_dir, filename)
        try:
            with open(path, "r", encoding="utf-8") as source:
                files_found += 1
                for line_number, line in enumerate(source, start=1):
                    if not line.strip():
                        continue
                    try:
                        record = parse_record(line)
                    except ValueError as exc:
                        error_entries.append(
                            f"{filename}:{line_number}: REJECTED - {exc} | {line.rstrip()}"
                        )
                        continue

                    reg_no = record["register_number"]
                    if reg_no in seen:
                        error_entries.append(
                            f"{filename}:{line_number}: DUPLICATE - {reg_no} | {line.rstrip()}"
                        )
                        continue

                    seen.add(reg_no)
                    master.append(record)
                    for event in record["events"]:
                        event_groups.setdefault(event, []).append(record)

        except FileNotFoundError:
            error_entries.append(f"{filename}: MISSING FILE")
            continue
        except PermissionError as exc:
            error_entries.append(f"{filename}: PERMISSION DENIED - {exc}")
            continue
        except UnicodeDecodeError as exc:
            error_entries.append(f"{filename}: ENCODING ERROR - {exc}")
            continue
        except OSError as exc:
            error_entries.append(f"{filename}: FILE ERROR - {exc}")
            continue

    # Master report
    master_path = os.path.join(output_dir, "master_list.csv")
    with open(master_path, "w", encoding="utf-8") as out:
        out.write("register_number,name,department,email,events\n")
        for record in master:
            event_text = ";".join(record["events"])
            out.write(
                f"{record['register_number']},{record['name']},"
                f"{record['department']},{record['email']},{event_text}\n"
            )

    # Event reports
    for event, participants in sorted(event_groups.items()):
        safe_event = "".join(ch.lower() if ch.isalnum() else "_" for ch in event)
        event_path = os.path.join(output_dir, f"event_{safe_event}.txt")
        with open(event_path, "w", encoding="utf-8") as out:
            out.write(f"Participants for {event}\n")
            for record in participants:
                out.write(
                    f"{record['register_number']} | {record['name']} | "
                    f"{record['department']} | {record['email']}\n"
                )

    # Summary report
    summary_path = os.path.join(output_dir, "summary_report.txt")
    with open(summary_path, "w", encoding="utf-8") as out:
        out.write("COLLEGE FEST REGISTRATION SUMMARY\n")
        out.write(f"Files successfully opened: {files_found}\n")
        out.write(f"Unique valid registrations: {len(master)}\n")
        out.write(f"Events: {len(event_groups)}\n")
        for event, participants in sorted(event_groups.items()):
            out.write(f"{event}: {len(participants)} participant(s)\n")

    # Error log (also created when there are no errors)
    error_path = os.path.join(output_dir, "error_log.txt")
    with open(error_path, "w", encoding="utf-8") as out:
        if error_entries:
            out.write("\n".join(error_entries) + "\n")
        else:
            out.write("No errors.\n")

    return {
        "master": master,
        "event_groups": event_groups,
        "errors": error_entries,
        "files_found": files_found,
        "output_dir": output_dir,
    }


def list_based_unique(registrations):
    """Slow baseline: compare each register number against the earlier list."""
    accepted = []
    seen_list = []
    for reg_no in registrations:
        if reg_no not in seen_list:
            seen_list.append(reg_no)
            accepted.append(reg_no)
    return accepted


def set_based_unique(registrations):
    """Average O(n) baseline using a set."""
    accepted = []
    seen = set()
    for reg_no in registrations:
        if reg_no not in seen:
            seen.add(reg_no)
            accepted.append(reg_no)
    return accepted


def benchmark_duplicate_detection():
    print("\nDUPLICATE DETECTION BENCHMARK")
    print("-" * 72)
    print(f"{'Records':>12} {'List search':>18} {'Set method':>18} {'Speedup':>12}")

    for n in (1_000, 100_000):
        rng = random.Random(17 + n)
        registrations = [f"REG{rng.randrange(max(1, n // 2)):07d}" for _ in range(n)]

        # Pairwise/list-search baseline is intentionally not run for 100k:
        # it can take a very long time due to quadratic growth.
        if n == 1_000:
            gc.collect()
            start = time.perf_counter()
            list_result = list_based_unique(registrations)
            list_time = time.perf_counter() - start

        gc.collect()
        start = time.perf_counter()
        set_result = set_based_unique(registrations)
        set_time = time.perf_counter() - start

        if n == 1_000:
            assert list_result == set_result
            speedup = list_time / set_time if set_time else float("inf")
            print(f"{n:>12} {list_time:>17.6f}s {set_time:>17.6f}s {speedup:>11.2f}x")
        else:
            print(f"{n:>12} {'Skipped (O(n²))':>18} {set_time:>17.6f}s {'—':>12}")


def create_demo_files(folder):
    """Create test department files; CIVIL is intentionally missing."""
    records = {
        "CSE.txt": [
            "192311001,Asha,CSE,asha@example.com,Music;Dance",
            "192311002,Bala,CSE,bala@example.com,Drama",
            "192311003,Charan,CSE,charan@example.com,Quiz",
            "192311004,Divya,CSE,not-an-email,Music",
            "192311005,Edwin,CSE,edwin@example.com,Photography",
            "BROKEN LINE WITH TOO FEW FIELDS",
        ],
        "ECE.txt": [
            "192311001,Asha,CSE,asha@example.com,Dance;Music",  # duplicate reg no
            "192322001,Fathima,ECE,fathima@example.com,Drama;Quiz",
            "192322002,Gokul,ECE,gokul@example.com,Music",
        ],
        "EEE.txt": [
            "192333001,Hari,EEE,hari@example.com,Quiz;Photography",
        ],
        "MECH.txt": [
            "192344001,Isha,MECH,isha@example.com,Dance",
        ],
        # CIVIL.txt deliberately not created to test missing-file handling.
    }

    for filename, lines in records.items():
        with open(os.path.join(folder, filename), "w", encoding="utf-8") as out:
            out.write("\n".join(lines) + "\n")


def main():
    print("=" * 72)
    print("TASK 6 - COLLEGE FEST REGISTRATION DESK")
    print("=" * 72)

    with tempfile.TemporaryDirectory(prefix="fest_demo_") as root:
        input_dir = os.path.join(root, "department_files")
        output_dir = os.path.join(root, "reports")
        os.makedirs(input_dir)
        create_demo_files(input_dir)

        department_files = [f"{dept}.txt" for dept in DEPARTMENTS]
        result = process_files(input_dir, department_files, output_dir)

        print("\nDEMO VALIDATION")
        print("-" * 72)
        print(f"Files opened successfully: {result['files_found']} / {len(DEPARTMENTS)}")
        print(f"Unique valid registrations: {len(result['master'])}")
        print(f"Event groups created: {len(result['event_groups'])}")
        print(f"Logged errors/issues: {len(result['errors'])}")

        print("\nMASTER LIST")
        print("-" * 72)
        for record in result["master"]:
            print(
                f"{record['register_number']} | {record['name']} | "
                f"{record['department']} | {record['email']} | "
                f"{', '.join(record['events'])}"
            )

        print("\nEVENT COUNTS")
        print("-" * 72)
        for event, participants in sorted(result["event_groups"].items()):
            print(f"{event}: {len(participants)}")

        print("\nERROR LOG")
        print("-" * 72)
        for entry in result["errors"]:
            print(entry)

        # Read generated reports to verify files were created and contain data.
        report_files = sorted(os.listdir(output_dir))
        print("\nGENERATED OUTPUT FILES")
        print("-" * 72)
        for name in report_files:
            print(name)

        assert len(result["master"]) == 8
        assert any("DUPLICATE" in entry for entry in result["errors"])
        assert any("invalid email" in entry for entry in result["errors"])
        assert any("REJECTED" in entry for entry in result["errors"])
        assert any("MISSING FILE" in entry for entry in result["errors"])
        assert "master_list.csv" in report_files
        assert "summary_report.txt" in report_files
        assert "error_log.txt" in report_files

        print("\nAll demonstration assertions: PASSED")
        print("Temporary demo files and reports will be cleaned up automatically.")

    benchmark_duplicate_detection()

    print("\nFINAL DESIGN DECISION")
    print("-" * 72)
    print("Use a set for duplicate detection: average O(1) membership per record,")
    print("so processing n records is average O(n). List searching can approach")
    print("O(n^2). The set needs extra hash-table memory, but is justified for")
    print("large registrations. Per-file exception handling keeps processing alive.")


if __name__ == "__main__":
    main()
