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

"""Unit tests for the ``pytest-gherkinator`` plugin.

Notes:
    - The ``write_feature`` fixture (see ``conftest.py``) writes feature
      files that mirror gherkinator's ``GenerateGherkin`` renderer, so
      these tests encode the plugin's contract with gherkinator's output
      format without requiring the gherkinator binary.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING

import pytest

from pytest_gherkinator import RISKS, STATUSES, TYPES

if TYPE_CHECKING:
    from _pytest.pytester import RunResult

TEST_MODULE = """\
from pytest_bdd import given, scenarios

scenarios("features/")


@given("a step")
def _a_step():
    pass
"""


def _collected(result: "RunResult") -> list[str]:
    """Return the collected test names in the order pytest reports them."""
    return [line.split("::")[-1] for line in result.stdout.lines if "::" in line]


def test_all_schema_marks_registered(pytester: pytest.Pytester) -> None:
    """Every gherkinator schema value is registered as a pytest mark."""
    result = pytester.runpytest("--markers")

    stdout = result.stdout.str()
    for name in (*RISKS, *STATUSES, *TYPES):
        assert f"@pytest.mark.{name}:" in stdout


def test_execution_order_risk_then_type(
    pytester: pytest.Pytester, write_feature: Callable[..., None]
) -> None:
    """Scenarios run edge-to-stable and functional-to-performance."""
    combos = [
        (risk, type_)
        for risk in ("stable", "candidate", "beta", "edge")
        for type_ in ("performance", "security", "solution", "functional")
    ]
    for index, (risk, type_) in enumerate(combos):
        write_feature(
            f"Feature {index:02d}",
            [f"{risk} {type_}\nGiven a step"],
            type_=type_,
            risk=risk,
            status="implemented",
        )
    pytester.makepyfile(test_bdd=TEST_MODULE)

    result = pytester.runpytest("--collect-only", "-q")

    expected = [
        f"test_{risk}_{type_}"
        for risk in ("edge", "beta", "candidate", "stable")
        for type_ in ("functional", "solution", "security", "performance")
    ]
    assert _collected(result) == expected


def test_feature_tags_apply_to_every_scenario(
    pytester: pytest.Pytester, write_feature: Callable[..., None]
) -> None:
    """Feature-level tags classify every scenario in the feature file."""
    write_feature(
        "Multi",
        [
            "first scenario\nGiven a step",
            "second scenario\nGiven a step",
            "third scenario\nGiven a step",
        ],
        type_="reliability",
        risk="beta",
        status="implemented",
    )
    pytester.makepyfile(test_bdd=TEST_MODULE)

    result = pytester.runpytest("-m", "beta", "--collect-only", "-q")

    assert _collected(result) == [
        "test_first_scenario",
        "test_second_scenario",
        "test_third_scenario",
    ]


def test_planned_and_deprecated_scenarios_are_skipped(
    pytester: pytest.Pytester, write_feature: Callable[..., None]
) -> None:
    """Only implemented scenarios run; skip reasons name the plan status."""
    write_feature(
        "Planned",
        ["planned scenario\nGiven a step"],
        type_="functional",
        risk="edge",
        status="planned",
    )
    write_feature(
        "Deprecated",
        ["deprecated scenario\nGiven a step"],
        type_="functional",
        risk="edge",
        status="deprecated",
    )
    write_feature(
        "Implemented",
        ["implemented scenario\nGiven a step"],
        type_="functional",
        risk="edge",
        status="implemented",
    )
    pytester.makepyfile(test_bdd=TEST_MODULE)

    result = pytester.runpytest("-ra")

    result.assert_outcomes(passed=1, skipped=2)
    stdout = result.stdout.str()
    assert "gherkinator test plan status is 'planned'" in stdout
    assert "gherkinator test plan status is 'deprecated'" in stdout


def test_marks_support_m_filtering(
    pytester: pytest.Pytester, write_feature: Callable[..., None]
) -> None:
    """Classification marks are first-class citizens for ``-m`` filtering."""
    write_feature(
        "Edge",
        ["edge scenario\nGiven a step"],
        type_="functional",
        risk="edge",
        status="implemented",
    )
    write_feature(
        "Stable",
        ["stable scenario\nGiven a step"],
        type_="performance",
        risk="stable",
        status="implemented",
    )
    write_feature(
        "Planned",
        ["planned scenario\nGiven a step"],
        type_="solution",
        risk="beta",
        status="planned",
    )
    pytester.makepyfile(test_bdd=TEST_MODULE)

    result = pytester.runpytest("-m", "edge")
    result.assert_outcomes(passed=1)

    result = pytester.runpytest("-m", "implemented")
    result.assert_outcomes(passed=2)

    result = pytester.runpytest("-m", "edge and functional")
    result.assert_outcomes(passed=1)


def test_missing_status_tag_does_not_skip(
    pytester: pytest.Pytester, write_feature: Callable[..., None]
) -> None:
    """Scenarios without a status tag (hand-written features) are not skipped."""
    write_feature(
        "Handwritten",
        ["handwritten scenario\nGiven a step"],
        type_="functional",
        risk="edge",
    )
    pytester.makepyfile(test_bdd=TEST_MODULE)

    result = pytester.runpytest()

    result.assert_outcomes(passed=1)


def test_unclassified_items_run_last(
    pytester: pytest.Pytester, write_feature: Callable[..., None]
) -> None:
    """Items without classification marks run after all classified items."""
    write_feature("Aaa", ["untagged scenario\nGiven a step"])
    write_feature(
        "Zzz",
        ["classified scenario\nGiven a step"],
        type_="functional",
        risk="edge",
        status="implemented",
    )
    pytester.makepyfile(test_bdd=TEST_MODULE)
    pytester.makepyfile(test_plain="def test_plain_untagged():\n    assert True\n")

    result = pytester.runpytest("--collect-only", "-q")

    assert _collected(result) == [
        "test_classified_scenario",
        "test_untagged_scenario",
        "test_plain_untagged",
    ]


def test_conflicting_risk_marks_warn_and_run_unclassified(
    pytester: pytest.Pytester, write_feature: Callable[..., None]
) -> None:
    """Conflicting classification marks are reported, never guessed."""
    write_feature(
        "Ambiguous",
        ["conflicting scenario\nGiven a step"],
        type_="functional",
        risk="edge",
        status="implemented",
        scenario_tags={"conflicting scenario": ["beta"]},
    )
    pytester.makepyfile(test_bdd=TEST_MODULE)

    result = pytester.runpytest()

    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(["*conflicting gherkinator marks*"])


def test_custom_tags_do_not_affect_classification(
    pytester: pytest.Pytester, write_feature: Callable[..., None]
) -> None:
    """Custom plan tags are marks too but are ignored for classification."""
    write_feature(
        "Tagged",
        ["tagged scenario\nGiven a step"],
        type_="functional",
        risk="stable",
        status="implemented",
        tags=["multi-node"],
    )
    pytester.makepyfile(test_bdd=TEST_MODULE)

    result = pytester.runpytest("-m", "functional")

    result.assert_outcomes(passed=1)


def test_scenario_outline_rows_are_marked_and_skipped(
    pytester: pytest.Pytester, write_feature: Callable[..., None]
) -> None:
    """Every example row of a parametrized scenario inherits the skip."""
    write_feature(
        "Outline",
        ["fill <field>\nGiven a step\nWhen a step"],
        type_="functional",
        risk="edge",
        status="planned",
        examples=[["alpha"], ["beta"]],
    )
    pytester.makepyfile(test_bdd=TEST_MODULE)

    result = pytester.runpytest()

    result.assert_outcomes(skipped=2)


def test_marked_plain_tests_sorted_with_scenarios(
    pytester: pytest.Pytester, write_feature: Callable[..., None]
) -> None:
    """Manually marked plain tests are ordered exactly like BDD scenarios."""
    write_feature(
        "Bdd",
        ["bdd edge scenario\nGiven a step"],
        type_="functional",
        risk="edge",
        status="implemented",
    )
    pytester.makepyfile(test_bdd=TEST_MODULE)
    pytester.makepyfile(
        test_plain=(
            "import pytest\n"
            "\n"
            "\n"
            "@pytest.mark.edge\n"
            "@pytest.mark.functional\n"
            "def test_marked_plain():\n"
            "    assert True\n"
            "\n"
            "\n"
            "def test_unmarked_plain():\n"
            "    assert True\n"
        )
    )

    result = pytester.runpytest("--collect-only", "-q")

    assert _collected(result) == [
        "test_bdd_edge_scenario",
        "test_marked_plain",
        "test_unmarked_plain",
    ]
