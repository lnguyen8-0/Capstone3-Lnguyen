from agents.sql_agent import validate_sql

tests = [
    (
        "Valid SELECT",
        "SELECT * FROM clients WHERE status = 'active'",
        True,
    ),
    (
        "Destructive DELETE",
        "DELETE FROM clients WHERE id = 1",
        False,
    ),
    (
        "Column named deleted_at (whole-word match)",
        "SELECT id, deleted_at FROM clients",
        True,
    ),
    (
        "Stacked query with blocked keyword",
        "SELECT * FROM clients; DROP TABLE clients",
        False,
    ),
    (
        "Stacked two SELECTs (no blocked keyword)",
        "SELECT * FROM clients; SELECT * FROM projects",
        False,
    ),
]

all_passed = True
for name, query, expected_valid in tests:
    result = validate_sql(query)
    passed = result["valid"] == expected_valid
    status = "PASS" if passed else "FAIL"
    if not passed:
        all_passed = False
    print(f"[{status}] {name}")
    print(f"       Query:    {query}")
    print(f"       Expected: {'ALLOW' if expected_valid else 'BLOCK'} | Got: {'ALLOW' if result['valid'] else 'BLOCK'} | Reason: {result['reason']}")
    print()

print("All tests passed!" if all_passed else "SOME TESTS FAILED.")
