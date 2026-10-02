"""Streamlit UI for the Glitchy Guesser number-guessing game."""

import random

import streamlit as st

from logic_utils import (
    build_guess_summary,
    check_guess,
    get_range_for_difficulty,
    load_high_score,
    parse_guess,
    save_high_score,
    update_score,
)


def reset_game(low: int, high: int, difficulty: str) -> None:
    """Reset all per-game session state.

    Draws a new secret from the inclusive ``low``-``high`` range and stores
    ``difficulty`` so a later difficulty change can be detected.
    """
    # FIX: Centralized with AI assistance and verified through Streamlit tests.
    st.session_state.update(
        secret=random.randint(low, high),
        secret_difficulty=difficulty,
        attempts=0,
        score=100,
        status="playing",
        history=[],
    )


def render_game_progress(
    progress_display,
    summary_display,
    attempts: int,
    attempt_limit: int,
    history: list[int],
    secret: int,
) -> None:
    """Render current attempt progress and a structured guess summary.

    ``progress_display`` and ``summary_display`` are ``st.empty()``
    placeholders whose contents are replaced on each call.
    """
    progress_display.progress(
        min(attempts / attempt_limit, 1.0),
        text=f"Attempts used: {attempts}/{attempt_limit}",
    )

    summary = build_guess_summary(history, secret)
    if summary:
        summary_display.dataframe(summary, hide_index=True, width="stretch")
    else:
        summary_display.caption("No guesses yet.")


def render_game_state(
    info_display,
    debug_display,
    low: int,
    high: int,
    attempt_limit: int,
    difficulty: str,
) -> None:
    """Render current counters and developer state from the same snapshot.

    ``info_display`` and ``debug_display`` are ``st.empty()`` placeholders
    whose contents are replaced on each call.
    """
    # FIX: AI helped replace the hardcoded prompt with the active range.
    info_display.info(
        f"Guess a number between {low} and {high}. "
        f"Attempts left: {attempt_limit - st.session_state.attempts}"
    )

    with debug_display.container(), st.expander("Developer Debug Info"):
        st.write("Secret:", st.session_state.secret)
        st.write("Attempts:", st.session_state.attempts)
        st.write("Score:", st.session_state.score)
        st.write("Difficulty:", difficulty)
        st.write("History:", st.session_state.history)


st.set_page_config(page_title="Glitchy Guesser", page_icon="🎮")

st.title("🎮 Game Glitch Investigator")
st.caption("An AI-generated guessing game. Something is off.")

st.sidebar.header("Settings")

difficulty = st.sidebar.selectbox("Difficulty", ["Easy", "Normal", "Hard"], index=1)
attempt_limit = {"Easy": 6, "Normal": 8, "Hard": 5}[difficulty]

low, high = get_range_for_difficulty(difficulty)

st.sidebar.caption(f"Range: {low} to {high}")
st.sidebar.caption(f"Attempts allowed: {attempt_limit}")
current_score_display = st.sidebar.empty()
high_score_display = st.sidebar.empty()

# FIX: AI helped track difficulty; Streamlit tests verify reset timing.
if (
    "secret" not in st.session_state
    or st.session_state.get("secret_difficulty") != difficulty
):
    reset_game(low, high, difficulty)

for key, default in (
    ("attempts", 0),
    ("score", 100),
    ("status", "playing"),
    ("history", []),
):
    if key not in st.session_state:
        st.session_state[key] = default

if "high_score" not in st.session_state:
    st.session_state.high_score = load_high_score()

current_score_display.metric("Current Score", st.session_state.score)
high_score_display.metric("High Score", st.session_state.high_score)

st.subheader("Make a guess")

info_display = st.empty()
debug_display = st.empty()
render_game_state(
    info_display,
    debug_display,
    low,
    high,
    attempt_limit,
    difficulty,
)

raw_guess = st.text_input("Enter your guess:", key=f"guess_input_{difficulty}")

col1, col2, col3 = st.columns(3)
with col1:
    submit = st.button("Submit Guess 🚀")
with col2:
    new_game = st.button("New Game 🔁")
with col3:
    show_hint = st.checkbox("Show hint", value=True)

hint_display = st.empty()

st.subheader("Session Summary")
progress_display = st.empty()
summary_display = st.empty()
render_game_progress(
    progress_display,
    summary_display,
    st.session_state.attempts,
    attempt_limit,
    st.session_state.history,
    st.session_state.secret,
)

if new_game:
    # FIX: AI suggested reusing the complete reset; I verified the state.
    reset_game(low, high, difficulty)
    st.success("New game started.")
    st.rerun()

if st.session_state.status != "playing":
    if st.session_state.status == "won":
        st.success("You already won. Start a new game to play again.")
    else:
        st.error("Game over. Start a new game to try again.")
    st.stop()

if submit:
    ok, guess_int, err = parse_guess(raw_guess, low, high)

    if not ok:
        hint_display.error(err)
    else:
        # FIX: AI moved this after validation; pytest verifies rejected inputs.
        st.session_state.attempts += 1
        st.session_state.history.append(guess_int)

        # FIX: AI removed text coercion; focused hint tests verify the result.
        outcome, message = check_guess(guess_int, st.session_state.secret)

        if show_hint:
            hint_display.warning(message)

        st.session_state.score = update_score(
            st.session_state.score,
            outcome,
            st.session_state.attempts,
            attempt_limit,
        )
        current_score_display.metric("Current Score", st.session_state.score)

        if outcome == "Win":
            st.session_state.high_score = save_high_score(st.session_state.score)
            high_score_display.metric("High Score", st.session_state.high_score)
            st.balloons()
            st.session_state.status = "won"
            st.success(
                f"You won! The secret was {st.session_state.secret}. "
                f"Final score: {st.session_state.score}"
            )
        elif st.session_state.attempts >= attempt_limit:
            st.session_state.status = "lost"
            st.error(
                f"Out of attempts! The secret was {st.session_state.secret}. "
                f"Score: {st.session_state.score}"
            )

        render_game_progress(
            progress_display,
            summary_display,
            st.session_state.attempts,
            attempt_limit,
            st.session_state.history,
            st.session_state.secret,
        )
        render_game_state(
            info_display,
            debug_display,
            low,
            high,
            attempt_limit,
            difficulty,
        )

st.divider()
st.caption("Built by an AI that claims this code is production-ready.")
