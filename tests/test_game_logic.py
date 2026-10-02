"""Tests for the game logic in logic_utils.py and the Streamlit app in app.py."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from logic_utils import (
    build_guess_summary,
    check_guess,
    get_range_for_difficulty,
    load_high_score,
    parse_guess,
    save_high_score,
    update_score,
)

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
RANGES = [("Easy", 1, 20), ("Normal", 1, 50), ("Hard", 1, 100)]


def load_app():
    """Run app.py once in Streamlit's test harness and return the running app."""
    return AppTest.from_file(str(APP_PATH)).run()


def assert_game_reset(at):
    """Check that attempts, score, status and history match a new game."""
    assert at.session_state.attempts == 0
    assert at.session_state.score == 100
    assert at.session_state.status == "playing"
    assert at.session_state.history == []


# ---------------------------------------------------------------------------
# logic_utils.py: high score
# ---------------------------------------------------------------------------


def test_high_score_file_keeps_best_score(tmp_path):
    """Missing, malformed, and negative scores load safely; the best score wins."""
    score_file = tmp_path / "high_score.txt"
    assert load_high_score(score_file) == 0
    assert save_high_score(40, score_file) == 40
    assert save_high_score(25, score_file) == 40
    assert load_high_score(score_file) == 40

    score_file.write_text("not a score", encoding="utf-8")
    assert load_high_score(score_file) == 0
    score_file.write_text("-10", encoding="utf-8")
    assert load_high_score(score_file) == 0
    assert save_high_score(10, score_file) == 10
    assert load_high_score(score_file) == 10


# ---------------------------------------------------------------------------
# logic_utils.py: get_range_for_difficulty
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("difficulty, low, high", RANGES)
def test_range_for_difficulty(difficulty, low, high):
    """Each difficulty returns its own range."""
    assert get_range_for_difficulty(difficulty) == (low, high)


# ---------------------------------------------------------------------------
# logic_utils.py: parse_guess
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("raw, expected", [("1", 1), (" 50 ", 50)])
def test_guess_inside_range_is_accepted(raw, expected):
    """Guesses inside 1-50, including both edges, are accepted and turned into ints."""
    assert parse_guess(raw, 1, 50) == (True, expected, None)


RANGE_ERROR = "Guess must be between 1 and 50."


@pytest.mark.parametrize(
    ("raw", "expected_error"),
    [
        ("", "Enter a guess."),
        ("abc", "Enter a whole number."),
        ("3.5", "Enter a whole number."),
        ("-5", RANGE_ERROR),
        (str(10**100), RANGE_ERROR),
    ],
    ids=[
        "empty",
        "non-numeric",
        "decimal",
        "negative",
        "huge-positive",
    ],
)
def test_invalid_input_classes_are_rejected(raw, expected_error):
    """Empty, non-numeric, non-integer, and extreme inputs fail safely."""
    assert parse_guess(raw, 1, 50) == (False, None, expected_error)


# ---------------------------------------------------------------------------
# logic_utils.py: check_guess
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "guess, secret, expected",
    [(50, 50, "Win"), (60, 50, "Too High"), (40, 50, "Too Low")],
)
def test_guess_outcome(guess, secret, expected):
    """A correct, high or low guess returns Win, Too High or Too Low."""
    # FIX verification: compare the returned outcome instead of the whole tuple.
    assert check_guess(guess, secret)[0] == expected


@pytest.mark.parametrize(
    "guess, secret, expected, direction",
    [
        (19, 18, "Too High", "LOWER"),
        (20, 9, "Too High", "LOWER"),
        (9, 18, "Too Low", "HIGHER"),
        (49, 50, "Too Low", "HIGHER"),
    ],
)
def test_hint_direction(guess, secret, expected, direction):
    """Too-high guesses say go LOWER and too-low guesses say go HIGHER.

    Pairs like (20, 9) and (9, 18) would fail if the numbers were compared as text.
    """
    outcome, message = check_guess(guess, secret)
    assert outcome == expected
    assert direction in message


# ---------------------------------------------------------------------------
# logic_utils.py: build_guess_summary
# ---------------------------------------------------------------------------


def test_guess_summary_preserves_attempt_order_and_results():
    """Summary rows are numbered in guess order and show each guess's result."""
    assert build_guess_summary([], secret=10) == []
    assert build_guess_summary([5, 15, 10], secret=10) == [
        {"Attempt": 1, "Guess": 5, "Result": "Too Low"},
        {"Attempt": 2, "Guess": 15, "Result": "Too High"},
        {"Attempt": 3, "Guess": 10, "Result": "Win"},
    ]


# ---------------------------------------------------------------------------
# logic_utils.py: update_score
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("attempt_limit", "scores_after_wrong_guesses"),
    [
        (6, [84, 67, 50, 34, 17, 0]),
        (8, [88, 75, 63, 50, 38, 25, 13, 0]),
        (5, [80, 60, 40, 20, 0]),
    ],
    ids=["easy", "normal", "hard"],
)
def test_wrong_guesses_scale_to_attempt_limit(
    attempt_limit,
    scores_after_wrong_guesses,
):
    """Each difficulty spreads a 100-point deduction across all attempts."""
    score = 100
    for attempts_used, expected_score in enumerate(
        scores_after_wrong_guesses,
        start=1,
    ):
        score = update_score(score, "Too Low", attempts_used, attempt_limit)
        assert score == expected_score


@pytest.mark.parametrize(
    ("attempts_used", "expected_score"),
    [(1, 100), (5, 20)],
)
def test_hard_win_keeps_points_remaining(attempts_used, expected_score):
    """A Hard win ranges from 100 on the first try to 20 on the last."""
    assert update_score(0, "Win", attempts_used, 5) == expected_score


# ---------------------------------------------------------------------------
# app.py: starting and resetting a game
# ---------------------------------------------------------------------------


def test_game_starts_with_all_attempts_available():
    """A fresh game has all attempts available and displays 100 points."""
    at = load_app()
    assert at.session_state.attempts == 0
    assert "Attempts left: 8" in at.info[0].value
    assert at.metric[0].label == "Current Score"
    assert at.metric[0].value == "100"


def test_winning_guess_finishes_game(monkeypatch):
    """A correct guess records the win, attempt, history, and score."""
    monkeypatch.setattr("logic_utils.save_high_score", lambda score: score)
    at = load_app()
    at.session_state.secret = 25
    at.text_input[0].set_value("25")
    at.button[0].click().run()

    assert at.session_state.status == "won"
    assert at.session_state.attempts == 1
    assert at.session_state.history == [25]
    assert at.session_state.score == 100
    assert at.session_state.high_score == 100


@pytest.mark.parametrize(
    ("difficulty", "secret", "guess", "expected_score"),
    [
        ("Normal", 50, 1, 88),
    ],
)
def test_first_wrong_guess_uses_difficulty_attempt_limit(
    difficulty,
    secret,
    guess,
    expected_score,
):
    """The live app applies the deduction for the selected difficulty."""
    at = load_app()
    at.selectbox[0].set_value(difficulty).run()
    at.session_state.secret = secret
    at.text_input[0].set_value(str(guess))
    at.button[0].click().run()

    assert at.session_state.attempts == 1
    assert at.session_state.score == expected_score
    assert at.metric[0].label == "Current Score"
    assert at.metric[0].value == str(expected_score)


def test_attempt_limit_ends_game():
    """The final allowed wrong guess ends the game with consistent state."""
    at = load_app()
    at.session_state.secret = 50
    for _ in range(8):
        at.text_input[0].set_value("1")
        at.button[0].click().run()

    assert at.session_state.status == "lost"
    assert at.session_state.attempts == 8
    assert at.session_state.history == [1] * 8
    assert at.session_state.score == 0
    assert "Out of attempts" in at.error[0].value


@pytest.mark.parametrize("finished_status", ["won", "lost"])
def test_new_game_resets_finished_game_state(finished_status):
    """Clicking New Game after a win or loss clears the old game's state."""
    at = load_app()
    at.session_state.attempts = 4
    at.session_state.score = 35
    at.session_state.status = finished_status
    at.session_state.history = [20, 40, 32]

    at.button[1].click().run()
    assert_game_reset(at)


def test_difficulty_change_starts_a_fresh_game():
    """Switching difficulty mid-game clears attempts, score and history."""
    at = load_app()
    at.session_state.attempts = 3
    at.session_state.score = -15
    at.session_state.status = "playing"
    at.session_state.history = [10, 20, 30]

    at.selectbox[0].set_value("Easy").run()
    assert_game_reset(at)


# ---------------------------------------------------------------------------
# app.py: difficulty range and secret
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("difficulty, low, high", RANGES)
def test_range_message_matches_difficulty(difficulty, low, high):
    """The range message shows the selected difficulty's range."""
    at = load_app()
    at.selectbox[0].set_value(difficulty).run()
    assert f"Guess a number between {low} and {high}." in at.info[0].value


def test_secret_uses_exact_difficulty_bounds(monkeypatch):
    """Difficulty changes and New Game pass the exact bounds to randint."""
    at = load_app()
    monkeypatch.setattr(
        "random.randint", lambda selected_low, selected_high: selected_high
    )
    at.selectbox[0].set_value("Easy").run()
    assert at.session_state.secret == 20

    at.button[1].click().run()
    assert at.session_state.secret == 20


# ---------------------------------------------------------------------------
# app.py: submitting guesses
# ---------------------------------------------------------------------------


def test_rejected_guesses_do_not_use_attempts_or_go_in_history():
    """Out-of-range and non-number guesses use no attempt and stay out of History."""
    at = load_app()
    at.session_state.secret = 10
    start = at.session_state.attempts

    for raw in ["51", "abc", "7", "5"]:
        at.text_input[0].set_value(raw)
        at.button[0].click()
        at.run()

    assert at.session_state.attempts - start == 2
    assert at.session_state.history == [7, 5]


def test_hints_are_correct_on_every_attempt():
    """The hint stays correct across 5 attempts in a row."""
    at = load_app()
    at.session_state.secret = 18

    for attempt in range(5):
        at.text_input[0].set_value("9")
        at.button[0].click()
        at.run()
        assert "HIGHER" in at.warning[0].value, f"wrong hint on guess {attempt + 1}"
