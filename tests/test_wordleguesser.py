"""Regression tests use tiny temporary dictionaries and no external services."""
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import wordleguesser as solver


class WordleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='wordle-fixture-')
        self.root = Path(self.temp.name).resolve()
        self.assertTrue(self.root.is_relative_to(Path(tempfile.gettempdir()).resolve()))
        self.addCleanup(self.temp.cleanup)
        self.words = self.root / 'words.txt'
        self.weights = self.root / 'weights.json'
        self.words.write_text('cabin\nmaple\norbit\ndrama\ncurry\ncurly\nbobby\n', encoding='utf-8')
        self.weights.write_text(json.dumps({'cabin': 5, 'maple': 3, 'orbit': 2, 'curry': 7, 'curly': 9}), encoding='utf-8')

    def solve(self, guessed='', **kwargs):
        return solver.findword(guessed, word_file=self.words, frequency_file=self.weights, **kwargs)

    def test_requires_every_distinct_yellow_letter(self):
        self.assertEqual(self.solve(y='a1,b2'), [{'word': 'cabin', 'weight': 5}])

    def test_optional_colors_use_documented_defaults(self):
        self.assertEqual(len(self.solve()), 7)
        self.assertEqual(self.solve(), self.solve(g='', y=''))

    def test_combines_green_yellow_and_inferred_gray(self):
        self.assertEqual([item['word'] for item in self.solve('crane', g='c1', y='r2')], ['curly', 'curry'])

    def test_yellow_letter_cannot_stay_at_its_position(self):
        self.assertNotIn('cabin', [item['word'] for item in self.solve(y='a2')])

    def test_case_whitespace_and_repeated_identical_clues(self):
        self.assertEqual(self.solve(' CRANE , ', g=' C1,c1 ', y=' R2 '), self.solve('crane', g='c1', y='r2'))

    def test_multiple_yellow_positions_do_not_invent_letter_counts(self):
        self.assertIn('cabin', [item['word'] for item in self.solve(y='a1,a3')])

    def test_rejects_bad_positions_and_conflicting_colors(self):
        cases = [{'g': 'a0'}, {'y': 'a6'}, {'g': 'a10'}, {'y': '3a'}, {'g': 'a1,b1'},
                 {'g': 'c1', 'y': 'c1'}, {'g': 'c1', 'gray': 'c'}, {'g': 5}, {'gray': 'a,b'}]
        for clues in cases:
            with self.subTest(clues=clues), self.assertRaises(ValueError):
                self.solve(**clues)

    def test_rejects_malformed_guesses_before_reading_data(self):
        for guessed in ['abc', 'sixsix', 'one,three', None]:
            with self.subTest(guessed=guessed), self.assertRaises(ValueError):
                solver.findword(guessed, word_file=self.root / 'missing', frequency_file=self.root / 'missing')

    def test_frequency_ranking_and_missing_weight(self):
        result = self.solve()
        self.assertEqual(result[0], {'word': 'curly', 'weight': 9})
        self.assertIn({'word': 'drama', 'weight': 0}, result)
        self.assertEqual([item['weight'] for item in result], sorted((item['weight'] for item in result), reverse=True))

    def test_skips_malformed_and_duplicate_dictionary_rows(self):
        self.words.write_text('CAT\ncabin\nCABIN\nabcdef\n12345\n\n', encoding='utf-8')
        self.assertEqual(self.solve(), [{'word': 'cabin', 'weight': 5}])

    def test_guessed_words_and_explicit_gray_are_excluded(self):
        self.assertEqual(self.solve('bobby', g='b1,o2,b3,b4,y5'), [])
        self.assertTrue(all('a' not in item['word'] for item in self.solve(gray='a')))

    def test_rejects_invalid_frequency_data(self):
        for weights in [[], {'cabin': 'high'}, {'cabin': float('nan')}, {'cabin': True}]:
            with self.subTest(weights=weights):
                self.weights.write_text(json.dumps(weights), encoding='utf-8')
                with self.assertRaises(ValueError):
                    self.solve()

    def test_import_and_default_paths_work_from_another_directory(self):
        copied = self.root / 'solver.py'
        copied.write_bytes(Path(solver.__file__).read_bytes())
        (self.root / 'fivewords.txt').write_bytes(self.words.read_bytes())
        (self.root / 'freq_map.json').write_bytes(self.weights.read_bytes())
        elsewhere = self.root / 'elsewhere'
        elsewhere.mkdir()
        code = ('import importlib.util; '
                's=importlib.util.spec_from_file_location("fixture", __import__("sys").argv[1]); '
                'm=importlib.util.module_from_spec(s); s.loader.exec_module(m); '
                'assert m.findword("", y="a1,b2") == [{"word":"cabin","weight":5}]')
        result = subprocess.run([sys.executable, '-B', '-c', code, str(copied)], cwd=elsewhere,
                                input='', capture_output=True, text=True, timeout=30, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '')

    def test_cli_handles_eof_and_bad_clues(self):
        with patch('builtins.input', side_effect=['', 'a9', '', EOFError()]), redirect_stdout(StringIO()), redirect_stderr(StringIO()) as errors:
            self.assertEqual(solver.main(), 0)
        self.assertIn('Invalid green clue', errors.getvalue())

    def test_cli_returns_failure_for_missing_data(self):
        with patch('builtins.input', side_effect=['', '', '']), patch.object(solver, 'DATA_DIR', self.root / 'missing'), redirect_stderr(StringIO()) as errors:
            self.assertEqual(solver.main(), 1)
        self.assertIn('Cannot load Wordle data', errors.getvalue())


if __name__ == '__main__':
    unittest.main()
