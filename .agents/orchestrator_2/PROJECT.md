# Project: Dynamic Carico Merci & HACCP Meat Traceability

## Architecture
- **Stack**: Flask 3.0, PostgreSQL (psycopg2-binary), Jinja2, Tailwind CSS (CDN), Vanilla JS.
- **Frontend Architecture**:
  - `templates/carico.html` renders `<select name="id_articolo" ...>` with `<option>` elements containing `data-categoria="{{ art.categoria }}"`.
  - Vanilla JS event listener on `change` / `input` of `id_articolo` checks whether the selected option's category is one of `['Bovino', 'Suino', 'Avicolo']`.
  - If meat category: reveals the HACCP traceability container (`paese_nascita`, `paese_allevamento`, `paese_macellazione`, `paese_sezionamento`, `data_macellazione`) via CSS classes (e.g., removing `hidden`), sets appropriate required/validation state or visual cues.
  - If non-meat or default unselected: hides the HACCP section via CSS (e.g. `hidden`), clears or removes required constraints.
- **Backend Architecture**:
  - GET `/carico`: fetches active articles of type `TAGLIO` and `VARIO`, groups by category, passes to template.
  - POST `/salva_carico`: queries DB for the selected `id_articolo` to determine its `categoria`.
    - If `categoria` in `('Bovino', 'Suino', 'Avicolo')`: validates that `paese_nascita`, `paese_allevamento`, `paese_macellazione`, `paese_sezionamento` are non-empty and at least one of `data_macellazione` or `data_scadenza` is present. If validation fails, flashes user-friendly error and redirects back to `/carico`.
    - If non-meat: country fields and `data_macellazione` are optional (saved as `NULL` if empty).
    - Executes `INSERT INTO LOTTO_MADRE (..., data_macellazione, ...)` with proper params.
- **Database Schema**:
  - `LOTTO_MADRE` table gets `data_macellazione DATE NULL`.
  - `database.sql` updated with `data_macellazione DATE NULL` in `CREATE TABLE LOTTO_MADRE`.
  - Standalone migration statement provided / applied.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Client-side dynamic form | Show/hide HACCP meat section based on `data-categoria` on change, without page reload or AJAX | M1 | ORIGINAL_REQUEST R1 |
| 2 | DB migration & schema update | Add `data_macellazione DATE NULL` to `LOTTO_MADRE` and update `database.sql` | M2 | ORIGINAL_REQUEST R2 |
| 3 | Backend conditional validation & insert | Check category in `/salva_carico`, enforce HACCP rules for meat, insert `data_macellazione` | M3 | ORIGINAL_REQUEST R3 |
| 4 | UX and Tailwind visual styling | Distinct visual box/styling for HACCP section in `templates/carico.html` | M4 | ORIGINAL_REQUEST R4 |
| 5 | Verification and non-regression | Local app startup, GET/POST testing for meat & non-meat, check routes | M5 | ORIGINAL_REQUEST AC |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Survey & Technical Plan | Explore FE, BE/DB, QA integration | None | DONE |
| M2 | Implementation | Implement R1, R2, R3, R4 in templates/carico.html, app.py, database.sql | M1 | DONE |
| M3 | Review & Challenger Testing | Independent reviews + dynamic execution tests | M2 | DONE |
| M4 | Forensic Audit | Verify integrity, no hardcoding, genuine implementation | M3 | DONE |
| M5 | Final Gate & Delivery | Gate sign-off and report to Sentinel | M4 | DONE |

## Code Layout
- `app.py`: Flask routes (`/carico`, `/salva_carico`), validation logic, DB queries.
- `templates/carico.html`: Jinja2 template with dynamic vanilla JS and Tailwind classes.
- `database.sql`: Base database schema definition.
- `templates/`: Other templates to ensure no regressions.
