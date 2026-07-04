"""Semantic Engine tests — DOC5 Section 6.6."""
from sqlviz_core.models import ColumnSchema
from sqlviz_inference.context import RuntimeContext
from sqlviz_inference.semantic.fuzzy_match import normalize_name
from sqlviz_inference.semantic.semantic_engine import SemanticEngine

engine = SemanticEngine()


class TestNormalization:

    def test_snake_case(self) -> None:
        assert normalize_name("total_revenue") == "total_revenue"

    def test_camel_case(self) -> None:
        assert normalize_name("totalRevenue") == "total_revenue"

    def test_spaces(self) -> None:
        assert normalize_name("Total Revenue") == "total_revenue"

    def test_special_chars(self) -> None:
        assert normalize_name("fecha_de_venta") == "fecha_de_venta"


class TestSemanticMatching:

    def test_revenue_english(self) -> None:
        assert engine.classify_column("revenue") == "METRIC_REVENUE"

    def test_revenue_spanish(self) -> None:
        assert engine.classify_column("ventas") == "METRIC_REVENUE"

    def test_revenue_alias(self) -> None:
        assert engine.classify_column("total_revenue") == "METRIC_REVENUE"

    def test_temporal_english(self) -> None:
        assert engine.classify_column("month") == "TEMPORAL_DIMENSION"

    def test_temporal_spanish(self) -> None:
        assert engine.classify_column("fecha") == "TEMPORAL_DIMENSION"

    def test_temporal_created_at(self) -> None:
        assert engine.classify_column("created_at") == "TEMPORAL_DIMENSION"

    def test_geographic_english(self) -> None:
        assert engine.classify_column("country") == "GEOGRAPHIC_DIMENSION"

    def test_geographic_spanish(self) -> None:
        assert engine.classify_column("pais") == "GEOGRAPHIC_DIMENSION"

    def test_product_entity(self) -> None:
        assert engine.classify_column("producto") == "PRODUCT_ENTITY"

    def test_customer_entity(self) -> None:
        assert engine.classify_column("cliente") == "CUSTOMER_ENTITY"

    def test_unknown_column(self) -> None:
        assert engine.classify_column("xyz_abc_123") is None


class TestFeatureVectorUpdate:

    def test_revenue_sets_dim30(self) -> None:
        schema = [
            ColumnSchema(name="month", type="DATE"),
            ColumnSchema(name="revenue", type="DOUBLE"),
        ]
        ctx = RuntimeContext(
            sql="SELECT month, SUM(revenue) FROM sales GROUP BY month",
            schema=schema,
        )
        ctx = engine.run(ctx)
        assert ctx.feature_vector[30] == 1.0  # METRIC_REVENUE
        assert ctx.feature_vector[31] == 1.0  # TEMPORAL_DIMENSION

    def test_spanish_columns(self) -> None:
        schema = [
            ColumnSchema(name="fecha", type="DATE"),
            ColumnSchema(name="ventas", type="DOUBLE"),
            ColumnSchema(name="region", type="VARCHAR"),
        ]
        ctx = RuntimeContext(
            sql="SELECT fecha, SUM(ventas) FROM ventas GROUP BY fecha",
            schema=schema,
        )
        ctx = engine.run(ctx)
        assert ctx.feature_vector[30] == 1.0  # METRIC_REVENUE  (ventas)
        assert ctx.feature_vector[31] == 1.0  # TEMPORAL_DIMENSION (fecha)
        assert ctx.feature_vector[32] == 1.0  # GEOGRAPHIC_DIMENSION (region)
