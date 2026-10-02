# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agent Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

I asked Claude Code to help complete the stretch work after the required repairs
while keeping the tests focused and non-redundant. Claude Code recommended a
file-backed High Score tracker as the Agent Mode feature.

**Files modified:** `app.py`, `logic_utils.py`, `tests/test_game_logic.py`, `.gitignore`, `README.md`, and `ai_interactions.md`.

**What did the agent do?**

Claude Code added `load_high_score` and `save_high_score` to `logic_utils.py`, displayed the saved score in the Streamlit sidebar, and updated it after a win. It added `high_score.txt` to `.gitignore` so runtime data is not committed. It also added one focused test using pytest's temporary directory and ran the full suite successfully.

**What did you have to verify or fix manually?**

I required the agent to avoid a matrix of repetitive test inputs and keep one test for the complete persistence workflow. During live verification, I checked a winning score of 65, confirmed it survived New Game, and opened a fresh app session to confirm it loaded from the file. The live check also exposed stale counters and a deprecated table-width option, so Claude Code synchronized the displays and replaced the deprecated option before rerunning lint and pytest.

---

## Test Generation (SF7)

> Document how you used AI to help generate or improve tests.

I worked with Claude Code to improve the edge-case tests for Challenge 1. I
checked its suggestions against the assignment and asked it to avoid duplicate
tests. We organized the inputs in `test_invalid_input_classes_are_rejected`
using `pytest.mark.parametrize`, which runs each input as a separate test case
while keeping one shared assertion.

**Prompt used:**

```
Add concise pytest coverage for negative, decimal, and extremely large inputs to
parse_guess, avoid duplicating existing tests, and run the complete test suite.
```

| Edge Case | Test | Did It Pass? | Rationale |
|-----------|------|--------------|-----------|
| Empty input | `parse_guess("", 1, 50)` returns `Enter a guess.` | Yes | A blank submission should show a clear error without becoming an attempt. |
| Non-numeric string | `parse_guess("abc", 1, 50)` returns `Enter a whole number.` | Yes | Text input reproduced a logged bug in which invalid data consumed an attempt and entered History. |
| Decimal number | `parse_guess("3.5", 1, 50)` returns `Enter a whole number.` | Yes | The starter parser truncated decimals, which silently changed the player's guess. |
| Negative number | `parse_guess("-5", 1, 50)` returns the range error. | Yes | A negative integer is numeric but outside every game range. |
| Extremely large number | `parse_guess(str(10**100), 1, 50)` returns the range error. | Yes | A very large integer verifies that range validation rejects unusual numeric input without crashing. |

---

## Linting & Style (SF9)

> Document your use of AI for linting or code style improvements.

I ran the lint checks in the terminal and used the following prompt for the style review.

**Prompt used:**

```
Review `logic_utils.py` and `app.py` for PEP 8 style issues: naming, line length, unused imports, spacing, and missing docstrings. Suggest fixes that don't change behavior, and explain each change in one line. After applying them, run `pytest` to confirm nothing broke.
```

**Linting output before:**

```
$ python -m flake8 logic_utils.py app.py
app.py:81:80: E501 line too long (84 > 79 characters)
app.py:182:80: E501 line too long (81 > 79 characters)
app.py:183:80: E501 line too long (80 > 79 characters)
logic_utils.py:59:80: E501 line too long (80 > 79 characters)
logic_utils.py:112:80: E501 line too long (85 > 79 characters)

$ python -m pydocstyle logic_utils.py app.py
logic_utils.py:1 at module level:
        D100: Missing docstring in public module
app.py:1 at module level:
        D100: Missing docstring in public module
```

**Changes applied:**

- Added a module docstring to `logic_utils.py` and `app.py` (D100).
- Re-wrapped the `parse_guess` docstring's return description to stay under 79 characters.
- Split the one-line conditional return in `update_score` into an `if` with two `return`s.
- No unused imports, naming issues, or spacing issues were found, and no game logic changed.
- I did not keep the line wraps for the three long lines in `app.py`. They satisfied flake8's 79-character limit but failed `ruff format --check`, and this project uses Ruff with its 88-character limit.

**Linting output after:**

```
$ ruff check --select E,W,F,I app.py logic_utils.py tests/test_game_logic.py
All checks passed!
$ ruff format --check app.py logic_utils.py tests/test_game_logic.py
3 files already formatted
$ python -m pydocstyle logic_utils.py app.py
```

**Test output after:**

```
$ venv/bin/python -m pytest -q
.....................................                                    [100%]
37 passed in 1.94s
```

---

## Model Comparison (SF11)

> Compare two AI models on the same task.

**Task given to both models:**

> The Normal and Hard ranges are swapped in `get_range_for_difficulty`. Propose the smallest Pythonic fix, explain why it works, and provide one focused pytest test. Do not change unrelated behavior.

| | Model A | Model B |
|-|---------|---------|
| **Model name** | Claude Code | Codex |
| **Response summary** | Swapped only the Normal and Hard return values (Normal → 1–50, Hard → 1–100), leaving Easy and the 1–100 fallback untouched. Provided one parameterized pytest test covering Easy, Normal, Hard, and an unknown difficulty. | Swapped only the Normal and Hard return values (Normal → 1–50, Hard → 1–100), preserving Easy and the existing unknown-difficulty fallback. Provided one focused parameterized pytest test covering the two corrected branches. |
| **More Pythonic?** | Same minimal fix as Model B; the test also checks the unknown-difficulty fallback, so it guards against changing unrelated behavior. | Same minimal fix as Model A; the focused test avoids unrelated cases, though it does not separately guard the fallback. |
| **Clearer explanation?** | Named the symptom (Hard was easier than Normal), the fix, and which test cases fail before the fix and which only confirm unchanged behavior. | Concisely identified the reversed upper bounds and explained that changing only those two values preserves Easy and fallback behavior. |

**Which did you prefer and why?**

I preferred Claude Code’s response because it made the same minimal fix as Codex while providing more complete regression coverage. Its single parameterized test checks Easy, Normal, Hard, and the unknown-difficulty fallback, confirming that the swapped ranges were corrected without changing unrelated behavior.
