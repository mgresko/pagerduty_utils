#!/usr/bin/env python

import argparse
import operator
from datetime import datetime, timedelta
from collections import defaultdict

import requests
from dateutil.parser import parse


def format_date(date):
    return date.strftime("%Y-%m-%d")


def get_entries(token, schedule, since, until):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Token token={}'.format(token),
        'Accept': 'application/vnd.pagerduty+json;version=2'
    }
    payload = {
        'since': format_date(since),
        'until': format_date(until),
        'schedule_ids[]': schedule
    }
    url = 'https://api.pagerduty.com/oncalls'
    return requests.get(url, params=payload, headers=headers).json()


def get_diff_minutes(start, end, since, until):
    start = (start if datetime.combine(start.date(), start.time()) >
             datetime.combine(since.date(), since.time()) else since)
    end = (end if datetime.combine(end.date(), end.time()) <
           datetime.combine(until.date(), until.time()) else until)
    diff = (datetime.combine(end.date(), end.time()) -
            datetime.combine(start.date(), start.time()))
    return int(diff.total_seconds() / 60)


def process_entries(entries, token, since, until):
    """
    process entries into user buckets
    """
    buckets = defaultdict(int)
    for data in entries:
        email = get_user(data['user']['id'], token)
        start = parse(data['start'])
        end = parse(data['end'])
        minutes = get_diff_minutes(start, end, since, until)
        buckets[email] += minutes
    return buckets


def get_user(user_id, token):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Token token={}'.format(token),
        'Accept': 'application/vnd.pagerduty+json;version=2'
    }
    url = 'https://api.pagerduty.com/users/{}'.format(user_id)
    return requests.get(url, headers=headers).json()['user']['email']


def parse_options():
    """
    Parse command line options
    """
    parser = argparse.ArgumentParser(description='What % of time do I spend '
                                     'oncall?')
    parser.add_argument('--schedule', '-s', dest='schedule', action='store',
                        type=str, required=True)
    parser.add_argument('--api-token', '-a', dest='token', action='store',
                        type=str, required=True, help='v2 API key')
    parser.add_argument('--start', dest='start', action='store', type=int,
                        help='number of days ago to start', default=1)
    parser.add_argument('--stop', dest='stop', action='store', type=int,
                        help='number of days ago to stop', default=0)
    return parser.parse_args()


def main():
    # parse options
    options = parse_options()

    since = datetime.now() - timedelta(days=options.start)
    if options.stop > 0:
        until = datetime.now() - timedelta(days=options.stop)
    else:
        until = datetime.now()
    total_minutes = get_diff_minutes(since, until, since, until)

    # pagerduty entries
    entries = get_entries(options.token, options.schedule, since,
                          until)['oncalls']
    # user, minutes dictionary
    buckets = process_entries(entries, options.token, since, until)
    # sort the bucket, highest first
    sorted_buckets = sorted(dict(buckets).iteritems(),
                            key=operator.itemgetter(1), reverse=True)

    print "Total Minutes: {}\n".format(str(total_minutes))
    # print % of total time oncall
    for name, minutes in sorted_buckets:
        percent = float(minutes) / float(total_minutes)
        print "{}: {:.2%}".format(name, percent)


if __name__ == '__main__':
    main()
