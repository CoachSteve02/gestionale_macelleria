## 2026-08-23T11:06:19Z

# Dispatch for Functional & Boundary Challenger

Empirically challenge and test the implementation of the dynamic Carico Merci form and validation rules:
1. Write and run stress / boundary tests exercising:
   - All categories: Bovino, Suino, Avicolo, Spezie, Latticini, Preparati, unknown/empty category.
   - Missing fields: meat with 0, 1, 2, 3 country fields; meat with no dates; meat with only `data_macellazione`; meat with only `data_scadenza`; meat with both dates.
   - Invalid dates: `data_macellazione` in future; `data_scadenza` in past; `data_scadenza < data_macellazione`.
   - String inputs: whitespace-only country strings, special characters, long strings.
   - Non-meat: country fields populated (should be saved as NULL or ignored), empty date behavior.
2. Verify exit codes, flash messages, and DB transaction rollback on failures vs commits on success.

Document all empirical test runs, outputs, and your verdict (`APPROVE` or `REQUEST_CHANGES`) in `handoff.md`.
