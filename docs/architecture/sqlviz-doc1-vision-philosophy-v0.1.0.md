# SQLviz — Vision & Philosophy
**Version:** v0.1.0 (Draft)
**Status:** Work in Progress
**Last Updated:** 2026-06-08

---

## 1. What is SQLviz?

SQLviz is an open source analytical operating system where SQL is the only interface.

> "If you know SQL, you know SQLviz."

The user writes SQL. SQLviz infers everything else.

---

## 2. The Problem

Every BI tool today has the same fundamental flaw:

**The tool makes the user think about the tool.**

```
Power BI    → drag fields, configure visuals, manage relationships
Tableau     → drag dimensions, drop measures, choose mark types
Metabase    → pick question type, select columns, configure chart
Superset    → write SQL, then manually configure every visual
```

The user spends more time configuring the tool than thinking about the data.

This is backwards.

The user should think about the business problem.
The tool should handle everything else.

### The specific problems SQLviz solves

```
Problem 1 — Too many decisions
Every BI tool asks: what chart? what layout? what filter?
SQLviz answers those questions automatically.

Problem 2 — SQL is disconnected from visuals
In most tools, SQL is an afterthought.
You write SQL, then manually configure a chart.
In SQLviz, SQL is the primary artifact.
The visual emerges from the SQL automatically.

Problem 3 — No analytical intelligence
BI tools render data. They do not understand it.
SQLviz understands what the user is trying to analyze
and generates insights, recommendations and findings
without being asked.

Problem 4 — Configuration never ends
Every new dashboard requires the same manual work.
SQLviz learns from every execution and improves over time.
```

---

## 3. The Philosophy

Five principles that govern every decision in SQLviz.
If a feature violates any of these principles, it does not belong in SQLviz.

### Principle 1 — SQL First, Always

SQL is the only interface between the user and SQLviz.
No drag and drop. No field pickers. No visual query builders.

```
✅ User writes SQL → SQLviz generates the dashboard
❌ User drags fields → tool generates SQL
```

If the user knows SQL, they know SQLviz.
Nothing else to learn.

### Principle 2 — Infer Everything

Every decision that can be inferred should be inferred.
The user should never configure what SQLviz can figure out.

```
✅ SQLviz infers: chart type, layout, filters, titles, KPI trends
❌ SQLviz asks: "What chart do you want?"
```

When inference fails, the user has a minimal override.
The override exists but is rarely needed.

### Principle 3 — Explain Every Decision

Every inference SQLviz makes must be explainable.
No black boxes. No "the algorithm decided."

```
✅ "Line chart selected because:
    - temporal dimension detected (score: 0.95)
    - aggregated metric detected (score: 0.89)
    - sequential ordering detected (score: 0.76)"

❌ "Line chart selected."
```

Confidence is built through explanation, not just accuracy.

### Principle 4 — Learn Continuously

SQLviz improves with every execution.
Every correction the user makes teaches SQLviz something.

```
✅ User corrects Bar → Line
   SQLviz learns: this SQL pattern → Line chart
   Next time: automatic

❌ User corrects the same mistake every time
```

SQLviz should be more accurate on day 100 than on day 1.

### Principle 5 — Sustainable by One Person

Every architectural decision must be sustainable
by a single developer without external services.

```
✅ DuckDB — embedded, no server
✅ SQLite — embedded, no server
✅ sqlglot — pure Python, no API
✅ Svelte — compiles to static files

❌ Kafka — requires infrastructure
❌ Kubernetes — requires DevOps
❌ External ML APIs — requires payment
❌ Vector databases — unnecessary complexity
```

If it requires a server to run, it does not belong in the core.

---

## 4. The Vision

### Today — v0.1

```
User writes SQL
→ SQLviz infers chart type
→ User manually arranges layout
→ User configures filters with $variables
→ Dashboard is saved in .sqlviz file
```

Useful. But still requires manual work.

### Near future — v0.2

```
User writes SQL
→ SQLviz infers chart type (95% accuracy)
→ SQLviz infers layout automatically
→ SQLviz infers filters automatically
→ SQLviz generates panel titles automatically
→ Dashboard appears complete
→ User never touches layout or configuration
```

The user only writes SQL.

### Medium future — v0.3

```
User writes SQL
→ SQLviz understands the analytical intent
→ SQLviz generates the dashboard
→ SQLviz generates insights automatically
   "Revenue dropped 22% in October"
→ SQLviz generates recommendations
   "Investigate by: Country, Product, Channel"
→ SQLviz investigates autonomously
   "Argentina explains 78% of the drop"
```

SQLviz becomes an analytical partner, not just a tool.

### Long term — v1.0

```
One SQL file → complete analytical system

-- dashboard: Revenue Analysis

SELECT COUNT(*) AS total_orders FROM orders;
SELECT date, SUM(revenue) FROM orders GROUP BY date;
SELECT country, SUM(revenue) FROM orders GROUP BY country;
SELECT product, COUNT(*) FROM orders GROUP BY product ORDER BY 2 DESC LIMIT 10;

→ SQLviz generates:
   Dashboard with 4 panels
   Correct chart for each query
   Optimal layout
   Relevant filters
   Automatic insights
   Recommendations for next analysis
```

Zero configuration. Just SQL.

---

## 5. What Makes SQLviz Different

Honest comparison with existing tools.

```
                    Power BI  Tableau  Metabase  Superset  SQLviz
SQL First           ❌        ❌       Partial   Partial   ✅
Auto Chart          ❌        ❌       ❌        ❌        ✅
Auto Layout         ❌        ❌       ❌        ❌        ✅
Auto Filters        ❌        ❌       ❌        ❌        ✅
Auto Insights       ❌        ❌       ❌        ❌        ✅
Explainable         ❌        ❌       ❌        ❌        ✅
Learns Over Time    ❌        ❌       ❌        ❌        ✅
No Server Required  ❌        ❌       ❌        ❌        ✅
Single File Project ❌        ❌       ❌        ❌        ✅
Open Source         ❌        ❌       ✅        ✅        ✅
```

The key insight:

> Every existing BI tool makes the user serve the tool.
> SQLviz makes the tool serve the user.

---

## 6. The Analogy — SQLviz as Analytical Operating System

The most accurate way to understand SQLviz architecture
is to think of it as an operating system.

An operating system does not do one thing.
It coordinates resources, processes, memory, drivers, signals,
security, files, extensions and UI.

SQLviz is built the same way.

> **Correction (fourth review round):** the table below is the
> original conceptual analogy from when this document was first
> written — it maps 13 OS concepts to 13 hypothetical packages.
> DOC 8 (Construction Plan) later made the concrete build decision:
> V0.1 ships **6 packages**, not 13. `sqlviz-runtime` (the
> "Process Scheduler" row below) and `sqlviz-parser` (not shown
> below, but implied by "CPU / Execution Engine") were absorbed as
> internal modules of `sqlviz-inference` (DOC 5, Sections 4 and 12;
> DOC 8, Section 2) — they were never built as separately
> versioned packages. `sqlviz-sources`, `sqlviz-events`,
> `sqlviz-cache`, `sqlviz-plugins`, `sqlviz-benchmarks`,
> `sqlviz-security`, and `sqlviz-sdk` are all deferred to V0.2/V0.3+
> (DOC 8, Section 6, with exact version targets and rationale for
> each). The analogy itself — SQLviz as a small kernel plus a
> growing ecosystem — remains correct and is why DOC 8's smaller
> V0.1 package set still leaves room for every row below to
> eventually exist; only the *timing* changed, not the vision.

```
Traditional OS              SQLviz (original analogy)   V0.1 reality (DOC 8)

Kernel                  →   sqlviz-core              →   sqlviz-core
Process Scheduler       →   sqlviz-runtime           →   merged into
                                                          sqlviz-inference
CPU / Execution Engine  →   sqlviz-inference         →   sqlviz-inference
                                                          (includes parsing
                                                          and scheduling)
Drivers                 →   sqlviz-sources           →   deferred to V0.2
Filesystem              →   sqlviz-storage           →   sqlviz-storage
System Signals          →   sqlviz-events            →   deferred to V0.3+
Memory Cache            →   sqlviz-cache             →   deferred to V0.2
Package Manager         →   sqlviz-plugins           →   deferred to V0.3
Shell / Terminal        →   sqlviz-cli               →   sqlviz-cli
Desktop Environment     →   sqlviz-web               →   sqlviz-web
System Diagnostics      →   sqlviz-benchmarks        →   lives inside
                                                          sqlviz-inference
                                                          until V0.2
Security Layer          →   sqlviz-security          →   lives inside
                                                          sqlviz-api until
                                                          V0.2/DOC 7 roles grow
Developer SDK           →   sqlviz-sdk               →   deferred to V0.3+
```

### Why this analogy matters

A well designed OS has a small, stable kernel.
Everything else connects through contracts.
You can add drivers, applications, plugins
without modifying the kernel.

SQLviz is built the same way:

```
sqlviz-core defines contracts.
All other packages implement those contracts.
The core never changes.
The ecosystem grows without limit.
```

### SQL as the user interface

In an OS, users interact through a shell.
The shell translates human commands into kernel operations.

In SQLviz, SQL is the shell.

```
User writes:
SELECT date, SUM(revenue) FROM sales GROUP BY date

SQLviz kernel processes:
→ Parse SQL to AST
→ Extract fingerprint: TIME_SERIES_AGGREGATION
→ Extract features: temporal_dimension=true, aggregation=SUM
→ Infer intent: Trend (confidence: 0.94)
→ Infer chart: Line (confidence: 0.96)
→ Infer layout: full_width, position=after_kpis
→ Generate title: "Revenue over time"
→ Generate insights: trend_strength, anomalies
→ Generate recommendations: by_country, by_product
→ Render dashboard
```

All of this happens automatically.
The user only wrote SQL.

---

## 7. Design Principles

Rules that are never broken.
These are not guidelines. They are hard constraints.

### Rule 1 — No Hardcoding

Nothing is hardcoded. Everything is configurable through contracts.

```python
# ❌ Wrong
if column_name == "revenue":
    metric_type = "financial"

# ✅ Correct
semantic_type = semantic_engine.classify(column_name)
```

Rules live in YAML files that can be overridden by plugins.
The engine reads rules. The engine does not contain rules.

### Rule 2 — No Direct Dependencies Between Packages

Packages never import each other directly.
They communicate through the RuntimeContext defined in sqlviz-core.

```python
# ❌ Wrong
from sqlviz_inference import IntentEngine
result = IntentEngine().run(sql)

# ✅ Correct
context = RuntimeContext(sql=sql)
context = runtime.execute(context)
intent = context.intents
```

### Rule 3 — Every Engine Returns an Explanation

No engine returns a result without an explanation.

```python
# ❌ Wrong
return ChartResult(type="line")

# ✅ Correct
return ChartResult(
    type="line",
    confidence=0.96,
    explanation=Explanation(
        evidence=["temporal_dimension", "aggregation", "sequential_order"],
        rules=["TEMPORAL_LINE_RULE"],
        scores={"temporal": 0.95, "aggregation": 0.89}
    )
)
```

### Rule 4 — Graceful Degradation Always

If any engine fails, the system continues with defaults.
The user always sees something useful.

```
Parser fails       → use column names as-is
Semantic fails     → use raw column names
Intent fails       → default to Comparison intent
Chart fails        → default to Table chart
Layout fails       → default to single column layout
Insights fail      → show dashboard without insights
```

Never show a blank screen.
Never crash because one engine had low confidence.

### Rule 5 — Confidence Is Always Explicit

Every inference carries a confidence score between 0.0 and 1.0.
No engine makes binary decisions without a score.

```python
# ❌ Wrong
if is_temporal:
    chart = "line"

# ✅ Correct
confidence = calculate_temporal_score(features)
candidates.append(ChartCandidate(type="line", confidence=confidence))
```

### Rule 6 — Fast Path First, Slow Path Background

The user never waits for analysis.

```
Fast Path  (<1 second)  → Dashboard rendered
Slow Path  (<3 seconds) → Insights appear
Background (<10 seconds)→ Recommendations appear
                        → Autonomous findings appear
```

Analysis runs in the background.
The dashboard is immediate.

### Rule 7 — One Module, One Responsibility

Each module does exactly one thing.
If a module is doing two things, it should be two modules.

> **Correction (fourth review round):** this rule's original
> example used `sqlviz-parser` as if it were its own top-level
> package, illustrating "one package, one responsibility." DOC 5
> and DOC 8 later settled SQL parsing as an internal *module*
> inside `sqlviz-inference` (not a separately versioned package) —
> the principle below is unchanged, only the example is corrected
> to module-level, matching DOC 5 Section 2 and DOC 8 Section 2.

```
parser module     → only parses SQL (DOC 5, Section 4)
sqlviz-inference  → only infers analytical intent
sqlviz-storage    → only manages persistence
sqlviz-api        → only handles HTTP
```

No module knows what another module does.
They only know the contracts defined in sqlviz-core,
or — within sqlviz-inference — the RuntimeContext (DOC 5,
Section 3).

---

## Appendix — Key Terminology

```
RuntimeContext    The carrier of all data that flows through
                  the entire inference pipeline, using
                  field-owned mutation — each module writes
                  only to fields it owns (DOC 5, Sections 3.4
                  and 16.1; this document originally called it
                  "immutable," which DOC 5's implementation
                  work corrected as inaccurate — see DOC 5
                  Section 16.1 for the full rationale).
                  Every engine receives it and returns it enriched.

Fingerprint       A normalized representation of a SQL pattern
                  independent of table names, column names or language.
                  TIME_SERIES_AGGREGATION is the same pattern in any SQL.

Intent            The analytical objective behind a SQL query.
                  Not what the SQL does — what the user wants to understand.

Explanation       The structured reasoning behind every inference.
                  Evidence + Rules + Scores + Confidence.

Gold Dataset      The set of SQL queries with known correct outputs
                  used to measure inference accuracy.
                  The release gate for every version of SQLviz.

brain.duckdb      The persistent DuckDB file that stores
                  all learned patterns, insights, and knowledge.
                  Separate from the user's project file.
                  Lives at ~/.sqlviz/brain.duckdb
```

---

*SQLviz Vision & Philosophy — v0.1.0 Draft*
*"The user writes SQL. SQLviz infers everything else."*
