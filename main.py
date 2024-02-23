import json
import argparse
import typing
from datetime import datetime, timedelta


class AverageDeliveryTimeDict(typing.TypedDict):
    date: str
    average_delivery_time: float


class ParsedEvent:
    timestamp: datetime
    duration: int

    def __init__(self, data: dict):
        self.timestamp = datetime.fromisoformat(data["timestamp"])
        self.duration = data["duration"]

    def __str__(self):
        return f"ParsedEvent{{timestamp: {self.timestamp}, duration: {self.duration}}}"


def simple_avg(l: list[int]) -> float:
    "Return the average of a list of integers."
    return sum(l) * 1.0 / len(l) if len(l) > 0 else 0


def parse_stream(stream_json_path: str) -> list[ParsedEvent]:
    "From a given json file path, parse the stream of events and return a list of ParsedEvent objects."
    with open(stream_json_path, "r") as fp:
        return json.load(fp, object_hook=ParsedEvent)


def average_delivery_time_by_minute(events: list[ParsedEvent], window_size: int) -> list[AverageDeliveryTimeDict]:
    """
    From a given list of events (ParsedEvent objects) and a window size, return the average delivery time from the last
    given window_size minutes by each minute.
    @param events: List of ParsedEvent objects
    @param window_size: Timeframe window size (in minutes)
    @return: List of dictionaries with the minute as a datetime and the average delivery time for that minute
    """
    avgs_output = []

    within_window: list[ParsedEvent] = []  # List of events that are within the window
    last_event_added_index = -1  # Last event index (in the given list) that was added to the within_window list
    window_end = events[0].timestamp.replace(second=0, microsecond=0)  # End of the window that is being considered

    if events[0].timestamp == window_end:
        avgs_output.append({
            "date": str(window_end - timedelta(minutes=1)),
            "average_delivery_time": 0
        })

    # Last minute to be considered
    LAST_MINUTE = events[-1].timestamp.replace(second=0, microsecond=0)
    if events[-1].timestamp != LAST_MINUTE:
        LAST_MINUTE += timedelta(minutes=1)

    while window_end <= LAST_MINUTE:
        window_start = window_end - timedelta(minutes=window_size)  # Start of the window that is being considered
        # Add events that are within the window
        for new_event in events[last_event_added_index + 1:]:
            if new_event.timestamp > window_end:
                break
            within_window.append(new_event)
            last_event_added_index += 1

        # Remove events that are out of the window
        while len(within_window) > 0:
            event = within_window[0]
            if event.timestamp > window_start:
                break
            within_window.remove(event)

        avgs_output.append({
            "date": str(window_end),
            "average_delivery_time": simple_avg([event.duration for event in within_window])
        })
        window_end += timedelta(minutes=1)

    return avgs_output


if __name__ == "__main__":
    # Target example terminal cli usage: unbabel_cli --input_file events.json --window_size 10
    arg_parser = argparse.ArgumentParser(description="Unbabel CLI")
    arg_parser.add_argument("--input_file", type=str, help="Input file path")
    arg_parser.add_argument("--window_size", type=int, help="Timeframe window size (in minutes)")
    arg_parser.add_argument("--output_file", type=str,
                            help="Output file path - if omitted will be in stdout", required=False, default=None)
    args = arg_parser.parse_args()

    events = parse_stream(args.input_file)
    avgs = average_delivery_time_by_minute(events, args.window_size)
    if args.output_file:
        with open(args.output_file, "w") as fp:
            json.dump(avgs, fp)
    else:
        print(avgs)
