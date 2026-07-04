# Phase 7 — Manual QA Checklist
**Version:** v0.1.0 pre-release  
**Date:** 2026-07-04  
**Based on:** DOC8 Phase 7 exit criteria + Phase 4–6 exit criteria

Legend:
- `[auto]` — covered by automated tests (file noted in parentheses)
- `[manual]` — requires visual browser or terminal verification; mark `[x]` when confirmed

Instructions: work through `[manual]` items in order. Mark `[!]` with a note if
something is wrong. All `[manual]` items must be `[x]` before tagging v0.1.0.

---

## Prerequisites

Before starting, build the frontend and install the CLI:

```bash
cd packages/sqlviz-web && npm run build
uv tool install packages/sqlviz-cli --reinstall
```

---

## 1. CLI Flows

### 1.1 Demo mode (no arguments)

```bash
sqlviz
```

- [auto] No `.sqlviz` file is created anywhere on disk *(test_phase7_qa.py)*
- [manual] Terminal prints the SQLviz banner and "Demo Mode"
- [manual] Terminal prints "In-memory database. Nothing is saved."
- [manual] Browser opens automatically at `http://localhost:4000`
- [manual] `Ctrl+C` stops the server cleanly

```bash
sqlviz --no-browser
```

- [manual] Server starts but browser does NOT open
- [manual] Terminal output is otherwise identical to above

### 1.2 Persistent mode — new project

```bash
sqlviz qa_test
```

- [manual] Terminal prompts: `Set admin password:`
- [manual] Terminal prompts: `Confirm password:` after entering password
- [manual] If passwords don't match, prompts again
- [manual] If password shorter than 4 characters, error and re-prompt
- [manual] File `qa_test.sqlviz` is created in the current directory
- [manual] Terminal prints "Project created."
- [manual] Browser opens at `http://localhost:4000` and shows login screen

### 1.3 Persistent mode — open existing project

```bash
# (with qa_test.sqlviz already existing)
sqlviz qa_test
```

- [manual] Terminal does NOT prompt for "Set admin password"
- [manual] Browser opens at `http://localhost:4000` and shows login screen
- [manual] Logging in with the password set above succeeds

### 1.4 Invalid file

```bash
# Create a non-SQLviz file first: echo "hello" > not_valid.sqlviz
sqlviz not_valid.sqlviz
```

- [manual] Error message printed: "not a valid .sqlviz project" (or similar)
- [manual] Process exits cleanly (exit code non-zero)
- [manual] Browser does NOT open
- [manual] No crash, no traceback

### 1.5 Path with .sqlviz extension already included

```bash
sqlviz my_project.sqlviz
```

- [manual] Does not create `my_project.sqlviz.sqlviz`
- [manual] Behaves identically to `sqlviz my_project`

---

## 2. Auth Flows  *(persistent mode only — skip in demo mode)*

Start with `sqlviz qa_test` and open `http://localhost:4000`.

### 2.1 Login screen

- [manual] Login screen appears before any dashboard content
- [manual] Page title / logo reads "SQLviz"
- [manual] Password field is type="password" (characters masked)
- [manual] Pressing Enter submits the form (same as clicking Sign in)

### 2.2 Correct login

- [auto] Set-Cookie carries HttpOnly flag *(test_phase7_qa.py)*
- [manual] Enter the password set in §1.2 → redirected to the dashboard

### 2.3 Wrong password

- [auto] Wrong password → 401 with "Invalid password" *(test_auth.py)*
- [auto] No-password project returns same generic message *(test_auth.py)*
- [manual] Stays on login screen (no redirect on wrong password)

### 2.4 Session persistence

- [auto] Cookie from login works on subsequent protected requests *(test_phase7_qa.py)*
- [manual] Close and reopen the browser tab → still logged in

### 2.5 Logout

- [auto] Logout invalidates the session; cookie cleared *(test_auth.py)*
- [manual] Clicking logout clears the session in the UI
- [manual] Subsequent page load redirects to /login

### 2.6 Change password

- [auto] Wrong current password → 401 *(test_auth.py)*
- [auto] Correct current + new password → 200 *(test_auth.py)*
- [auto] Old password rejected after change *(test_auth.py)*
- [auto] New password works after change *(test_auth.py)*

### 2.7 Demo mode — no auth required

- [auto] `GET /api/v1/auth/me` returns `{"demo": true}` *(test_demo.py)*
- [auto] All API routes open without session in demo mode *(test_demo.py)*

### 2.8 Frontend protection (FastAPI 0.139.0, router.frontend + require_admin)

- [auto] `GET /` without session → 302 redirect to `/login` (persistent mode) *(test_phase7_qa.py::TestAuthFlows::test_root_redirects_to_login_without_session)*
- [auto] `GET /login` without session → 200 + text/html (login form loads) *(test_phase7_qa.py::TestAuthFlows::test_login_page_accessible_without_session)*
- [auto] `GET /` with valid session → 200 (dashboard loads) *(test_phase7_qa.py::TestAuthFlows::test_root_accessible_after_login)*
- [auto] `GET /` in demo mode → 200 without any session *(test_phase7_qa.py::TestAuthFlows::test_frontend_accessible_in_demo_mode)*
- [auto] API `GET /api/v1/auth/me` 401 is NOT redirected — returns JSON 401 *(test_phase7_qa.py::TestAuthFlows::test_api_401_not_redirected)*
- [manual] Open browser at `http://localhost:4000` with no prior session → login screen appears (visual verification)

---

## 3. Dashboard and Panel Flows

### 3.1 Demo mode auto-seed

Start `sqlviz` (no args), open `http://localhost:4000`:

- [auto] 4 panels render (kpi, line, bar, bar_horizontal) *(test_demo.py)*
- [auto] GET /demo/sql returns 4 semicolon-separated statements *(test_demo.py)*
- [manual] Dashboard appears automatically — no SQL writing required
- [manual] Edit mode is active on first load (Monaco editor visible)
- [manual] The 4 demo queries are pre-loaded in the Monaco editor

### 3.2 Write SQL → Run → panels appear

In the Monaco editor, type:

```sql
SELECT SUM(amount) AS total FROM (VALUES (100.0),(200.0),(300.0)) t(amount);

SELECT month, SUM(rev) AS revenue
FROM (VALUES (1,100.0),(2,150.0),(3,200.0),(4,180.0)) t(month,rev)
GROUP BY month ORDER BY month
```

- [auto] SUM aggregate → kpi *(test_phase7_qa.py)*
- [auto] Time-series → line *(test_phase7_qa.py)*
- [auto] Line chart returns 4 rows *(test_phase7_qa.py)*
- [manual] Press `Ctrl+Enter` → panels execute
- [manual] Status message shows "Statement 1 / 2…" then "Statement 2 / 2…"
- [manual] KPI panel shows a single formatted number

### 3.3 Three-panel dashboard

Clear editor and paste:

```sql
SELECT SUM(amount) AS total FROM (VALUES (100.0)) t(amount);

SELECT month, SUM(rev) AS rev
FROM (VALUES (1,10.0),(2,20.0),(3,15.0)) t(month,rev)
GROUP BY month ORDER BY month;

SELECT cat, SUM(val) AS total
FROM (VALUES ('A',30.0),('B',20.0),('C',10.0)) t(cat,val)
GROUP BY cat ORDER BY cat
```

- [auto] kpi + line + bar chart types produced *(test_phase7_qa.py)*
- [auto] All panels have col_span > 0 *(test_phase7_qa.py)*
- [manual] Three panels render in the browser

### 3.4 Panel titles

- [auto] Auto-generated title is non-empty *(test_phase7_qa.py)*
- [auto] Title contains column keywords *(test_phase7_qa.py)*

### 3.5 Delete a panel via overflow menu

- [manual] Hover a panel in Edit mode → overflow menu (···) appears
- [manual] Click ··· → menu shows: "Change chart", "Edit SQL", "Delete"
- [manual] Click Delete → panel is removed
- [manual] Remaining panels recompose (layout updates)

### 3.6 Edit SQL via overflow menu

- [manual] Click ··· → "Edit SQL" → Monaco editor scrolls/focuses to that panel's statement
- [manual] Modify the SQL and press `Ctrl+Enter` → panel updates

### 3.7 Change chart via overflow menu

- [manual] Click ··· → "Change chart" → dropdown of 8 chart types appears
- [manual] Select a different chart type → panel re-renders with that type
- [manual] Override persists: refresh/re-run keeps the manually selected chart type

---

## 4. Preview vs Edit Mode

With at least one panel visible:

### 4.1 Edit mode elements

Switch to Edit mode:

- [manual] SQL editor is visible at the bottom
- [manual] Run button and `Ctrl+Enter` shortcut label visible
- [manual] Hovering a panel shows the overflow menu (···)
- [manual] Hovering a panel shows the footer (elapsed ms · row count · DuckDB)
- [manual] Preview/Edit toggle shows "Edit" as active

### 4.2 Preview mode elements

Switch to Preview mode:

- [manual] SQL editor is hidden
- [manual] Run button is hidden
- [manual] Overflow menu (···) does NOT appear on hover
- [manual] Panel footer does NOT appear on hover
- [manual] Panel title and chart remain visible
- [manual] Preview/Edit toggle shows "Preview" as active

### 4.3 FilterBar visibility in both modes

*(Requires a panel with a $variable — see §6)*

- [manual] FilterBar appears in Preview mode when panels have $variables
- [manual] FilterBar appears in Edit mode when panels have $variables

---

## 5. Dark / Light Theme

- [manual] Default theme on first load is **dark**
- [manual] Toggle in the UI switches to light theme
- [manual] Toggle back switches to dark theme
- [manual] Monaco editor background follows the theme
- [manual] KPI trend colors (↑ green / ↓ red / → gray) are visible in both themes
- [manual] Panel borders and backgrounds look correct in both themes

---

## 6. Filter Flows

### 6.1 Basic $variable → FilterBar

Paste this SQL and run:

```sql
SELECT cat, SUM(val) AS total
FROM (VALUES ('A',30.0),('B',20.0),('C',10.0)) t(cat,val)
WHERE cat = $region
GROUP BY cat ORDER BY cat
```

- [manual] After running, FilterBar appears between the app-bar and dashboard area
- [manual] FilterBar shows a control labeled "region"
- [manual] FilterBar is visible in both Preview and Edit modes

### 6.2 Filter interaction

- [manual] Enter a value in the filter control → panel re-executes with that value
- [manual] Changing the filter value updates only the panels that use that variable
- [manual] Panels without that variable are not re-executed
- [manual] Empty filter value → panel does not re-execute

### 6.3 Multiple $variables

- [auto] Two $vars in SQL → two FilterControl entries *(test_phase7_qa.py)*
- [manual] Two filter controls appear in FilterBar
- [manual] Changing `$region` re-executes only panels using `$region`
- [manual] Panel with both variables only re-executes when both have values

### 6.4 8 control types

- [auto] VARCHAR equality → dropdown *(test_phase7_qa.py)*
- [auto] DATE column → date_picker *(test_phase7_qa.py)*
- [auto] Two DATE vars on same col → date_range_picker *(test_phase7_qa.py)*
- [auto] ANY() → multiselect *(test_phase7_qa.py)*
- [auto] ILIKE → search *(test_phase7_qa.py)*
- [auto] INTEGER column → numeric *(test_phase7_qa.py)*
- [auto] Two INTEGER vars on same col → range_slider *(test_phase7_qa.py)*
- [auto] BOOLEAN column → toggle *(test_phase7_qa.py)*
- [manual] All 8 control types render correctly in the FilterBar UI

### 6.5 Debounce

- [manual] Typing in a text filter does not fire re-execute on every keystroke
- [manual] Re-execute fires approximately 350ms after the last keystroke

---

## 7. Explainability — "Why This Chart?"

### 7.1 ⓘ icon trigger

- [auto] chart_quality ∈ {high, medium, low} for every query *(test_phase7_qa.py)*
- [auto] Clear KPI query → chart_quality="high" *(test_phase7_qa.py)*
- [manual] If quality is "medium" or "low", the ⓘ icon appears next to the panel title
- [manual] KPI panel (high confidence) shows **no** ⓘ icon
- [manual] Line chart (high confidence) shows **no** ⓘ icon

### 7.2 Explain panel content

- [auto] explanation list present *(test_phase7_qa.py)*
- [auto] chart_alternatives list present *(test_phase7_qa.py)*
- [auto] intent_confidence_gap + chart_confidence_gap are floats *(test_phase7_qa.py)*
- [auto] intent_quality and chart_quality valid strings *(test_phase7_qa.py)*
- [auto] score_trace dict present *(test_phase7_qa.py)*
- [manual] Right-side drawer opens (ExplainPanel)
- [manual] Shows "Why a [chart type] chart?" in the drawer

### 7.3 "Use X instead" from Explain panel

- [manual] Selecting an alternative chart from the explain panel re-renders the panel
- [manual] The override applies persistently (re-run keeps the choice)

### 7.4 Explain panel close

- [manual] Clicking outside the drawer or a close button closes it
- [manual] Dashboard grid is usable when drawer is closed

---

## 8. KPI Shelf Layout

### 8.1 Single KPI (n=1)

- [auto] col_span=4 *(test_phase7_qa.py)*
- [auto] col_offset=4 (centered: 4+4+4=12) *(test_phase7_qa.py)*
- [manual] Panel visually centered in the 12-column grid

### 8.2 Two KPIs (n=2)

- [auto] Each col_span=4 *(test_phase7_qa.py)*
- [auto] First col_offset=2 (centered: 2+4+4+2=12) *(test_phase7_qa.py)*

### 8.3 Three KPIs (n=3)

- [auto] Each col_span=4 (4+4+4=12) *(test_phase7_qa.py)*

### 8.4 Four KPIs (n=4)

- [auto] Each col_span=3, sum=12 *(test_phase7_qa.py)*

### 8.5 KPI + other panels mixed

- [auto] KPI row_index < chart row_index *(test_phase7_qa.py)*
- [manual] KPIs appear in their own top row visually
- [manual] Line chart appears below the KPI row

### 8.6 KPI trend indicator

- [auto] trend_direction_label ∈ {growing, declining, flat, unknown} *(test_phase7_qa.py)*
- [auto] Single KPI aggregate → "unknown" *(test_phase7_qa.py)*
- [manual] KPI value renders formatted (e.g. 42,000 not 42000)
- [manual] Trend arrow shown only when label is not "unknown"
- [manual] ↑ arrow is green (`--sqlviz-positive`)
- [manual] ↓ arrow is red (`--sqlviz-negative`)
- [manual] → arrow is gray (`--sqlviz-neutral`)
- [manual] No trend arrow when label is "unknown"

---

## 9. Share Flows  *(persistent mode only — skip in demo mode)*

### 9.1 Generate a private share link

- [auto] Private share accessible without session cookie *(test_phase7_qa.py)*
- [auto] Response body includes dashboard data *(test_phase7_qa.py)*
- [auto] Link generated — 201 Created with token *(test_shares.py)*
- [manual] Open the link in a different browser/incognito → dashboard loads without login
- [manual] Viewer cannot see the SQL editor, overflow menus, or footer
- [manual] Viewer can see panels, titles, charts, and FilterBar (if filters exist)

### 9.2 Password-protected share link

- [auto] Wrong unlock password → 401 *(test_phase7_qa.py)*
- [auto] Correct unlock password → 200 *(test_phase7_qa.py)*
- [manual] Viewer sees a password prompt in the browser
- [manual] Share works across separate browser sessions

### 9.3 Public share link

- [auto] Public share accessible without session *(test_phase7_qa.py)*
- [manual] Open link in browser → loads directly, no prompt of any kind

### 9.4 Revoke a specific share

- [auto] Revoked token → 404 *(test_shares.py)*
- [auto] Other shares remain valid after one is revoked *(test_shares.py)*
- [manual] Confirm in browser that revoked link returns error

### 9.5 Regenerate session secret (revoke ALL shares)

- [auto] All shares invalidated after regenerate *(test_shares.py)*
- [auto] New shares work after regeneration *(test_shares.py)*
- [manual] Confirm in browser that old links return error after regeneration

---

## 10. The 4 Example Dashboard Panels

### 10.1 Demo mode

Run `sqlviz`, open `http://localhost:4000`:

- [auto] Exactly 4 panels render *(test_demo.py)*
- [auto] Chart types: kpi + line + bar + bar_horizontal *(test_demo.py)*
- [auto] **Panel 1 — KPI**: value = 42,000.0 *(test_phase7_qa.py)*
- [auto] **Panel 1 — KPI**: col_span=4 in KPI Shelf *(test_phase7_qa.py)*
- [auto] **Panel 2 — Line**: 6 data points *(test_phase7_qa.py)*
- [auto] **Panel 2 — Line**: full-width col_span=12 *(test_phase7_qa.py)*
- [auto] **Panel 3 — Bar**: 4 category rows *(test_phase7_qa.py)*
- [auto] **Panel 4 — Bar Horizontal**: ordered by revenue DESC *(test_phase7_qa.py)*
- [auto] All panels have non-empty data *(test_demo.py)*
- [manual] Dashboard auto-loads (no SQL writing needed)
- [manual] KPI shows formatted number (42,000.0)
- [manual] Bar: 4 categories in alphabetical order on X axis
- [manual] Bar Horizontal: highest bar at top

### 10.2 Persistent mode regression

- [auto] Same 4 chart types in persistent mode *(test_phase7_qa.py)*
- [manual] No "singleton connection" errors or crashes (DOC2 §5 regression)
- [manual] UI behavior is **identical** to demo mode

### 10.3 Demo mode singleton-connection regression (DOC2 §5)

- [auto] Create → execute → delete → create → execute → no errors *(test_demo.py)*
- [manual] Multiple sequential executions on `:memory:` work in the browser
- [manual] No "connection closed" or "database is gone" errors

---

## 11. Edge Cases and Error Handling

### 11.1 Invalid SQL

In the Monaco editor, type and run:

```sql
SELECT this is not valid sql ;;;
```

- [auto] fallback_applied=True + data=[] *(test_execute.py)*
- [manual] Error message appears in the toolbar (not a crash)
- [manual] Previously displayed panels remain visible

### 11.2 SQL that returns no rows

```sql
SELECT month, SUM(rev) AS rev
FROM (VALUES (1,10.0),(2,20.0)) t(month,rev)
WHERE month > 999
GROUP BY month
```

- [auto] data=[] + HTTP 200 *(test_phase7_qa.py)*
- [manual] Panel renders without crash (empty state or empty chart)

### 11.3 $variable with no value provided

```sql
SELECT * FROM (VALUES (1,'A'),(2,'B'),(3,'C')) t(id,val)
WHERE val = $category
```

- [auto] filter_controls non-empty (inference-only mode) *(test_phase7_qa.py)*
- [auto] data=[] *(test_phase7_qa.py)*
- [manual] FilterBar appears with the control
- [manual] After entering a value in FilterBar → panel executes and shows data

### 11.4 Fewer panels after delete

- [auto] Delete all → panel list is empty *(test_phase7_qa.py)*
- [auto] New SQL creates fresh executable panels *(test_phase7_qa.py)*
- [manual] Empty state message visible ("Write SQL below and press Ctrl+Enter to run")

---

## 12. Final Sign-off

All `[manual]` items above checked `[x]`:

- [ ] Demo mode exit criterion: `sqlviz` → auto-dashboard → zero manual config
- [ ] Persistent mode exit criterion: `sqlviz qa_test` → login → paste 4 queries → same result as demo
- [ ] Demo mode and persistent mode produce **identical UI behavior** for the same SQL (DOC2 §5 regression confirmed clean)
- [ ] All automated tests passing: `uv run pytest packages/ -q`

---

*Ready to tag v0.1.0 when all `[manual]` items above are `[x]`.*
