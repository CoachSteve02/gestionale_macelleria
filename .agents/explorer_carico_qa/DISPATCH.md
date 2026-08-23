# Dispatch for QA & Verification Explorer

## 2026-08-23T10:58:15Z

Investigate test and verification setup:
- Check existing project structure, dependencies (`requirements.txt`), `.env`, database configuration.
- Check how to test Flask app locally (`python app.py`) or via Flask test client.
- Check routes `/carico`, `/salva_carico`, `/magazzino`, `/etichetta`, `/etichetta_taglio` to identify potential regression risks.
- Design comprehensive test cases:
  1. GET `/carico` - renders options with `data-categoria`, default unselected state.
  2. POST `/salva_carico` with meat category ("Bovino", "Suino", "Avicolo") without required country fields -> failure, flash error, redirect to `/carico`, no DB insert.
  3. POST `/salva_carico` with meat category without neither data_macellazione nor data_scadenza -> failure, flash error.
  4. POST `/salva_carico` with meat category, valid country fields and data_macellazione (with or without data_scadenza) -> success, inserted with data_macellazione.
  5. POST `/salva_carico` with non-meat category (e.g. "Spezie", "Latticini", "Preparati", etc.) with empty country fields / data_macellazione -> success, inserted with NULLs.
  6. Migration execution test on database.
  7. Route health check on `/magazzino`, `/etichetta`, `/etichetta_taglio`.
