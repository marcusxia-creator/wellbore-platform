"""Tests for the WellStor enums.

Pure-logic tests: they assert the integer encodings stay aligned with the
upstream processed-data pipeline and require no database access.
"""

from apps.wellstor.enums import DeepestCasingType, PerforationType


class TestPerforationType:
    def test_integer_values(self):
        assert PerforationType.UNDEFINED == 0
        assert PerforationType.TREAT == 1
        assert PerforationType.PERF == 2
        assert PerforationType.FRAC == 3
        assert PerforationType.OPENHOLE == 4
        assert PerforationType.PLUG == 5
        assert PerforationType.LINER == 6

    def test_member_count(self):
        assert len(PerforationType.choices) == 7


class TestDeepestCasingType:
    def test_integer_values(self):
        assert DeepestCasingType.UNKNOWN == 0
        assert DeepestCasingType.INTERMEDIATE == 1
        assert DeepestCasingType.PRODUCTION == 2
        assert DeepestCasingType.LINER == 3
        assert DeepestCasingType.SURFACE == 4
        assert DeepestCasingType.CONDUCTOR == 5

    def test_member_count(self):
        assert len(DeepestCasingType.choices) == 6
