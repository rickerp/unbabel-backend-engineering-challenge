import os
import json
import random
import argparse
from datetime import datetime, timedelta


def generate_events_stream(n_events, output_path="generated-input.json"):
    "Generate a stream of events and save it to a file."
    EXAMPLE_EVENT = {
        # Example event data without the timestamp and duration
        "translation_id": "5aa5b2f39f7254a75aa5",
        "source_language": "en",
        "target_language": "fr",
        "client_name": "airliberty",
        "event_name": "translation_delivered",
        "nr_words": 30,
    }

    event_timestamp = datetime.now()  # First event timestamp
    events_stream = []
    for _ in range(n_events):
        events_stream.append(
            {
                **EXAMPLE_EVENT,
                "timestamp": str(event_timestamp),
                "duration": random.randint(1, 100),  # Duration is random
            }
        )
        event_timestamp += timedelta(minutes=random.randint(1, 25))  # Random time between events

    folder_path = os.path.dirname(output_path)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    with open(output_path, "w") as fp:
        json.dump(events_stream, fp)


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="Unbabel CLI")
    arg_parser.add_argument("n_events", type=int, help="Number of events to generate")
    arg_parser.add_argument("output_file", type=str, help="Output file path", default="generated-input.json", nargs='?')
    args = arg_parser.parse_args()

    generate_events_stream(args.n_events, args.output_file)
