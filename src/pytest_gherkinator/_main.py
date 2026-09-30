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

"""``pytest-gherkinator`` plugin module.

The plugin relies on the classification tags that ``gherkinator`` renders
on the feature-level tag line of every generated ``*.feature`` file
(``@<type> @<risk> @<status> @<custom tags>``). ``pytest-bdd`` converts
Gherkin tags into ``pytest`` marks, so every scenario collected from a
gherkinator-generated feature file carries one mark per classification
field. Based on those marks, the plugin:

1. Sorts scenario execution by risk level (``edge`` -> ``beta`` ->
   ``candidate`` -> ``stable``), then by test type within each risk level
   (``functional`` -> ``solution`` -> ``reliability`` -> ``security`` ->
   ``performance``).
2. Skips scenarios whose plan status is ``planned`` or ``deprecated``.

Classification is purely mark-driven, so plain ``pytest`` tests manually
marked with gherkinator marks are ordered exactly like BDD scenarios.
Items without classification marks run after all classified items and
keep their original relative order.

Notes:
    - The plugin never reads gherkinator YAML test plans; the mark set in
      :mod:`pytest_gherkinator._constants` is its entire contract with
      gherkinator.
    - :func:`pytest_collection_modifyitems` must remain a plain hook
      implementation. Making it ``tryfirst``, ``trylast``, or a hook
      wrapper changes when it runs relative to the builtin mark plugin's
      ``-m`` deselection and can make the skip marks it adds invisible to
      mark-based filtering.
"""

__all__ = ["GherkinatorWarning", "pytest_collection_modifyitems", "pytest_configure"]

import warnings

import pytest

from ._constants import (
    MARKS,
    RISK_ORDER,
    RISKS,
    SKIP_STATUSES,
    STATUSES,
    TYPE_ORDER,
    TYPES,
)


class GherkinatorWarning(pytest.PytestWarning):
    """Warning raised for test items with conflicting gherkinator marks."""


def pytest_configure(config: pytest.Config) -> None:
    """Register the gherkinator classification marks.

    Args:
        config: The ``pytest`` config object for this test run.
    """
    for name, help_text in MARKS.items():
        config.addinivalue_line("markers", f"{name}: {help_text}")


def pytest_collection_modifyitems(
    session: pytest.Session, config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Sort and skip the collected items according to their gherkinator marks.

    Args:
        session: The ``pytest`` session.
        config: 
            The ``pytest`` config object for this test run.
            items: The collected test items; sorted in place.

    Notes:
        - The sort is stable: items sharing the same classification keep
          their original relative order, which preserves scenarios that
          build state on each other within a single feature file.
        - Unclassified items (items without gherkinator marks) run after
          all classified items, in their original relative order.
    """
    conflicts: list[str] = []
    decorated: list[tuple[int, pytest.Item, str | None, str | None]] = []

    for position, item in enumerate(items):
        risk = _single_mark(item, RISKS, conflicts)
        type_ = _single_mark(item, TYPES, conflicts)
        status = _single_mark(item, STATUSES, conflicts)

        if status in SKIP_STATUSES:
            item.add_marker(pytest.mark.skip(reason=f"gherkinator test plan status is '{status}'"))

        decorated.append((position, item, risk, type_))

    if conflicts:
        details = "\n".join(f"  - {conflict}" for conflict in conflicts)
        warnings.warn(
            "pytest-gherkinator found test items with conflicting gherkinator "
            f"marks; affected items will run unclassified:\n{details}",
            GherkinatorWarning,
            stacklevel=1,
        )

    decorated.sort(
        key=lambda entry: (
            _sort_position(RISK_ORDER, entry[2]),
            _sort_position(TYPE_ORDER, entry[3]),
            entry[0],
        )
    )
    items[:] = [entry[1] for entry in decorated]


def _single_mark(item: pytest.Item, names: tuple[str, ...], conflicts: list[str]) -> str | None:
    """Get the single mark from ``names`` present on ``item``.

    Args:
        item: The collected test item to inspect.
        names: The candidate mark names of one classification field.
        conflicts: Conflict record collector; appended to when ``item``
            carries more than one of the candidate marks.

    Returns:
        The single mark name present on the item, or ``None`` when the
        item carries none of the marks or more than one of them.
        Ambiguous items are never classified by guessing.
    """
    found = {marker.name for marker in item.iter_markers() if marker.name in names}
    if not found:
        return None
    if len(found) > 1:
        conflicts.append(f"{item.nodeid}: {sorted(found)}")
        return None

    return found.pop()


def _sort_position(order: dict[str, int], value: str | None) -> int:
    """Return the execution position for ``value`` under ``order``.

    Args:
        order: One of the classification execution orders.
        value: The classified mark name, or ``None`` when the item is not
            classified for this field.

    Returns:
        The execution position for ``value``. Unclassified values sort
        after all classified values.
    """
    if value is None:
        return len(order)

    return order.get(value, len(order))
