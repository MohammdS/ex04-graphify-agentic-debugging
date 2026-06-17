# Hot Nodes

Graphify found 19 nodes and 31 edges across four communities. The most useful
debugging entry points were:

| Rank | Node | Why it mattered |
| --- | --- | --- |
| 1 | `read_file()` | Highest-degree data-loading hub |
| 2 | `_amounts_by_status()` | Shared calculation helper for loan metrics |
| 3 | `calculate_unpaid_loans()` | Public calculation function |
| 4 | `calculate_paid_loans()` | Public calculation function |
| 5 | `average_paid_loans()` | Public calculation function |
| 6 | `foo()` | Target bug node for mutable default argument defect |

For the selected bug, `foo()` was the relevant hot node even though it was not
the highest-degree node. Its direct neighborhood pointed to:

- `src/buggy_python/foobar.py:L4`
- Import exposure through `src/buggy_python/__init__.py`
- A docstring rationale describing the default-argument behavior

See [[bug-investigation]] and [[agent-workflow]].

