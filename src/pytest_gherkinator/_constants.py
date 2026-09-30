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

"""Constants used within the ``pytest-gherkinator`` plugin."""

MARKS: dict[str, str] = {
    # Risk levels
    "edge": "gherkinator risk level 'edge' (executed first)",
    "beta": "gherkinator risk level 'beta'",
    "candidate": "gherkinator risk level 'candidate'",
    "stable": "gherkinator risk level 'stable' (executed last)",
    # Plan statuses
    "planned": "gherkinator plan status 'planned' (skipped by pytest-gherkinator)",
    "implemented": "gherkinator plan status 'implemented'",
    "deprecated": "gherkinator plan status 'deprecated' (skipped by pytest-gherkinator)",
    # Test types
    "functional": "gherkinator test type 'functional' (executed first within its risk level)",
    "solution": "gherkinator test type 'solution'",
    "reliability": "gherkinator test type 'reliability'",
    "security": "gherkinator test type 'security'",
    "performance": "gherkinator test type 'performance' (executed last within its risk level)",
}
"""Mark registration table: mark name to its ``--markers`` help text."""

RISKS = ("edge", "beta", "candidate", "stable")
"""Risk level values of the gherkinator YAML schema ``risk`` field."""

RISK_ORDER = {"edge": 0, "beta": 1, "candidate": 2, "stable": 3}
"""Execution order for risk levels: ``edge`` first, ``stable`` last."""

SKIP_STATUSES = frozenset({"planned", "deprecated"})
"""Plan statuses whose scenarios are skipped at runtime."""

STATUSES = ("planned", "implemented", "deprecated")
"""Status values of the gherkinator YAML schema ``status`` field."""

TYPES = ("functional", "solution", "performance", "reliability", "security")
"""Test type values of the gherkinator YAML schema ``type`` field."""

TYPE_ORDER = {
    "functional": 0,
    "solution": 1,
    "reliability": 2,
    "security": 3,
    "performance": 4,
}
"""Execution order for test types within a risk level: ``performance`` last."""
