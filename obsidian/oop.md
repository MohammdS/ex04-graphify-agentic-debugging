# OOP and Module Relationships

The selected codebase is procedural and does not define Python classes. The
diagram below documents the public module relationships and the JSON record
shape used by the calculation functions.

```mermaid
classDiagram
  class BuggyPythonPackage {
    <<package>>
    +foo()
    +lambda_array()
    +read_file()
    +calculate_unpaid_loans()
    +calculate_paid_loans()
    +average_paid_loans()
  }
  class FoobarModule {
    <<module>>
    +foo(bar=[]) list
  }
  class IoModule {
    <<module>>
    +read_file(path=None) dict
    +_amounts_by_status(data, status) list
    +calculate_unpaid_loans(data) int
    +calculate_paid_loans(data) float
    +average_paid_loans(data) float
  }
  class LoopModule {
    <<module>>
    +lambda_array() list
  }
  class LoanRecord {
    <<data shape>>
    +amount float
    +status str
  }
  BuggyPythonPackage --> FoobarModule : re-exports
  BuggyPythonPackage --> IoModule : re-exports
  BuggyPythonPackage --> LoopModule : re-exports
  IoModule --> LoanRecord : reads JSON records
```

This is still an OOP/class relationship artifact because it records the absence
of classes and the effective public interface boundaries.
