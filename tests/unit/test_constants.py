# Copyright 2026 Canonical Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Consistency tests for the gherkinator schema constants."""

from pytest_gherkinator import RISK_ORDER, RISKS, SKIP_STATUSES, STATUSES, TYPE_ORDER, TYPES


def test_risk_order_covers_the_risk_schema() -> None:
    """Every risk value has exactly one execution position."""
    assert set(RISK_ORDER) == set(RISKS)
    assert list(RISK_ORDER.values()) == list(range(len(RISKS)))


def test_type_order_covers_the_type_schema() -> None:
    """Every type value has exactly one execution position."""
    assert set(TYPE_ORDER) == set(TYPES)
    assert list(TYPE_ORDER.values()) == list(range(len(TYPES)))


def test_skip_statuses_are_valid_statuses() -> None:
    """Skipped statuses are a subset of the status schema."""
    assert SKIP_STATUSES <= set(STATUSES)
    assert "implemented" not in SKIP_STATUSES
