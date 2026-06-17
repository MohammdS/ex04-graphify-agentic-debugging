# Architecture

The extracted project is a small Python package with three public behavior
areas: list/default-argument behavior, loan-file calculations, and lambda
generation.

```mermaid
flowchart LR
  OriginalRepo["andela/buggy-python"] --> ExtractedPackage["src/buggy_python"]
  ExtractedPackage --> PublicAPI["__init__.py public API"]
  PublicAPI --> Foo["foobar.foo"]
  PublicAPI --> LoanIO["io loan calculations"]
  PublicAPI --> LambdaFactory["loop.lambda_array"]
  LoanIO --> DataFile["loans.json"]
  Tests["pytest regression tests"] --> PublicAPI
  Graphify["Graphify AST extraction"] --> GraphJson["data/graph.json"]
  ExtractedPackage --> Graphify
  GraphJson --> LangGraph["agent/workflow.py"]
  LangGraph --> Tests
  GraphJson --> Obsidian["obsidian vault and reports"]
```

The architecture is intentionally flat. That makes it a good assignment target:
the graph still reveals public API exposure and impact radius without requiring
large-project setup.

