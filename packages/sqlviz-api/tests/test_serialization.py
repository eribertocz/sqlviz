"""Tests for sqlviz_api.serialization.json_safe().

Covers every DuckDB-mapped Python type to ensure no query result
can raise a JSON serialization error.
"""

from __future__ import annotations

import datetime
import uuid
from decimal import Decimal

import pytest
from sqlviz_api.serialization import json_safe


class TestPrimitives:
    def test_none(self) -> None:
        assert json_safe(None) is None

    def test_bool_true(self) -> None:
        assert json_safe(True) is True

    def test_bool_false(self) -> None:
        assert json_safe(False) is False

    def test_bool_not_treated_as_int(self) -> None:
        # bool is a subclass of int; must stay bool, not become 1/0
        result = json_safe(True)
        assert isinstance(result, bool)

    def test_int(self) -> None:
        assert json_safe(42) == 42

    def test_int_negative(self) -> None:
        assert json_safe(-7) == -7

    def test_int_large(self) -> None:
        # HUGEINT / UBIGINT can be very large
        assert json_safe(10**30) == 10**30

    def test_float(self) -> None:
        assert json_safe(3.14) == pytest.approx(3.14)

    def test_float_nan_becomes_none(self) -> None:
        assert json_safe(float("nan")) is None

    def test_float_inf_becomes_none(self) -> None:
        assert json_safe(float("inf")) is None

    def test_float_neg_inf_becomes_none(self) -> None:
        assert json_safe(float("-inf")) is None

    def test_string(self) -> None:
        assert json_safe("hello") == "hello"

    def test_empty_string(self) -> None:
        assert json_safe("") == ""


class TestDecimal:
    def test_decimal_integer_value(self) -> None:
        assert json_safe(Decimal("42")) == pytest.approx(42.0)

    def test_decimal_fractional(self) -> None:
        assert json_safe(Decimal("3.14")) == pytest.approx(3.14)

    def test_decimal_negative(self) -> None:
        assert json_safe(Decimal("-99.99")) == pytest.approx(-99.99)

    def test_decimal_returns_float(self) -> None:
        assert isinstance(json_safe(Decimal("1.5")), float)

    def test_decimal_nan_becomes_none(self) -> None:
        assert json_safe(Decimal("nan")) is None

    def test_decimal_infinity_becomes_none(self) -> None:
        assert json_safe(Decimal("Infinity")) is None


class TestTemporal:
    def test_date(self) -> None:
        assert json_safe(datetime.date(2024, 1, 15)) == "2024-01-15"

    def test_datetime_naive(self) -> None:
        assert json_safe(datetime.datetime(2024, 1, 15, 10, 30, 0)) == "2024-01-15T10:30:00"

    def test_datetime_with_microseconds(self) -> None:
        result = json_safe(datetime.datetime(2024, 1, 15, 10, 30, 0, 123456))
        assert result == "2024-01-15T10:30:00.123456"

    def test_datetime_aware(self) -> None:
        dt = datetime.datetime(2024, 1, 15, 10, 30, tzinfo=datetime.timezone.utc)
        result = json_safe(dt)
        assert isinstance(result, str)
        assert "2024-01-15" in result

    def test_datetime_before_date(self) -> None:
        # datetime is a subclass of date; must not fall through to date branch
        val = datetime.datetime(2024, 6, 1, 12, 0, 0)
        result = json_safe(val)
        assert "T" in result  # datetime ISO includes "T", date ISO does not

    def test_time(self) -> None:
        assert json_safe(datetime.time(10, 30, 45)) == "10:30:45"

    def test_time_with_microseconds(self) -> None:
        result = json_safe(datetime.time(10, 30, 45, 123456))
        assert result == "10:30:45.123456"

    def test_timedelta_whole_seconds(self) -> None:
        assert json_safe(datetime.timedelta(seconds=90)) == pytest.approx(90.0)

    def test_timedelta_days(self) -> None:
        assert json_safe(datetime.timedelta(days=1)) == pytest.approx(86400.0)

    def test_timedelta_fractional(self) -> None:
        assert json_safe(datetime.timedelta(seconds=1, microseconds=500000)) == pytest.approx(1.5)


class TestUUID:
    def test_uuid(self) -> None:
        u = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
        assert json_safe(u) == "550e8400-e29b-41d4-a716-446655440000"

    def test_uuid_returns_string(self) -> None:
        assert isinstance(json_safe(uuid.uuid4()), str)


class TestBytes:
    def test_bytes_empty(self) -> None:
        assert json_safe(b"") == ""

    def test_bytes_hex(self) -> None:
        assert json_safe(b"\xde\xad\xbe\xef") == "deadbeef"

    def test_bytearray(self) -> None:
        assert json_safe(bytearray(b"\x00\xff")) == "00ff"


class TestCompound:
    def test_list_empty(self) -> None:
        assert json_safe([]) == []

    def test_list_primitives(self) -> None:
        assert json_safe([1, 2, 3]) == [1, 2, 3]

    def test_list_with_decimal(self) -> None:
        result = json_safe([Decimal("1.5"), Decimal("2.5")])
        assert result == pytest.approx([1.5, 2.5])

    def test_list_nested(self) -> None:
        result = json_safe([[1, 2], [3, 4]])
        assert result == [[1, 2], [3, 4]]

    def test_list_with_date(self) -> None:
        result = json_safe([datetime.date(2024, 1, 1)])
        assert result == ["2024-01-01"]

    def test_tuple_treated_as_list(self) -> None:
        result = json_safe((1, 2, 3))
        assert result == [1, 2, 3]

    def test_dict_empty(self) -> None:
        assert json_safe({}) == {}

    def test_dict_primitives(self) -> None:
        assert json_safe({"a": 1, "b": 2}) == {"a": 1, "b": 2}

    def test_dict_with_decimal_values(self) -> None:
        result = json_safe({"x": Decimal("9.99")})
        assert result == {"x": pytest.approx(9.99)}

    def test_dict_keys_coerced_to_str(self) -> None:
        result = json_safe({1: "one", 2: "two"})
        assert result == {"1": "one", "2": "two"}

    def test_dict_nested(self) -> None:
        result = json_safe({"outer": {"inner": Decimal("1")}})
        assert result == {"outer": {"inner": pytest.approx(1.0)}}

    def test_list_with_none(self) -> None:
        assert json_safe([None, 1, None]) == [None, 1, None]


class TestFallback:
    def test_unknown_type_becomes_str(self) -> None:
        class Exotic:
            def __str__(self) -> str:
                return "exotic"

        assert json_safe(Exotic()) == "exotic"

    def test_never_raises(self) -> None:
        # Broad check: none of these should raise
        values: list[object] = [
            None, True, False, 0, -1, 10**30,
            0.0, float("nan"), float("inf"),
            Decimal("0"), Decimal("nan"), Decimal("Infinity"),
            "", "hello",
            datetime.date.today(),
            datetime.datetime.now(),
            datetime.datetime.now(datetime.timezone.utc),
            datetime.time(0, 0),
            datetime.timedelta(0),
            uuid.uuid4(),
            b"", b"\xff",
            [], [1, [2, [3]]],
            {}, {"k": [datetime.date(2000, 1, 1)]},
        ]
        import json
        for v in values:
            result = json_safe(v)
            # Must be serializable by the stdlib json module
            json.dumps(result)
