# pytest-gherkinator

![GitHub License](https://img.shields.io/github/license/canonical/pytest-gherkinator)
[![Matrix](https://img.shields.io/matrix/ubuntu-hpc%3Amatrix.org?logo=matrix&label=ubuntu-hpc)](https://matrix.to/#/#hpc:ubuntu.com)

A `pytest` plugin that controls the execution of `pytest-bdd` scenarios
according to the classification tags that
[`gherkinator`](https://github.com/canonical/gherkinator) renders into
generated `*.feature` files.

`gherkinator` transpiles centralized YAML test plans into Gherkin feature
files, rendering each plan's classification as a feature-level tag line:

```gherkin
@functional @stable @implemented @multi-node
Feature: GPU job submission
  As a cluster user I want to be able to successfully submit jobs
  to the partitions that I have access to.

  Scenario: Submit a job
    Given my user '<username>' exists
```

`pytest-bdd` turns Gherkin tags into `pytest` marks, and `pytest-gherkinator`
uses those marks to order, mark, and skip the collected scenarios. The plugin
is deliberately thin: its only contract with `gherkinator` is the set of
classification marks below, and it never reads gherkinator YAML test plans.

## ✨ Getting Started

### Installation

#### Option 1: Install from PyPI

```shell
$ python3 -m pip install pytest-gherkinator
```

#### Option 2: Install from source

```shell
$ pip install .
```

### Usage

#### What the plugin does

1. **Sorts execution order** by risk level, then by test type within each
   risk level:

   | Dimension | Execution order |
   | --------- | --------------- |
   | Risk      | `edge` → `beta` → `candidate` → `stable` |
   | Type      | `functional` → `solution` → `reliability` → `security` → `performance` |

2. **Skips** scenarios whose plan status is `planned` or `deprecated`, so
   only `implemented` scenarios run.
3. **Registers all twelve classification values as `pytest` marks**, so
   tag-derived marks are first-class citizens:

   ```shell
   pytest -m edge                     # only edge-risk scenarios
   pytest -m implemented              # exclude planned/deprecated
   pytest -m "edge and functional"    # combine classifications
   ```

Items sharing the same classification keep their original relative order, so
scenarios that build state on each other within one feature file stay in
definition order.

#### Classification rules

| Situation | Behavior |
| --------- | -------- |
| Feature tagged `@planned` or `@deprecated` | Scenario is skipped |
| Feature tagged `@implemented`, or no status tag | Scenario runs |
| No risk tag | Scenario runs after all risk-classified scenarios |
| No type tag | Scenario runs last within its risk level |
| No classification tags at all | Scenario runs after all classified items, in original order |
| Conflicting tags (e.g. feature `@edge` plus scenario `@beta`) | Scenario runs unclassified with a warning; the plugin never guesses |

Because classification is purely mark-driven, plain `pytest` tests marked
with `@pytest.mark.edge`, `@pytest.mark.functional`, and friends are ordered
exactly like BDD scenarios.

#### Run-time requirements

- Python 3.12+
- [`pytest-bdd`](https://pypi.org/project/pytest-bdd/) 8.x

#### Limitations

- `pytest-xdist` distributes items to workers independently of execution
  order, so the ordering applies to single-process runs only.
- Reordering plugins such as `pytest-randomly` can undo the plugin's
  ordering.
- Custom plan tags (for example `@multi-node`) become marks too, but
  `pytest-gherkinator` does not register them. Register custom marks in your
  own configuration to silence `PytestUnknownMarkWarning`.

## 🛠️ Development

The project uses [just](https://github.com/casey/just) and
[uv](https://github.com/astral-sh/uv) for development, which provides some
useful commands that will help you while hacking on pytest-gherkinator:

```shell
just fmt          # Apply formatting standards to code
just lint         # Check code against coding style standards
just typecheck    # Run static type checks
just unit         # Run unit tests
```

If you're interested in contributing your work to pytest-gherkinator, take a
look at our [contributing guidelines](./CONTRIBUTING.md) for further details.

## 🤝 Project and community

pytest-gherkinator is part of the tooling built around the
[`gherkinator`](https://github.com/canonical/gherkinator) test plan format,
is a project of the [Ubuntu High-Performance Computing community](https://ubuntu.com/community/governance/teams/hpc).
Interested in contributing bug fixes, new features, documentation, or
feedback? You’ve come to the right place 🤩

Here’s some links to help you get started with joining the community:

* [Ubuntu Code of Conduct](https://ubuntu.com/community/ethos/code-of-conduct)
* [Join the conversation on Matrix](https://matrix.to/#/#hpc:ubuntu.com)
* [Get the latest news on Discourse](https://discourse.ubuntu.com/c/hpc/151)

Check out the [`gherkinator`](https://github.com/canonical/gherkinator) repository to learn 
more about the format this plugin is built on.

## 📋 License

pytest-gherkinator is free software, distributed under the Apache License,
v2.0. See the [LICENSE](./LICENSE) file for further details.
