# EX04 Vault Index

This vault documents the reverse-engineering and bug-diagnosis workflow for the
selected repository: `andela/buggy-python`.

## Navigation

- [[hot]] - Graphify hot nodes and graph entry points
- [[architecture]] - System block diagram and module responsibilities
- [[oop]] - Class/module relationship diagram
- [[bug-investigation]] - Root cause analysis for the selected bug
- [[agent-workflow]] - LangGraph debugging workflow
- [[token-efficiency]] - Naive vs graph-guided context comparison
- [[before-after]] - Broken behavior and suggested patch

## Key Evidence

- Graph artifact: `data/graph.json`
- Graph report: `reports/GRAPH_REPORT.md`
- Bug report: `reports/BUG_REPORT.md`
- Token report: `reports/MEASURED_TOKEN_COMPARISON.md`
- Architecture report: `reports/ARCHITECTURE_REPORT.md`
- Verification command: `python -m pytest -q`
