# Backend Engineering Challenge (Solution)

## Running

This project was implemented using python 3.11.3 and [pdm package manager](https://github.com/pdm-project/pdm) - also helps with virtual environment management. There is **no need to install pdm** as only one non-builtin library was used, `ijson`. So, to setup, just simply install it in one of the following ways:
```shell
pip install ijson  # way 1
pip install -r requirements.txt  # way 2

pdm install  # with pdm - optional
```

Then to run, simply run the `main.py` file with your arguments.

Example:
```shell
python main.py --input_file tests/inputoutput/example/input.json --window_size 10
```

You can see more information about the arguments by using the following command.
```shell
python main.py --help
```

## Assumptions

1. When in the scenario it is said "(...) calculating, for every minute, a moving average of the translation delivery time for the last X minutes", if the minute being considered is the _minute 20_ and _X (`window_size`) is equal to 10_ and there is an event with the timestamp *10m00.000s* and an event with *20m00.000s*, **only** the event with the timestamp *20m00.000s* will be considered - Interval exclusive at the start and inclusive at the end. (Check `test_assumption_1` test in [test.py](test.py))
2. The **first line** of the output will always include an average delivery time of zero with the date of the last minute with this value before a relevant value appears. As for the **last line**, it will be first line where the last event contributes for the average of the minute. 

## Testing

There are a few input examples in the [inputoutput folder](./inputoutput) that were created manually with some special scenarios that I thought worth testing or were unique to some extent. These are used when running the tests of the [test.py file](test.py) which you can do by running the following command:

```shell
python -m unittest test.py
```

### Results 

Some of these tests were actually generated to _stress test_ the program. This means that their actual result isn't verified, just its performace is considered. These are located in `inputoutput/big-*` and are generated automatically in the test `setUpClass` fixture using the [gen.py file](inputoutput/gen.py). The following results were obtained when running these _stress tests_ in my machine (Macbook M1Pro 16GB RAM):

| # Events    | Window Size | Elapsed Time | Old Version | Improvement |
| ----------- | ----------- | ------------ | ----------- | ----------- |
| 3 (example) | 10          | 1ms          | 1ms         | x1          |
| 1 000       | 10          | 28ms         | 33ms        | x1.18       |
| 10 000      | 10          | 263ms        | 1s700ms     | x6.46       |
| 100 000     | 10          | 2s736ms      | 3m03s       | x66.9       |
| 100 000     | 1           | 2s255ms      | 2m52s       | x76.3       |
| 100 000     | 100         | 3s183ms      | 2m55s       | x55.0       |
| 1 000 000   | 10          | 29s303ms     | -           | -           |

**PS**: The old version is located in the [old-version branch](https://github.com/rickerp/unbabel-backend-engineering-challenge/tree/old-version). The improvement is calculated by dividing the old version's elapsed time by the new version's elapsed time. (e.g. 33ms / 28ms = 1.18x faster

## Analysis 

The comparison clearly shows that the new version is significantly faster than the old one. The old version used a simple minute-by-minute iteration from the first to the last timestamp, checking a list of events each time to see if they fell within the window interval. After that, it checked the window interval event list for events that were no longer within the window interval. This process was quite slow, especially as the number of events increased. This was due to various reasons, one of which was that the input JSON file was being loaded entirely into memory at the start.

On the other hand, the new version adopts a different approach. It reads one event at a time, using a Python generator to yield it, and then processes it in the main function. This approach significantly reduces memory usage and time complexity because the events are processed as they are read, without repeating a minute timestamp, as the events are ordered by timestamp.


## Relevant Files
```shell
├── inputoutput 	# Input and outputs examples used for testing
│   ├── big-... 	# These are big examples which are only generated once the stress tests are ran
│   ├── gen.py 		# Generator for input examples
│   └── ...			# Other examples created manually
├── main.py		 # Main file
└── test.py		 # Test file
```

## Challenge Introduction

Welcome to our Engineering Challenge repository 🖖

If you found this repository it probably means that you are participating in our recruitment process. Thank you for your time and energy. If that's not the case please take a look at our [openings](https://unbabel.com/careers/) and apply!

Please fork this repo before you start working on the challenge, read it careful and take your time and think about the solution. Also, please fork this repository because we will evaluate the code on the fork.

This is an opportunity for us both to work together and get to know each other in a more technical way. If you have any questions please open and issue and we'll reach out to help.

Good luck!

## Challenge Scenario

At Unbabel we deal with a lot of translation data. One of the metrics we use for our clients' SLAs is the delivery time of a translation. 

In the context of this problem, and to keep things simple, our translation flow is going to be modeled as only one event.

### *translation_delivered*

Example:

```json
{
	"timestamp": "2018-12-26 18:12:19.903159",
	"translation_id": "5aa5b2f39f7254a75aa4",
	"source_language": "en",
	"target_language": "fr",
	"client_name": "airliberty",
	"event_name": "translation_delivered",
	"duration": 20,
	"nr_words": 100
}
```

## Challenge Objective

Your mission is to build a simple command line application that parses a stream of events and produces an aggregated output. In this case, we're interested in calculating, for every minute, a moving average of the translation delivery time for the last X minutes.

If we want to count, for each minute, the moving average delivery time of all translations for the past 10 minutes we would call your application like (feel free to name it anything you like!).

	unbabel_cli --input_file events.json --window_size 10
	
The input file format would be something like:

	{"timestamp": "2018-12-26 18:11:08.509654","translation_id": "5aa5b2f39f7254a75aa5","source_language": "en","target_language": "fr","client_name": "airliberty","event_name": "translation_delivered","nr_words": 30, "duration": 20}
	{"timestamp": "2018-12-26 18:15:19.903159","translation_id": "5aa5b2f39f7254a75aa4","source_language": "en","target_language": "fr","client_name": "airliberty","event_name": "translation_delivered","nr_words": 30, "duration": 31}
	{"timestamp": "2018-12-26 18:23:19.903159","translation_id": "5aa5b2f39f7254a75bb3","source_language": "en","target_language": "fr","client_name": "taxi-eats","event_name": "translation_delivered","nr_words": 100, "duration": 54}

Assume that the lines in the input are ordered by the `timestamp` key, from lower (oldest) to higher values, just like in the example input above.

The output file would be something in the following format.

```
{"date": "2018-12-26 18:11:00", "average_delivery_time": 0}
{"date": "2018-12-26 18:12:00", "average_delivery_time": 20}
{"date": "2018-12-26 18:13:00", "average_delivery_time": 20}
{"date": "2018-12-26 18:14:00", "average_delivery_time": 20}
{"date": "2018-12-26 18:15:00", "average_delivery_time": 20}
{"date": "2018-12-26 18:16:00", "average_delivery_time": 25.5}
{"date": "2018-12-26 18:17:00", "average_delivery_time": 25.5}
{"date": "2018-12-26 18:18:00", "average_delivery_time": 25.5}
{"date": "2018-12-26 18:19:00", "average_delivery_time": 25.5}
{"date": "2018-12-26 18:20:00", "average_delivery_time": 25.5}
{"date": "2018-12-26 18:21:00", "average_delivery_time": 25.5}
{"date": "2018-12-26 18:22:00", "average_delivery_time": 31}
{"date": "2018-12-26 18:23:00", "average_delivery_time": 31}
{"date": "2018-12-26 18:24:00", "average_delivery_time": 42.5}
```

#### Notes

Before jumping right into implementation we advise you to think about the solution first. We will evaluate, not only if your solution works but also the following aspects:

+ Simple and easy to read code. Remember that [simple is not easy](https://www.infoq.com/presentations/Simple-Made-Easy)
+ Comment your code. The easier it is to understand the complex parts, the faster and more positive the feedback will be
+ Consider the optimizations you can do, given the order of the input lines
+ Include a README.md that briefly describes how to build and run your code, as well as how to **test it**
+ Be consistent in your code. 

Feel free to, in your solution, include some your considerations while doing this challenge. We want you to solve this challenge in the language you feel most comfortable with. Our machines run Python (3.7.x or higher) or Go (1.16.x or higher). If you are thinking of using any other programming language please reach out to us first 🙏.

Also, if you have any problem please **open an issue**. 

Good luck and may the force be with you
