"""Filter Wordle candidates using known colors and rank by word frequency."""
from __future__ import annotations

import json
import math
from pathlib import Path
import re
import sys

DATA_DIR = Path(__file__).resolve().parent


def _positions(value: str | None, color: str) -> set[tuple[str, int]]:
    if value is None or isinstance(value, str) and not value.strip():
        return set()
    if not isinstance(value, str):
        raise ValueError(f"{color} clues must be comma-separated letter/position pairs.")
    clues = set()
    for entry in value.lower().split(","):
        entry = entry.strip()
        if not re.fullmatch(r"[a-z][1-5]", entry):
            raise ValueError(f"Invalid {color} clue: {entry!r}; use e.g. r2 (positions 1–5).")
        clues.add((entry[0], int(entry[1]) - 1))
    return clues


def findword(guessed: str, g: str | None = None, y: str | None = None,
             gray: str = "", *, word_file: str | Path | None = None,
             frequency_file: str | Path | None = None) -> list[dict]:
    """Return {word, weight} candidates satisfying all supplied constraints.

    Positions are one-based in g/y. Repeated yellow clues exclude positions;
    they do not establish exact letter counts across previous guesses.
    Optional file paths support alternate dictionaries and isolated callers.
    """
    greens = _positions(g, "green")
    yellows = _positions(y, "yellow")
    if not isinstance(guessed, str) or not isinstance(gray, str):
        raise ValueError("Guesses and gray letters must be strings.")
    guessed_words = {word.strip().lower() for word in guessed.split(",") if word.strip()}
    if any(not re.fullmatch(r"[a-z]{5}", word) for word in guessed_words):
        raise ValueError("Each guessed word must contain exactly five English letters.")
    gray = gray.strip().lower()
    if gray and not re.fullmatch(r"[a-z]+", gray):
        raise ValueError("Gray clues must contain letters only.")
    green_by_position = {}
    for char, pos in greens:
        if pos in green_by_position and green_by_position[pos] != char:
            raise ValueError("Two different green letters cannot occupy the same position.")
        green_by_position[pos] = char
    if greens & yellows:
        raise ValueError("A letter cannot be both green and yellow at the same position.")
    known_letters = {char for char, _ in greens | yellows}
    if set(gray) & known_letters:
        raise ValueError("A gray letter cannot also be green or yellow.")
    excluded_letters = set(gray) | (set("".join(guessed_words)) - known_letters)
    required_yellow = {char for char, _ in yellows}

    words_path = Path(word_file) if word_file is not None else DATA_DIR / "fivewords.txt"
    weights_path = Path(frequency_file) if frequency_file is not None else DATA_DIR / "freq_map.json"
    candidates = []
    seen = set()
    with words_path.open(encoding="utf-8") as source:
        for line in source:
            word = line.strip().lower()
            if not re.fullmatch(r"[a-z]{5}", word) or word in seen:
                continue
            seen.add(word)
            if word in guessed_words or excluded_letters.intersection(word):
                continue
            if not required_yellow.issubset(word):
                continue
            if any(word[pos] == char for char, pos in yellows):
                continue
            if any(word[pos] != char for char, pos in greens):
                continue
            candidates.append(word)

    with weights_path.open(encoding="utf-8") as source:
        weights = json.load(source)
    if not isinstance(weights, dict):
        raise ValueError("The frequency file must contain a JSON object.")
    ranked = []
    for word in candidates:
        weight = weights.get(word, 0)
        if isinstance(weight, bool) or not isinstance(weight, (int, float)) or (isinstance(weight, float) and not math.isfinite(weight)):
            raise ValueError(f"Invalid frequency weight for {word!r}.")
        ranked.append({"word": word, "weight": weight})
    return sorted(ranked, key=lambda item: item["weight"], reverse=True)


def main() -> int:
    """Run the interactive CLI; EOF and Ctrl+C end it without a traceback."""
    while True:
        try:
            guessed = input("Input words you guessed? Format: word1,word2,word3\n")
            green = input("Input GREEN letters and positions? Enter for none. Format: h1,j4,k5\n")
            yellow = input("Input YELLOW letters and positions? Enter for none. Format: h1,j4,k5\n")
            results = findword(guessed, g=green, y=yellow)
        except (EOFError, KeyboardInterrupt):
            return 0
        except (OSError, json.JSONDecodeError) as error:
            print(f"Cannot load Wordle data: {error}", file=sys.stderr)
            return 1
        except ValueError as error:
            print(f"Cannot find candidates: {error}", file=sys.stderr)
            continue
        if not results:
            print("No candidates match these clues.")
        for count, item in enumerate(results, 1):
            print(f"{count}, {item['word']}, {item['weight']}")


if __name__ == "__main__":
    raise SystemExit(main())
