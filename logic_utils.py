"""Game logic helpers for the Glitchy Guesser number-guessing game."""

from pathlib import Path

DEFAULT_HIGH_SCORE_PATH = Path(__file__).with_name("high_score.txt")
MAX_SCORE = 100
# FIX: Refactored and corrected with AI assistance, then verified by pytest.
DIFFICULTY_RANGES = {
    "Easy": (1, 20),
    "Normal": (1, 50),
    "Hard": (1, 100),
}


def load_high_score(path: str | Path = DEFAULT_HIGH_SCORE_PATH) -> int:
    """Return the saved high score from ``path``.

    Negative saved values are clamped to zero. A missing, unreadable, or
    non-integer file also returns zero.
    """
    try:
        return max(0, int(Path(path).read_text(encoding="utf-8").strip()))
    except (FileNotFoundError, OSError, ValueError):
        return 0


def save_high_score(
    score: int,
    path: str | Path = DEFAULT_HIGH_SCORE_PATH,
) -> int:
    """Save ``score`` if it beats the stored high score, then return the best.

    The file is written only when ``score`` is strictly greater than the value
    returned by ``load_high_score``; otherwise it is left untouched.
    """
    saved_score = load_high_score(path)
    if score > saved_score:
        Path(path).write_text(str(score), encoding="utf-8")
        return score
    return saved_score


def get_range_for_difficulty(difficulty: str) -> tuple[int, int]:
    """Return the inclusive ``(low, high)`` range for a difficulty.

    Unknown difficulty names fall back to ``(1, 100)``.
    """
    return DIFFICULTY_RANGES.get(difficulty, (1, 100))


def parse_guess(
    raw: str | None,
    low: int | None = None,
    high: int | None = None,
) -> tuple[bool, int | None, str | None]:
    """Parse raw input into a whole-number guess.

    Bounds are checked only when both ``low`` and ``high`` are given, and they
    are inclusive.

    Returns ``(ok, value, error)``: ``(True, value, None)`` for a valid
    guess, or ``(False, None, message)`` for empty, non-integer, or
    out-of-range input.
    """
    if raw in (None, ""):
        return False, None, "Enter a guess."

    try:
        # FIX: AI changed parsing; I verified decimals are rejected by pytest.
        value = int(raw)
    except (TypeError, ValueError):
        return False, None, "Enter a whole number."

    # FIX: AI added bounds; I verified each difficulty and its edge values.
    if low is not None and high is not None and not (low <= value <= high):
        return False, None, f"Guess must be between {low} and {high}."

    return True, value, None


def check_guess(guess: int, secret: int) -> tuple[str, str]:
    """Return the outcome label and player-facing hint for a guess.

    The outcome label is ``"Win"``, ``"Too High"``, or ``"Too Low"``.
    """
    if guess == secret:
        return "Win", "🎉 Correct!"
    # FIX: Corrected the hint direction with AI assistance and focused tests.
    if guess > secret:
        return "Too High", "📉 Go LOWER!"
    return "Too Low", "📈 Go HIGHER!"


def build_guess_summary(
    history: list[int],
    secret: int,
) -> list[dict[str, int | str]]:
    """Build attempt, guess, and result rows for the current game."""
    return [
        {
            "Attempt": attempt,
            "Guess": guess,
            "Result": check_guess(guess, secret)[0],
        }
        for attempt, guess in enumerate(history, start=1)
    ]


def update_score(
    current_score: int,
    outcome: str,
    attempts_used: int,
    attempt_limit: int,
) -> int:
    """Return a 0-100 score scaled to the difficulty's attempt allowance.

    The score begins at 100. Each wrong guess removes an equal fraction of the
    available points, rounded cumulatively so the score remains a whole number.
    A win keeps the points remaining after earlier wrong guesses, while using
    every attempt without winning reduces the score to zero. Unknown outcomes
    leave ``current_score`` unchanged.
    """
    if attempt_limit <= 0:
        raise ValueError("attempt_limit must be greater than zero")
    if attempts_used < 0:
        raise ValueError("attempts_used cannot be negative")

    if outcome == "Win":
        wrong_guesses = max(attempts_used - 1, 0)
    elif outcome in ("Too High", "Too Low"):
        wrong_guesses = attempts_used
    else:
        return current_score

    points_lost = MAX_SCORE * wrong_guesses // attempt_limit
    return max(0, MAX_SCORE - points_lost)
