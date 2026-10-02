# 💭 Reflection: Game Glitch Investigator

Answer each question in 3 to 5 sentences. Be specific and honest about what actually happened while you worked. This is about your process, not trying to sound perfect.

## 1. What was broken when you started?

- What did the game look like the first time you ran it?

  The game loaded and looked normal at first, with the difficulty selector, guess input, score, and history visible. Once I started playing, the hints and scoring behaved inconsistently, and the game was almost impossible to win. The interface worked, but the underlying logic and session state were broken.

- List at least two concrete bugs you noticed at the start  
  (for example: "the hints were backwards").

  I noticed three related state bugs. Changing difficulty kept the old secret, New Game always generated a secret from 1–100, and New Game did not clear the score, status, or history. I also found backwards hints, text-based comparisons, incorrect ranges and scoring, and invalid guesses that consumed attempts. I fixed those additional problems, but the three state and reset bugs were the main focus of my investigation.

**Bug Reproduction Log**

Document at least 3 bugs you found. Add rows as needed.

| Input | Expected Behavior | Actual Behavior | Console Output / Error |
|-------|-------------------|-----------------|------------------------|
| Select Normal or Hard | Normal uses 1–50 and Hard uses 1–100 | Normal used 1–100 and Hard used 1–50 | N/A |
| Select any difficulty | The prompt shows the selected difficulty's range | The prompt always said "between 1 and 100" | N/A |
| Start Hard with secret 87, then select Easy | Easy starts a fresh game with a secret from 1–20 | The old Hard secret 87 remained active | N/A |
| Select Easy or Normal, then click New Game | The new secret uses the selected difficulty's range | New Game always called `random.randint(1, 100)`, so the secret could be outside the displayed range | N/A |
| Open a fresh Normal game | All 8 attempts are available | The game started with one attempt used and showed 7 remaining | N/A |
| Enter `3.5` | Reject the decimal without using an attempt | The parser silently changed `3.5` to `3` and accepted it | N/A |
| Enter 150 on Normal | Reject the guess without using an attempt | The out-of-range guess was accepted and stored in History | N/A |
| Enter `abc` | Show an error without changing attempts or History | The game used an attempt and stored `"abc"` in History | N/A |
| Guess 9 when the secret is 18 on the first submission | Return "Too Low" and say "Go HIGHER" | The secret became text on alternating attempts, so `"9"` was treated as greater than `"18"` | None (`TypeError` was caught silently) |
| Guess 19 when the secret is 18 | Return "Too High" and say "Go LOWER" | The game said "Go HIGHER" | N/A |
| Make a wrong Too High guess | The score decreases | On alternating attempts, a Too High guess added 5 points | N/A |
| Win or lose, then click New Game | Status becomes "playing," score and attempts reset, and History is empty | The old status, score, and History remained | N/A |

---

## 2. How did you use AI as a teammate?

- Which AI tools did you use on this project (for example: ChatGPT, Gemini, Copilot)?

  I used Claude Code to investigate the bugs, propose fixes, improve the tests, and implement the stretch features. I used Codex as the second model for the comparison in Challenge 5. I verified the suggestions myself through Streamlit testing, pytest, and code review instead of accepting them automatically.

- Give one example of an AI suggestion that was correct (including what the AI suggested and how you verified the result).

  One correct suggestion was to put every per-game state reset in one `reset_game` function. It generates the secret from the current difficulty's bounds and resets attempts, score, status, and history together. The app calls it for New Game and when `secret_difficulty` does not match the selected difficulty. I verified the suggestion with `test_new_game_resets_finished_game_state` and `test_difficulty_change_starts_a_fresh_game`, and both passed.

- Give one example of an AI suggestion you did not accept as written (including what the AI suggested, why you rejected or changed it, and how you verified your version). It does not have to be a suggestion that was wrong: over-engineered, out of scope, harder to read, or a poor fit for this codebase all count.

  When I asked for tests for each bug, Claude Code created a separate `test_guess_compared_as_number_not_text` test. It checked a guess of 9 against a secret of 18. During review, I discovered that an existing hint test already covered the same case, so the new test added no coverage. I removed the duplicate, kept its explanation in the `test_hint_direction` docstring, and reran the retained test to verify the behavior.

---

## 3. Debugging and testing your fixes

- How did you decide whether a bug was really fixed?

  After each fix, I saved the file and played the game again in Streamlit to see if the behavior changed. I changed difficulty and clicked New Game after both a win and a loss, then checked the secret, score, attempts, status, and history in session state. I also wrote or updated a test for each behavior and ran `pytest` until every test passed. I only counted a bug as fixed when it worked in the game and had a passing test, so it cannot quietly break again.

- Describe at least one test you ran (manual or using pytest)  
  and what it showed you about your code.

  I ran `test_new_game_resets_finished_game_state` for both a won and a lost game. It showed that New Game creates a new in-range secret and returns attempts to zero, score to 100, status to `playing`, and history to an empty list. I also ran `test_difficulty_change_starts_a_fresh_game`, which showed that changing from Hard to Easy replaces the old secret and resets the same per-game values. Additional tests cover the other fixes, including hints, parsing, ranges, scoring, and invalid input.

- Did AI help you design or understand any tests? How?

  Claude Code helped me design Streamlit tests that set session state, click New Game, and change the difficulty selector. Those tests let me check the complete reset instead of testing only one variable. It also repaired the starter assertions for the `(outcome, message)` return value and generated brief coverage for the other bugs. When pytest could not import `logic_utils.py`, it explained the cause and added `pytest.ini`, and I reviewed every change before keeping it.


---

## 4. What did you learn about Streamlit and state?

- How would you explain Streamlit "reruns" and session state to a friend who has never used Streamlit?

Every interaction causes Streamlit to run the entire script again from the top. Normal variables are recreated during each rerun, so a secret generated at the top of `app.py` could change after every click. `st.session_state` acts like a notebook that preserves values such as the secret, attempts, score, and history between reruns. Those values should be initialized only when missing and deliberately replaced when the player starts a new game or changes difficulty. That is why the repaired game keeps one secret during play but generates an appropriate new one after either reset action.

---

## 5. Looking ahead: your developer habits

- What is one habit or strategy from this project that you want to reuse in future labs or projects?
  - This could be a testing habit, a prompting strategy, or a way you used Git.

    Writing a test before fixing a bug. First I write a test that fails because of the bug, then I make the fix and check that the test passes. That way I know the test really catches the problem, and it keeps protecting against the bug later.

- What is one thing you would do differently next time you work with AI on a coding task?

  I would define all acceptance checks before asking the AI to make changes. In this project, I tested a complete live Streamlit session later in the process, and that check exposed stale counters and a deprecated table option that the logic tests did not catch. Next time, I would include manual gameplay, pytest, and Ruff checks in my original prompt so every change is verified from the beginning.

- In one or two sentences, describe how this project changed the way you think about AI generated code.

  AI is a great tool for building faster, but only when I stay in control. I need to understand what the AI is changing and why, instead of just accepting its code.
