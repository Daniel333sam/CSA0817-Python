import re
from time import perf_counter


def normalise_phone(phone):
    if not phone:
        return ""

    digits = re.sub(r"\D", "", phone)

    if len(digits) == 10:
        return "91" + digits
    if len(digits) == 12 and digits.startswith("91"):
        return digits

    return ""  # Unknown or unsupported format; do not guess


def clean_name(name):
    return " ".join(name.split()) if name else ""


def merge_contacts(records):
    merged = {}
    unresolved = []

    for contact in records:
        phone = contact.get("phone", "")
        key = normalise_phone(phone)

        if not key:
            unresolved.append(contact)
            continue

        if key not in merged:
            merged[key] = {
                "names": set(),
                "phones": set(),
                "emails": set()
            }

        name = clean_name(contact.get("name", ""))
        email = contact.get("email", "").strip().lower()

        if name:
            merged[key]["names"].add(name)
        if phone:
            merged[key]["phones"].add(phone.strip())
        if email:
            merged[key]["emails"].add(email)

    return merged, unresolved


# Sample contacts from two phones and a SIM card
sample = [
    {
        "name": "Dr. Ravi",
        "phone": "+91 98400 12345",
        "email": "RAVI@EXAMPLE.COM"
    },
    {
        "name": "ravi kumar",
        "phone": "9840012345",
        "email": "ravi.alt@example.com"
    },
    {
        "name": "Anita",
        "phone": "9876543210",
        "email": "anita@example.com"
    },
    {
        "name": "No phone contact",
        "phone": "",
        "email": "none@example.com"
    },
    {
        "name": "Ravi",
        "phone": "+91-98400-12345",
        "email": ""
    }
]


# Merge and display the contacts
merged, unresolved = merge_contacts(sample)

for number, info in sorted(merged.items()):
    print(
        number,
        "| names:", sorted(info["names"]),
        "| phones:", sorted(info["phones"]),
        "| emails:", sorted(info["emails"])
    )

print("unresolved records:", len(unresolved))


# Verify the first merged group
assert len(merged) == 2
assert len(merged["919840012345"]["emails"]) == 2


# Scale test with unique phone numbers
def make_contacts(n):
    return [
        {
            "name": f"Person {i}",
            "phone": f"{9000000000 + i}",
            "email": f"user{i}@example.com"
        }
        for i in range(n)
    ]


for n in (1000, 100000):
    records = make_contacts(n)

    start = perf_counter()
    result, missing = merge_contacts(records)
    dictionary_time = perf_counter() - start

    print(
        n,
        "contacts | dictionary merge:",
        round(dictionary_time, 4),
        "s | groups:", len(result)
    )


# Naive pair-comparison illustration for a small input
def pair_comparisons(records):
    comparisons = 0

    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            comparisons += 1
            normalise_phone(records[i].get("phone")) == normalise_phone(
                records[j].get("phone")
            )

    return comparisons


print(
    "pair comparisons for 100 records:",
    pair_comparisons(make_contacts(100))
)
