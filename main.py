import json
import argparse
from datetime import datetime, timedelta


class ParsedEvent:
    timestamp: datetime
    duration: int

    def __init__(self, data: dict):
        self.timestamp = datetime.fromisoformat(data["timestamp"])
        self.duration = data["duration"]


def simple_avg(l: list[int]) -> float:
    "Return the average of a list of integers."
    return sum(l)*1.0/len(l) if len(l) > 0 else 0


def parse_stream(stream_json_path: str) -> list[ParsedEvent]:
    "From a given json file path, parse the stream of events and return a list of ParsedEvent objects."
    with open(stream_json_path, "r") as fp:
        return json.load(fp, object_hook=ParsedEvent)
    
def average_delivery_time_by_minute(events: list[ParsedEvent], window_size: int) -> list[dict]:
    "From a given list of events (ParsedEvent objects) and a window size, return the average delivery time from the last given window_size minutes by each minute."
    avgs_output = []

    within_window: list[ParsedEvent] = []  # List of events that are within the window
    last_event_added_index = -1  # Last event index (in the given list) that was added to the within_window list
    window_end = events[0].timestamp.replace(second=0, microsecond=0)  # End of the window that is being considered

    LAST_MINUTE = events[-1].timestamp.replace(second=0, microsecond=0) + timedelta(minutes=1)  # Last minute to be considered
    while window_end <= LAST_MINUTE:
        window_start = window_end - timedelta(minutes=window_size)  # Start of the window that is being considered
        
        # Add events that are within the window
        for new_event in events[last_event_added_index+1:]:
            if new_event.timestamp > window_end:
                break
            within_window.append(new_event)
            last_event_added_index += 1
               
        # Remove events that are out of the window
        for event in within_window:
            if event.timestamp > window_start:
                break
            within_window.remove(event)

        avgs_output.append({"date": str(window_end), "average_delivery_time": simple_avg([event.duration for event in within_window])})
        window_end += timedelta(minutes=1)

    return avgs_output


if __name__ == "__main__":
    # Target example terminal cli usage: unbabel_cli --input_file events.json --window_size 10
    arg_parser = argparse.ArgumentParser(description="Unbabel CLI")
    arg_parser.add_argument("--input_file", type=str, help="Input file path")
    arg_parser.add_argument("--window_size", type=int, help="Timeframe window size (in minutes)")
    args = arg_parser.parse_args()

    events = parse_stream(args.input_file)
    avgs = average_delivery_time_by_minute(events, args.window_size)

    print(avgs)
    # with open("tests/input-output/example/output.json", "r") as fp:
    #     print(f"EQUAL? {'YES' if json.load(fp) == avgs else 'NO'}")
