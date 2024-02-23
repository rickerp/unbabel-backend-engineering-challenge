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
    def test_simple(self):
        "Test the simple case with a 10 minutes window size."
        result = average_delivery_time_by_minute(parse_stream("inputoutput/simple/input.json"), 10)
        expected = load_json("inputoutput/simple/10-expected-output.json")

        assert result == expected, "Result not as expected for the simple scenario (10 minutes window size)"

    def test_example(self):
        "Test the example case from the README.md with a 5, a 10 and 20 minutes window size."

        result_10 = average_delivery_time_by_minute(parse_stream("inputoutput/example/input.json"), 10)
        expected_10 = load_json("inputoutput/example/10-expected-output.json")
        assert result_10 == expected_10, "Result not as expected for README example (10 minutes window size)"

        result_20 = average_delivery_time_by_minute(parse_stream("inputoutput/example/input.json"), 20)
        expected_20 = load_json("inputoutput/example/20-expected-output.json")
        assert result_20 == expected_20, "Result not as expected for README example (20 minutes window size)"

        result_5 = average_delivery_time_by_minute(parse_stream("inputoutput/example/input.json"), 5)
        expected_5 = load_json("inputoutput/example/5-expected-output.json")
        assert result_5 == expected_5, "Result not as expected for README example (5 minutes window size)"

    def test_example_with_invalid_match(self):
        "Test the example case from the README.md with an invalid expected (window_size 5)"
        result = average_delivery_time_by_minute(parse_stream("inputoutput/example/input.json"), 5)
        expected = load_json("inputoutput/example/5-not-expected-output.json")
        assert result != expected, "Result shouldn't match the non expected json (5 minutes window size)"

    def test_zero_seconds_event(self):
        "Test the case where an event has 0 seconds (and microseconds) in the timestamp."

        result_simple = average_delivery_time_by_minute(parse_stream(
            "inputoutput/zero-seconds-event-simple/input.json"), 10)
        expected_simple = load_json("inputoutput/zero-seconds-event-simple/10-expected-output.json")
        assert result_simple == expected_simple, "Result not expected for the 0 seconds event simple scenario (10 minutes window size)"

        result_begin = average_delivery_time_by_minute(parse_stream(
            "inputoutput/zero-seconds-event-begin/input.json"), 10)
        expected_begin = load_json("inputoutput/zero-seconds-event-begin/10-expected-output.json")
        assert result_begin == expected_begin, "Result not expected for the 0 seconds event beggining scenario (10 minutes window size)"

        result_end = average_delivery_time_by_minute(parse_stream("inputoutput/zero-seconds-event-end/input.json"), 10)
        expected_end = load_json("inputoutput/zero-seconds-event-end/10-expected-output.json")
        assert result_end == expected_end, "Result not expected for the 0 seconds event ending scenario (10 minutes window size)"

    def test_same_minute_events(self):
        "Test the case where multiple events are within the same minute."

        result_simple = average_delivery_time_by_minute(parse_stream(
            "inputoutput/same-minute-events-simple/input.json"), 10)
        expected_simple = load_json("inputoutput/same-minute-events-simple/10-expected-output.json")
        assert result_simple == expected_simple, "Result not expected for same minute events simple scenario (10 minutes window size)"

        result_small = average_delivery_time_by_minute(parse_stream(
            "inputoutput/same-minute-events-small/input.json"), 10)
        expected_small = load_json("inputoutput/same-minute-events-small/10-expected-output.json")
        assert result_small == expected_small, "Result not expected for same minute events small scenario (10 minutes window size)"

    def test_same_timestamp_events(self):
        "Test the case where multiple events have the same timestamp."
        result = average_delivery_time_by_minute(parse_stream("inputoutput/same-timestamp-events/input.json"), 10)
        expected = load_json("inputoutput/same-timestamp-events/10-expected-output.json")
        assert result == expected, "Result not expected for same timestamp events scenario (10 minutes window size)"

    def test_complex(self):
        "Test the complex case - a mix of all the previous cases."

        result_10 = average_delivery_time_by_minute(parse_stream("inputoutput/complex/input.json"), 10)
        expected_10 = load_json("inputoutput/complex/10-expected-output.json")
        assert result_10 == expected_10, "Result not as expected for the complex scenario (10 minutes window size)"

        result_3 = average_delivery_time_by_minute(parse_stream("inputoutput/complex/input.json"), 3)
        expected_3 = load_json("inputoutput/complex/3-expected-output.json")
        assert result_3 == expected_3, "Result not as expected for the complex scenario (3 minutes window size)"

        result_2 = average_delivery_time_by_minute(parse_stream("inputoutput/complex/input.json"), 2)
        expected_2 = load_json("inputoutput/complex/2-expected-output.json")
        assert result_2 == expected_2, "Result not as expected for the complex scenario (2 minutes window size)"

    def test_assumption_1(self):
        "Test the assumption 1 - interval is exclusive start and inclusive ending."
        result = average_delivery_time_by_minute(parse_stream("inputoutput/assumption-1/input.json"), 10)
        expected = load_json("inputoutput/assumption-1/10-expected-output.json")
        assert result == expected, "Result not as expected for the assumption 1 scenario (10 minutes window size)"


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
