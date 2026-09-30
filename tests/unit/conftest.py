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

import re
from collections.abc import Callable

import pytest

pytest_plugins = ["pytester"]


@pytest.fixture
def write_feature(pytester: pytest.Pytester) -> Callable[..., None]:
    """Generate a helper function that writes gherkinator-format ``*.feature`` files.

    Notes:
        - The helper mirrors gherkinator's ``GenerateGherkin`` renderer
          (canonical/gherkinator @ ``main``, ``internal/common/transpile.go``;
          commits ``fff4439`` and ``f989cc6``) so the fixtures match real
          generated output byte-for-byte.
        - Each scenario block's first line is the scenario title; the
          remaining lines are Gherkin steps, mirroring the scenario strings
          of the gherkinator YAML schema.
    """

    def _write(
        feature: str,
        scenarios: list[str],
        *,
        type_: str | None = None,
        risk: str | None = None,
        status: str | None = None,
        tags: list[str] | None = None,
        scenario_tags: dict[str, list[str]] | None = None,
        examples: list[list[str]] | None = None,
    ) -> None:
        """Write one feature file into the pytester sandbox.

        Args:
            feature:
                The feature name; also derives the file name the same
                way gherkinator does (lower-cased, spaces replaced with
                underscores).
            scenarios: Scenario blocks (title line plus step lines).
            type_: The ``type`` classification tag.
            risk: The ``risk`` classification tag.
            status:
                The ``status`` classification tag; omitted to simulate
                hand-written feature files.
            tags: Custom tags rendered after the classification tags.
            scenario_tags:
                Scenario-level tags keyed by scenario title, for
                example to simulate conflicting classification tags.
            examples:
                Example rows; their presence turns scenarios into
                scenario outlines with a trailing ``Examples`` table.
        """
        tag_names = [name for name in (type_, risk, status) if name is not None]
        tag_names.extend(tags or [])

        lines: list[str] = []
        if tag_names:
            lines.append("@" + " @".join(tag_names))
        lines.append(f"Feature: {feature}")
        lines.append("")

        keyword = "Scenario Outline" if examples else "Scenario"
        for block in scenarios:
            title, *steps = block.splitlines()
            title = title.strip()
            for scenario_tag in (scenario_tags or {}).get(title, []):
                lines.append(f"  @{scenario_tag}")
            lines.append(f"  {keyword}: {title}")
            for step in steps:
                lines.append(f"    {step.strip()}")

        if examples:
            params: list[str] = []
            for block in scenarios:
                for token in re.findall(r"<([^>]+)>", block):
                    if token not in params:
                        params.append(token)
            lines.append("")
            lines.append("  Examples:")
            lines.append("    | " + " | ".join(params) + " |")
            for row in examples:
                lines.append("    | " + " | ".join(row) + " |")

        path = pytester.path / "features" / f"{feature.lower().replace(' ', '_')}.feature"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return _write
