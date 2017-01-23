#!/usr/bin/env python

import sys
import json
import argparse
import datetime

import matplotlib.pyplot as plt


class ArgParser(argparse.ArgumentParser):
    """
    Argument parser that displays help on error
    """

    def error(self, message):
        sys.stderr.write("error: {}\n".format(message))
        self.print_help()
        sys.exit(2)


def parse(file):
    result = []
    for line in file:
        if line[0] == "{":
            result.append(json.loads(line))
    return result


def select_ts(event, type, ts):
    if type not in event:
        return ts

    if type == "task_started":
        return min(event[type], ts)
    else:
        return max(event[type], ts)


def extract_plot_data(intervals):
    tuples = ((v["id"], v["start"], v["start"] + v["duration"])
              for v in intervals.values())
    sorted_tuples = sorted(tuples, key=lambda x: (x[1:]))
    return zip(*sorted_tuples)


def plot(intervals, output):
    labels, start, end = extract_plot_data(intervals)
    plt.hlines(range(len(labels)), start, end, lw=2)
    plt.yticks(range(len(labels)), labels)
    ax = plt.gca()
    ax.set_xlabel("time (s)")
    ax.set_title("Deployment timeline")
    plt.tight_layout()
    plt.savefig(output)


def extract_intervals(input):
    times = {}
    events = parse(input)
    for event in events:
        event_type = event.get("event_type", "")
        if event_type not in {"task_started", "task_succeeded"}:
            continue

        if event.get("context", {}).get("node_id", "") == "":
            continue

        node_id = event["context"]["node_id"]
        ts = datetime.datetime.strptime(event["timestamp"].split("+")[0],
                                        "%Y-%m-%d %H:%M:%S.%f")
        event_data = times.get(node_id, dict(id=node_id))
        event_data[event_type] = select_ts(event_data, event_type, ts)
        times[node_id] = event_data
    return times


def relativize_intervals(intervals):
    start = intervals.values()[0]["task_started"]

    for interval in intervals.values():
        delta = interval["task_succeeded"] - interval["task_started"]
        interval["duration"] = delta.total_seconds()
        start = min(start, interval["task_started"])

    for interval in intervals.values():
        interval["start"] = (interval["task_started"] - start).total_seconds()


def main(input, output):
    intervals = extract_intervals(input)
    relativize_intervals(intervals)
    plot(intervals, output)


if __name__ == "__main__":
    parser = ArgParser(description="Visualize deployment flow")
    parser.add_argument("input", help="Cloudify log dump to visualize",
                        type=argparse.FileType("r"))
    parser.add_argument("output", help="Output image")
    args = parser.parse_args()

    main(args.input, args.output)
