# Pipeline trace - vol.xlsx

## 0 readiness

**Tool.** `determinism.find_volatile + determinism.check`

**Returned.** `{"volatile": "1 volatile cell(s) using RAND", "determinism": "not reached"}`

**Decision.** REFUSE

**Why.** A proof is a comparison of two evaluations. This workbook does not evaluate to the same numbers twice, so no proof drawn from it would reproduce. Refusing is the honest answer; auditing anyway would produce findings that look identical to real ones.
