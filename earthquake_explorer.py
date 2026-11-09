"""Explore a bundled USGS earthquake snapshot without a network connection."""

import csv
import math
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent / 'data' / 'earthquakes.csv'


def load_earthquakes(path=DATA_FILE):
    """Read valid earthquake rows; count rows unsuitable for this explorer."""
    earthquakes = []
    skipped = 0
    with open(path, encoding='utf-8', newline='') as source:
        reader = csv.DictReader(source)
        required = {'id', 'time', 'place', 'mag', 'depth', 'type'}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError('The CSV is missing required columns.')
        seen_ids = set()
        for row in reader:
            # Non-earthquake events and incomplete records must not affect totals.
            try:
                magnitude = float(row['mag'])
                depth = float(row['depth'])
                event_id = row['id'].strip()
                place = row['place'].strip()
                event_time = row['time'].strip()
                valid = (row['type'] == 'earthquake' and event_id and place
                         and event_time and math.isfinite(magnitude)
                         and math.isfinite(depth) and event_id not in seen_ids)
            except (ValueError, TypeError, AttributeError):
                valid = False
            if not valid:
                skipped += 1
                continue
            seen_ids.add(event_id)
            earthquakes.append({'id': event_id, 'time': event_time,
                                'place': place, 'magnitude': magnitude,
                                'depth': depth})
    return earthquakes, skipped


def parse_minimum(text):
    """Accept only a finite magnitude between 2.5 and 10, inclusive."""
    try:
        number = float(text)
    except (ValueError, TypeError):
        raise ValueError('Enter a number from 2.5 to 10.') from None
    if not math.isfinite(number) or not 2.5 <= number <= 10:
        raise ValueError('Enter a finite number from 2.5 to 10.')
    return number


def find_earthquakes(earthquakes, location, minimum):
    """Match a location substring and include events at the magnitude boundary."""
    minimum = parse_minimum(minimum)
    location = location.strip().casefold()
    matches = [event for event in earthquakes
               if location in event['place'].casefold()
               and event['magnitude'] >= minimum]
    # Strongest first, with time and ID providing reproducible tie ordering.
    return sorted(matches, key=lambda event: (-event['magnitude'],
                                              event['time'], event['id']))


def format_results(matches, limit=10):
    """Summarize all matches while keeping the displayed event list manageable."""
    if not matches:
        return 'No earthquakes matched your search in this snapshot.'
    strongest = max(event['magnitude'] for event in matches)
    average = sum(event['magnitude'] for event in matches) / len(matches)
    lines = [f'Matching earthquakes: {len(matches)}',
             f'Strongest magnitude: {strongest:.2f}',
             f'Mean reported magnitude: {average:.2f}',
             'The mean describes reported magnitudes, not average energy.',
             f'Showing {min(limit, len(matches))} of {len(matches)} matches:',
             'UTC time | Magnitude | Depth (km) | Location']
    for event in matches[:limit]:
        lines.append(f"{event['time']} | {event['magnitude']:.2f} | "
                     f"{event['depth']:.2f} | {event['place']}")
    return '\n'.join(lines)


def main(input_fn=input, output_fn=print, data_path=DATA_FILE):
    """Run a repeating search menu, recovering from ordinary input mistakes."""
    try:
        earthquakes, skipped = load_earthquakes(data_path)
    except (OSError, UnicodeError, ValueError, csv.Error) as error:
        output_fn(f'Cannot load the earthquake snapshot: {error}')
        return 1
    output_fn('EARTHQUAKE EXPLORER')
    output_fn('USGS M2.5+ weekly feed snapshot, not a live alert or prediction.')
    output_fn(f'Loaded {len(earthquakes)} earthquakes; skipped {skipped} rows.')
    if not earthquakes:
        output_fn('No usable earthquake records are available.')
        return 1
    times = [event['time'] for event in earthquakes]
    output_fn(f'Event times (UTC): {min(times)} to {max(times)}')
    try:
        while True:
            choice = input_fn('\n1. Search earthquakes\n2. Exit\nChoose 1 or 2: ').strip()
            if choice == '2':
                output_fn('Goodbye.')
                return 0
            if choice != '1':
                output_fn('Please choose 1 or 2.')
                continue
            location = input_fn('Location text (blank for all locations): ')
            # Keep asking for magnitude until the user supplies a valid number.
            while True:
                try:
                    minimum = parse_minimum(input_fn('Minimum magnitude (2.5 to 10): '))
                    break
                except ValueError as error:
                    output_fn(str(error))
            matches = find_earthquakes(earthquakes, location, minimum)
            output_fn(format_results(matches))
    except (EOFError, KeyboardInterrupt):
        output_fn('\nSession ended. Goodbye.')
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
