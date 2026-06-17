# Graph Report - .  (2026-06-17)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 19 nodes · 31 edges · 4 communities
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]

## God Nodes (most connected - your core abstractions)
1. `read_file()` - 5 edges
2. `_amounts_by_status()` - 5 edges
3. `calculate_unpaid_loans()` - 4 edges
4. `calculate_paid_loans()` - 4 edges
5. `average_paid_loans()` - 4 edges
6. `foo()` - 3 edges
7. `lambda_array()` - 3 edges
8. `Default argument example from the selected buggy repository.` - 1 edges
9. `Return a list containing a single ``"baz"`` item.      The original implementati` - 1 edges
10. `Loan file loading and aggregate calculations.` - 1 edges

## Surprising Connections (you probably didn't know these)
- `read_file()` --references--> `Any`  [EXTRACTED]
  src/buggy_python/io.py → src/buggy_python/io.py  _Bridges community 3 → community 0_

## Import Cycles
- None detected.

## Communities (4 total, 0 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.57
Nodes (6): Any, _amounts_by_status(), average_paid_loans(), calculate_paid_loans(), calculate_unpaid_loans(), Loan file loading and aggregate calculations.

### Community 1 - "Community 1"
Cohesion: 0.50
Nodes (3): foo(), Default argument example from the selected buggy repository., Return a list containing a single ``"baz"`` item.      The original implementati

### Community 2 - "Community 2"
Cohesion: 0.50
Nodes (3): lambda_array(), Lambda factory from the selected buggy repository., Return ten lambdas that add their index to a supplied value.

### Community 3 - "Community 3"
Cohesion: 0.67
Nodes (3): Read loan data from a JSON file.      When no path is provided, the bundled fixt, read_file(), Path

## Knowledge Gaps
- **1 isolated node(s):** `Path`
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `read_file()` connect `Community 3` to `Community 0`, `Community 1`?**
  _High betweenness centrality (0.233) - this node is a cross-community bridge._
- **Why does `lambda_array()` connect `Community 2` to `Community 1`?**
  _High betweenness centrality (0.111) - this node is a cross-community bridge._
- **What connects `Default argument example from the selected buggy repository.`, `Return a list containing a single ``"baz"`` item.      The original implementati`, `Path` to the rest of the system?**
  _7 weakly-connected nodes found - possible documentation gaps or missing edges._