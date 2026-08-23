## 2026-08-23T11:02:21Z
Task assignment from parent:
Carico Merci HACCP dynamic form milestone.

Tasks:
1. Implement client-side dynamic form in templates/carico.html (R1 & R4) with data-categoria, distinct Tailwind HACCP section, and vanilla JS toggles/required state.
2. Implement backend conditional validation and 9-field INSERT in app.py /salva_carico (R2 & R3).
3. Update database.sql and execute the DB migration (ALTER TABLE LOTTO_MADRE ADD COLUMN IF NOT EXISTS data_macellazione DATE; ALTER TABLE LOTTO_MADRE ALTER COLUMN data_scadenza DROP NOT NULL;) on the PostgreSQL database.
4. Execute non-regression defensive updates if necessary.
5. Create and run automated verification tests (e.g. test_carico_verification.py) and verify python app.py starts up cleanly.
6. Write full changes, test outputs, and complete 5-section handoff.md in your working directory.
When finished, send a message to parent with the summary and handoff path.
