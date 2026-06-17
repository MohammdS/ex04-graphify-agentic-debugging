# Graph Report

## Tooling

Graph extraction used Graphify (`graphifyy` package, CLI command `python -m
graphify`).

Commands:

```powershell
python -m graphify extract src --out . --no-cluster
python -m graphify cluster-only . --graph graphify-out\graph.json --no-label --no-viz
```

## Summary

- Nodes: 19
- Edges: 31
- Communities: 4
- Import cycles: none detected
- LLM semantic extraction tokens: 0 input, 0 output
- Canonical graph artifact: `data/graph.json`

## Highest-Degree Nodes

| Node | Degree | Role |
| --- | ---: | --- |
| `read_file()` | 5 | Loan JSON entry point |
| `_amounts_by_status()` | 5 | Shared calculation helper |
| `calculate_unpaid_loans()` | 4 | Public aggregate |
| `calculate_paid_loans()` | 4 | Public aggregate |
| `average_paid_loans()` | 4 | Public aggregate |
| `foo()` | 3 | Selected bug node |
| `lambda_array()` | 3 | Lambda factory |

## Bug-Relevant Subgraph

`foo()` has three direct graph edges:

- `foobar.py --contains--> foo()`
- `__init__.py --imports--> foo()`
- `rationale node --rationale_for--> foo()`

This gave the agent a precise inspection path: open `src/buggy_python/foobar.py`
and confirm the package impact through `src/buggy_python/__init__.py`.

