# wordle-guesser-code


![Project screenshot](./screenshot.png)

Filter five-letter Wordle candidates from your known colors and rank them by
the bundled English frequency weights. Runs locally with Python 3.10 or later;
no external service or third-party Python package is required.

## Project Status

The CLI and importable `findword` function are covered by standard-library
regression tests. This is a local utility; there is no hosted application backend.

## Setup

Install dependencies for the detected stack and run the existing entry point. Keep secrets in ignored environment files.

## Usage

Run `python wordleguesser.py` from the repository, or pass the full script path
from another directory. Data files are located beside the script.

Enter previous guesses separated by commas, green clues such as `c1`, and
yellow clues such as `r2`. Positions run from 1 to 5. Enter a blank line for no
color clues; Ctrl+C or EOF ends the session. Invalid clues are explained and
can be retried. Case and surrounding whitespace are normalized.

For example, guess `crane`, green `c1`, yellow `r2`: candidates must start with
`c`, contain `r` outside position 2, and contain none of `a`, `n`, or `e`.
Every distinct yellow letter must be present. Results are ranked by weight;
unlisted frequency weights default to zero.

Library use: `findword('crane', g='c1', y='r2')` returns dictionaries with `word`
and `weight` fields. Importing the module does not prompt or load data. Optional
`word_file` and `frequency_file` arguments accept alternate local data paths.

The compact clue format does not encode exact duplicate-letter counts from
individual feedback rounds. Repeated yellow clues exclude positions without
assuming that each clue represents another occurrence of the letter.

Run checks with `python -B -m unittest discover -s tests -v`. Tests use temporary
synthetic dictionaries; the bundled word list and frequency file are preserved.

## License

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
