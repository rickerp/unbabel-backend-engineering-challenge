import os
import json
from unittest import TestCase
from datetime import datetime
from main import average_delivery_time_by_minute, parse_stream, AverageDeliveryTimeDict
from inputoutput.gen import generate_events_stream


def load_json(json_path: str) -> list[AverageDeliveryTimeDict]:
    with open(json_path, "r") as fp:
        return json.load(fp)


class TestParseStream(TestCase):
    def test_example(self):
        INPUT_PATH = "inputoutput/example/input.json"
        input_data = load_json(INPUT_PATH)
        events = parse_stream(INPUT_PATH)

        self.assertEqual(len(events), len(input_data))
        for parsedEvent, rawEvent in zip(events, input_data):
            self.assertIsInstance(parsedEvent.timestamp, datetime)
            self.assertIsInstance(parsedEvent.duration, int)

            self.assertEqual(parsedEvent.timestamp, datetime.fromisoformat(rawEvent["timestamp"]))
            self.assertEqual(parsedEvent.duration, rawEvent["duration"])

    def test_json_invalid(self):
        with self.assertRaises(json.JSONDecodeError):
            parse_stream("inputoutput/invalid-json/input.json")

    def test_no_duration_invalid(self):
        with self.assertRaises(KeyError):
            parse_stream("inputoutput/invalid-no-duration/input.json")

    def test_no_timestamp_invalid(self):
        with self.assertRaises(KeyError):
            parse_stream("inputoutput/invalid-no-timestamp/input.json")


class TestAverageDeliveryTimeByMinute(TestCase):
    def test_example(self):
        events = parse_stream("inputoutput/example/input.json")
        avgs = average_delivery_time_by_minute(events, 10)
        exp_avgs = load_json("inputoutput/example/10-expected-output.json")

        assert avgs == exp_avgs, "Output does not match expected output for 10 minutes window size"

    def test_example_with_20_window(self):
        events = parse_stream("inputoutput/example/input.json")
        avgs = average_delivery_time_by_minute(events, 20)
        exp_avgs = load_json("inputoutput/example/20-expected-output.json")

        assert avgs == exp_avgs, "Output does not match expected output for 20 minutes window size"

    def test_example_with_5_window(self):
        events = parse_stream("inputoutput/example/input.json")
        avgs = average_delivery_time_by_minute(events, 5)
        exp_avgs = load_json("inputoutput/example/5-expected-output.json")

        assert avgs == exp_avgs, "Output does not match expected output for 5 minutes window size"

    def test_example_with_5_window_invalid_match(self):
        events = parse_stream("inputoutput/example/input.json")
        avgs = average_delivery_time_by_minute(events, 5)
        exp_avgs = load_json("inputoutput/example/5-invalid-expected-output.json")

        assert avgs != exp_avgs, "Output shouldn't match the expected output (window size 5)"

    def test_exclusive_start_assumption(self):
        events = parse_stream("inputoutput/exclusive-start-assumption/input.json")
        avgs = average_delivery_time_by_minute(events, 10)

        assert avgs[-1]["average_delivery_time"] == events[1].duration, \
            f"Last minute average shouldn't consider the first event as it's timestamp {events[0].timestamp} \
                and the minute being considered is {avgs[-1]['date']} and we are assumming the interval as exclusive start."


class TestStressAverageDeliveryTimeByMinute(TestCase):
    @classmethod
    def setUpClass(cls):
        BIG_FILES = {1000: "inputoutput/big-thousand-events/input.json",
                     10000: "inputoutput/big-tenthousand-events/input.json",
                     100000: "inputoutput/big-hundredthousand-events/input.json"}

        for n_events, path in BIG_FILES.items():
            # Check if file exists, if not, generate it
            if not os.path.exists(path):
                generate_events_stream(n_events, path)

    def test_thousand_events_ok(self):
        events = parse_stream("inputoutput/big-thousand-events/input.json")
        assert average_delivery_time_by_minute(events, 10) is not None

    def test_tenthousand_events_ok(self):
        events = parse_stream("inputoutput/big-tenthousand-events/input.json")
        assert average_delivery_time_by_minute(events, 10) is not None

    def test_hundredthousand_events_ok(self):
        events = parse_stream("inputoutput/big-hundredthousand-events/input.json")
        assert average_delivery_time_by_minute(events, 10) is not None

    def test_hundredthousand_events_with_1_window_ok(self):
        events = parse_stream("inputoutput/big-hundredthousand-events/input.json")
        assert average_delivery_time_by_minute(events, 1) is not None

    def test_hundredthousand_events_with_100_window_ok(self):
        events = parse_stream("inputoutput/big-hundredthousand-events/input.json")
        assert average_delivery_time_by_minute(events, 100) is not None

    # def test_million_events_ok(self):
    #     events = parse_stream("inputoutput/million-events/input.json")
    #     assert average_delivery_time_by_minute(events, 10) is not None
