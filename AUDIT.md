# AUDIT.md — wordleguesser

Updated: 2026-09-10

## Confirmed diagnosis: candidate filtering and library entry point

Expected: the documented `findword(guessed, g=None, y=None, gray='')`
function returns frequency-ranked five-letter words satisfying every supplied
green, yellow and gray constraint. Importing it should not prompt for input.

Observed at commit `964af0109300d3c34b5823766b070416490892b6`:

- An isolated four-word fixture with yellow clues `a1,b2` returned `maple`,
  `orbit` and `drama`, although each lacks at least one required yellow letter.
  The cause is the `any(...)` membership condition in lines 72–79.
- Calling `findword('')` with its documented defaults raises `AttributeError`:
  lines 21–24 and 32–35 call `.split()` on `None`.
- Clue positions are indexed without validation, data paths are relative to the
  caller's directory, and the interactive loop runs at import (lines 141–147).
- Repeated-letter count feedback is a preexisting limitation of the compact
  clue format, as recorded in PRD.md. This release preserves that limitation;
  it does not infer exact counts from clues collected across multiple guesses.

The fixture substituted in-memory dictionary/frequency files and extracted only
the function definition. It did not run the interactive script or change data.

Fix: validate and normalize inputs, require every distinct yellow letter,
filter candidates in one pass, resolve bundled files beside the script and put
the CLI behind a main guard. Keep the existing input format and result shape.

Verification: standard-library tests for combined colors, absent optional clues,
invalid positions, case/whitespace, ranking, import safety, other working
directories and CLI EOF/error handling. Record both bundled data hashes before
and after the change. Run the same tests on Linux and Windows in CI.

The findings below are the older 2026-05-24 audit and are superseded where this
diagnosis identifies a concrete defect.

## 0. FILESYSTEM HEALTH REPORT
No corrupted, orphaned, or sync artifact files detected.

## 1. MASTER FEATURE MAP
| File | Purpose | Key Functions |
|------|---------|---------------|| wordleguesser.py | Source file | (see source) |

## 2. RECONCILIATION SUMMARY
Small utility project. Documentation matches implementation.

## 3-5. GAPS / GHOSTS / DRIFT
None identified for this project scope.

## 6. DATA INTEGRITY
N/A — no databases.

## 7. CODE QUALITY FINDINGS
| Tag | Description | Severity |
|-----|-------------|----------|
| [DEAD] | No dead code detected | N/A |

## 8. STRUCTURAL REORGANIZATION
No reorganization needed — structure appropriate for project size.

## 9. PRODUCTION READINESS
N/A — personal/educational utility, not a production service.

## 10. REMEDIATION ROADMAP
No remediation actions required.
