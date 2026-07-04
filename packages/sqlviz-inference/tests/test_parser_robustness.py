"""Paso 6 — Parser robustness: 4 cases × 4 dirty SQL variants = 16 tests.

Verifies that cosmetic SQL formatting (mixed case, double-quoted identifiers,
inline comments, irregular whitespace) never changes inference results.
Each variant must produce exactly the same (intent, chart, quality) triple
as its clean equivalent.
"""
from sqlviz_core.models import ColumnSchema
from sqlviz_inference import infer
from sqlviz_inference.result import InferenceResult

# ── Shared fixtures ──────────────────────────────────────────────────────────

_TREND_SCHEMA = [
    ColumnSchema(name="month",   type="DATE"),
    ColumnSchema(name="revenue", type="DOUBLE"),
]
_TREND_DATA = [
    {"month": f"2024-{i:02d}-01", "revenue": 8000 + (i - 1) * 1182}
    for i in range(1, 13)
]

_COMP_SCHEMA = [
    ColumnSchema(name="category", type="VARCHAR"),
    ColumnSchema(name="revenue",  type="DOUBLE"),
]
_COMP_DATA = [
    {"category": "Electronics", "revenue": 45000},
    {"category": "Clothing",    "revenue": 28000},
    {"category": "Food",        "revenue": 19000},
    {"category": "Sports",      "revenue": 14000},
    {"category": "Books",       "revenue": 12000},
]

_RANK_SCHEMA = [
    ColumnSchema(name="product", type="VARCHAR"),
    ColumnSchema(name="revenue", type="DOUBLE"),
]
_RANK_DATA = [
    {"product": f"Product_{i}", "revenue": 95000 - (i - 1) * 5800}
    for i in range(1, 16)
]

_DETAIL_SCHEMA = [
    ColumnSchema(name="id",         type="INTEGER"),
    ColumnSchema(name="name",       type="VARCHAR"),
    ColumnSchema(name="email",      type="VARCHAR"),
    ColumnSchema(name="created_at", type="DATE"),
]
_DETAIL_DATA = [
    {
        "id": i,
        "name": f"Customer_{i}",
        "email": f"c{i}@example.com",
        "created_at": f"2024-{(i % 12) + 1:02d}-01",
    }
    for i in range(1, 31)
]


def _triple(r: InferenceResult) -> tuple[str, str, str]:
    return (r.intent_winner, r.chart_winner, r.intent_quality)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _trend(sql: str) -> InferenceResult:
    return infer(sql=sql, schema=_TREND_SCHEMA, data=_TREND_DATA)


def _comparison(sql: str) -> InferenceResult:
    return infer(sql=sql, schema=_COMP_SCHEMA, data=_COMP_DATA)


def _ranking(sql: str) -> InferenceResult:
    return infer(sql=sql, schema=_RANK_SCHEMA, data=_RANK_DATA)


def _detail(sql: str) -> InferenceResult:
    return infer(sql=sql, schema=_DETAIL_SCHEMA, data=_DETAIL_DATA)


# ── Base (reference) results — computed once ──────────────────────────────────

_TREND_BASE    = _triple(_trend(
    "SELECT month, SUM(revenue) FROM sales GROUP BY month ORDER BY month"
))
_COMP_BASE     = _triple(_comparison(
    "SELECT category, SUM(revenue) FROM sales GROUP BY category"
))
_RANKING_BASE  = _triple(_ranking(
    "SELECT product, SUM(revenue) FROM sales GROUP BY product ORDER BY 2 DESC LIMIT 10"
))
_DETAIL_BASE   = _triple(_detail(
    "SELECT id, name, email, created_at FROM customers"
))


# ── Trend — 4 dirty variants ──────────────────────────────────────────────────

class TestParserRobustnessTrend:

    def test_mixed_case_keywords(self) -> None:
        r = _trend(
            "SeLeCt month, SUM(revenue) FrOm sales GrOuP By month OrDeR By month"
        )
        assert _triple(r) == _TREND_BASE

    def test_double_quoted_identifiers(self) -> None:
        r = _trend(
            'SELECT "month", SUM("revenue") FROM "sales" '
            'GROUP BY "month" ORDER BY "month"'
        )
        assert _triple(r) == _TREND_BASE

    def test_inline_comments(self) -> None:
        r = _trend(
            "-- monthly revenue report\n"
            "SELECT month, SUM(revenue) AS total -- the metric\n"
            "FROM sales\n"
            "GROUP BY month\n"
            "ORDER BY month"
        )
        assert _triple(r) == _TREND_BASE

    def test_irregular_whitespace(self) -> None:
        r = _trend(
            "SELECT month,SUM(revenue)\n"
            "FROM sales\n"
            "    GROUP BY month\n"
            "ORDER BY    month"
        )
        assert _triple(r) == _TREND_BASE


# ── Comparison — 4 dirty variants ─────────────────────────────────────────────

class TestParserRobustnessComparison:

    def test_mixed_case_keywords(self) -> None:
        r = _comparison(
            "sElEcT category, SUM(revenue) FrOm sales GrOuP By category"
        )
        assert _triple(r) == _COMP_BASE

    def test_double_quoted_identifiers(self) -> None:
        r = _comparison(
            'SELECT "category", SUM("revenue") FROM "sales" GROUP BY "category"'
        )
        assert _triple(r) == _COMP_BASE

    def test_inline_comments(self) -> None:
        r = _comparison(
            "SELECT category, -- the grouping column\n"
            "SUM(revenue) -- total revenue\n"
            "FROM sales GROUP BY category"
        )
        assert _triple(r) == _COMP_BASE

    def test_irregular_whitespace(self) -> None:
        r = _comparison(
            "SELECT  category,  SUM(revenue)  FROM  sales  GROUP  BY  category"
        )
        assert _triple(r) == _COMP_BASE


# ── Ranking — 4 dirty variants ────────────────────────────────────────────────

class TestParserRobustnessRanking:

    def test_mixed_case_keywords(self) -> None:
        r = _ranking(
            "SELECT product, SUM(revenue) fRoM sales "
            "GROUP BY product ORDER BY 2 dEsC LIMIT 10"
        )
        assert _triple(r) == _RANKING_BASE

    def test_double_quoted_identifiers(self) -> None:
        r = _ranking(
            'SELECT "product", SUM("revenue") FROM "sales" '
            'GROUP BY "product" ORDER BY 2 DESC LIMIT 10'
        )
        assert _triple(r) == _RANKING_BASE

    def test_inline_comments(self) -> None:
        r = _ranking(
            "SELECT product, SUM(revenue) -- total\n"
            "FROM sales -- the fact table\n"
            "GROUP BY product ORDER BY 2 DESC LIMIT 10"
        )
        assert _triple(r) == _RANKING_BASE

    def test_irregular_whitespace(self) -> None:
        r = _ranking(
            "SELECT product,SUM(revenue) FROM sales\n"
            "    GROUP BY product\n"
            "  ORDER BY 2 DESC\n"
            "LIMIT 10"
        )
        assert _triple(r) == _RANKING_BASE


# ── Detail — 4 dirty variants ─────────────────────────────────────────────────

class TestParserRobustnessDetail:

    def test_mixed_case_keywords(self) -> None:
        r = _detail(
            "sElEcT id, name, email, created_at FrOm customers"
        )
        assert _triple(r) == _DETAIL_BASE

    def test_double_quoted_identifiers(self) -> None:
        r = _detail(
            'SELECT "id", "name", "email", "created_at" FROM "customers"'
        )
        assert _triple(r) == _DETAIL_BASE

    def test_inline_comments(self) -> None:
        r = _detail(
            "-- customer master data\n"
            "SELECT id, name, email, created_at -- all fields\n"
            "FROM customers"
        )
        assert _triple(r) == _DETAIL_BASE

    def test_irregular_whitespace(self) -> None:
        r = _detail(
            "SELECT\n"
            "  id,\n"
            "  name,\n"
            "  email,\n"
            "  created_at\n"
            "FROM customers"
        )
        assert _triple(r) == _DETAIL_BASE
