import json
import ijson
import argparse
import typing as tp
from datetime import datetime, timedelta


class AverageDeliveryTimeDict(tp.TypedDict):
    date: str
    average_delivery_time: float


class Event(tp.TypedDict):
    timestamp: datetime
    duration: int


def simple_avg(l: list[int]) -> float:
    "Return the average of a list of integers."
    return sum(l) * 1.0 / len(l) if len(l) > 0 else 0


def round_ceil_to_minute(dt: datetime) -> datetime:
    "Round a datetime to the minute."
    floored_dt = dt.replace(second=0, microsecond=0)
    return floored_dt if dt == floored_dt else floored_dt + timedelta(minutes=1)


def stream_events(stream_json_path: str) -> tp.Generator[Event, None, None]:
    "From a given json file path, yields an event at a time once read."
    with open(stream_json_path, "rb") as fp:
        for prefix, parse_type, value in ijson.parse(fp):
            if parse_type == "start_map":
                event: Event = {}
            if prefix.endswith(".timestamp"):
                event["timestamp"] = datetime.fromisoformat(value)
            if prefix.endswith(".duration"):
                event["duration"] = value
            if parse_type == "end_map":
                yield event


def average_delivery_time_by_minute(
    events_stream: tp.Generator[Event, None, None], window_size: int
) -> list[AverageDeliveryTimeDict]:
    """
    From a given stream of events and a window size, return the average delivery time from the last window_size minutes (by each minute).
    @param events_stream: Stream of events - Generator which yields a dict event containing the timestamp and duration.
    @param window_size: Timeframe window size (in minutes).
    @return: List of dictionaries with the minute as a datetime and the average delivery time for that minute
    """
    within_window: list[Event] = []  # List of events that are within the window_size
    avgs_by_minute: list[AverageDeliveryTimeDict] = []

    for event_i in events_stream:
        window_end = round_ceil_to_minute((within_window[-1] if within_window else event_i)["timestamp"])
        while window_end < event_i["timestamp"]:  # Assumption 1 - Exclusive start (README.md)
            # Removal of outdated events (outside the window)
            while len(within_window) > 0 and \
                    within_window[0]["timestamp"] <= (window_end - timedelta(minutes=window_size)):
                # Remove the first element, if its timestamp is less than the window's start (window_end - window_size)
                within_window.pop(0)

            avgs_by_minute.append({
                "date": str(window_end),
                "average_delivery_time": simple_avg([e_ww["duration"] for e_ww in within_window]),
            })
            window_end += timedelta(minutes=1)
        within_window.append(event_i)

    # Removal of last outdated events
    while len(within_window) > 0 and \
            within_window[0]["timestamp"] <= (window_end - timedelta(minutes=window_size)):
        within_window.pop(0)

    # Assumption 2 - Start with an average time of 0 and end with the last event first minute contribution (README.md)
    avgs_by_minute = [
        {"date": str(datetime.fromisoformat(avgs_by_minute[0]["date"]) -
                     timedelta(minutes=1)), "average_delivery_time": 0},
        *avgs_by_minute,
        {"date": str(window_end), "average_delivery_time": simple_avg([e_ww["duration"] for e_ww in within_window])},
    ]
    return avgs_by_minute


def main(input_file: str, window_size: int):
    return average_delivery_time_by_minute(stream_events(input_file), window_size)


if __name__ == "__main__":
    # Target example terminal cli usage: unbabel_cli --input_file events.json --window_size 10
    arg_parser = argparse.ArgumentParser(description="Unbabel CLI")
    arg_parser.add_argument("--input_file", type=str, help="Input file path")
    arg_parser.add_argument("--window_size", type=int, help="Timeframe window size (in minutes)")
    arg_parser.add_argument(
        "--output_file", type=str, help="Output file path - if omitted will be in stdout", required=False, default=None
    )
    args = arg_parser.parse_args()

    avgs = main(args.input_file, args.window_size)
    if args.output_file:
        with open(args.output_file, "w") as fp:
            json.dump(avgs, fp)
    else:
        print(json.dumps(avgs, indent=4))
