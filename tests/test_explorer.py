"""Offline tests with synthetic records and the frozen local snapshot."""
import csv
import io
import math
from pathlib import Path
import tempfile
import unittest
from earthquake_explorer import (find_earthquakes, format_results,
                                 load_earthquakes, main, parse_minimum)

FIXTURE = '''id,time,place,mag,depth,type
a,2026-01-01T00:00:00Z,"10 km S of Town, Alaska",3.0,10,earthquake
b,2026-01-02T00:00:00Z,"20 km N of Town, Alaska",4.0,20,earthquake
c,2026-01-03T00:00:00Z,California,5.0,5,earthquake
'''


class ExplorerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'fixture.csv'
        self.path.write_text(FIXTURE, encoding='utf-8')
        self.events, _ = load_earthquakes(self.path)

    def test_inclusive_boundary_and_case_insensitive_location(self):
        result = find_earthquakes(self.events, ' ALASKA ', 3)
        self.assertEqual([event['id'] for event in result], ['b', 'a'])
        self.assertIn('Mean reported magnitude: 3.50', format_results(result))

    def test_blank_location_and_high_threshold(self):
        self.assertEqual([x['id'] for x in find_earthquakes(self.events, '', 5)], ['c'])

    def test_no_results(self):
        matches = find_earthquakes(self.events, 'Atlantis', 2.5)
        self.assertEqual(matches, [])
        self.assertIn('No earthquakes matched', format_results(matches))

    def test_invalid_magnitudes(self):
        for value in ['abc', '', 'nan', 'inf', '-inf', '2.49', '10.01', None]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_minimum(value)
        self.assertEqual(parse_minimum('2.5'), 2.5)
        self.assertEqual(parse_minimum('10'), 10)

    def test_bad_rows_and_duplicates_are_skipped(self):
        with self.path.open('a', encoding='utf-8') as f:
            f.write('d,2026-01-01,Somewhere,nan,1,earthquake\n')
            f.write('e,2026-01-01,Somewhere,3,inf,earthquake\n')
            f.write('f,2026-01-01,Somewhere,3,1,explosion\n')
            f.write('g,2026-01-01,Somewhere,,1,earthquake\n')
            f.write('a,2026-01-01,Duplicate,3,1,earthquake\n')
            f.write('h,2026-01-01,,3,1,earthquake\n')
            f.write('short,row\n')
        events, skipped = load_earthquakes(self.path)
        self.assertEqual(len(events), 3)
        self.assertEqual(skipped, 7)

    def test_missing_columns_and_missing_file(self):
        self.path.write_text('place,mag\nAlaska,3\n', encoding='utf-8')
        with self.assertRaises(ValueError):
            load_earthquakes(self.path)
        output = []
        self.assertEqual(main(output_fn=output.append, data_path=self.path), 1)
        self.path.unlink()
        self.assertEqual(main(output_fn=output.append, data_path=self.path), 1)
        self.assertIn('Cannot load', output[-1])

    def test_menu_recovers_from_input_errors(self):
        answers = iter(['wrong', '1', 'Alaska', 'abc', 'nan', '3', '2'])
        output = []
        result = main(lambda prompt: next(answers), output.append, self.path)
        self.assertEqual(result, 0)
        self.assertIn('Please choose 1 or 2.', output)
        self.assertTrue(any('Matching earthquakes: 2' in line for line in output))
        self.assertEqual(output[-1], 'Goodbye.')

    def test_eof_exits_cleanly(self):
        def ended(prompt):
            raise EOFError
        self.assertEqual(main(ended, lambda text: None, self.path), 0)

    def test_empty_data(self):
        self.path.write_text(FIXTURE.splitlines()[0] + '\n', encoding='utf-8')
        self.assertEqual(main(output_fn=lambda text: None, data_path=self.path), 1)

    def test_result_limit_does_not_change_summary(self):
        text = format_results(find_earthquakes(self.events, '', 2.5), limit=1)
        self.assertIn('Matching earthquakes: 3', text)
        self.assertIn('Mean reported magnitude: 4.00', text)
        self.assertIn('Showing 1 of 3', text)
        self.assertNotIn('10 km S', text)

    def test_ties_sort_deterministically(self):
        events = [dict(event, magnitude=3) for event in self.events]
        result = find_earthquakes(list(reversed(events)), '', 2.5)
        self.assertEqual([x['id'] for x in result], ['a', 'b', 'c'])

    def test_snapshot_against_independent_csv_calculation(self):
        events, skipped = load_earthquakes()
        self.assertTrue(events)
        self.assertTrue(all(math.isfinite(x['magnitude']) for x in events))
        from earthquake_explorer import DATA_FILE
        with DATA_FILE.open(encoding='utf-8', newline='') as f:
            raw = list(csv.DictReader(f))
        expected = sum(1 for x in raw if x['type'] == 'earthquake'
                       and 'alaska' in x['place'].lower() and float(x['mag']) >= 3)
        self.assertEqual(len(find_earthquakes(events, 'Alaska', 3)), expected)
        self.assertEqual(len(events) + skipped, len(raw))


if __name__ == '__main__':
    unittest.main()
