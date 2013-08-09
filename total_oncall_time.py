import argparse
import operator
from datetime import datetime, timedelta
from collections import defaultdict

import requests
from dateutil.parser import parse


def format_date(date):
    return date.strftime("%Y-%m-%d")


def get_entries(token, schedule, site, since, until):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Token token={}'.format(token)
    }
    payload = {
        'since': format_date(since),
        'until': format_date(until)
    }
    url = 'https://{}.pagerduty.com/api/v1/schedules/{}/entries'.format(
            site, schedule
    )
    return requests.get(url, params=payload, headers=headers).json()


def get_diff_minutes(since, until):
    diff = until - since
    return int(diff.total_seconds() / 60)


def process_entries(entries):
    """
    process entries into user buckets
    """
    buckets = defaultdict(int)
    for data in entries:
        email = data['user']['email']
        start = parse(data['start'])
        end = parse(data['end'])
        minutes = get_diff_minutes(start, end)
        buckets[email] += minutes
    return buckets


def parse_options():
    """
    Parse command line options
    """
    parser = argparse.ArgumentParser(description='What % of time do I spend oncall?')
    parser.add_argument('--schedule', '-s', dest='schedule', action='store',
                        type=str, required=True)
    parser.add_argument('--pd-site', '-p', dest='site', action='store',
                        type=str, required=True)
    parser.add_argument('--api-token', '-a', dest='token', action='store',
                        type=str, required=True)
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
    total_minutes = get_diff_minutes(since, until)

    # pagerduty entries
    entries = get_entries(options.token, options.schedule, options.site,
                since, until)['entries']
    # user, minutes dictionary
    buckets = process_entries(entries)
    # sort the bucket, highest first
    sorted_buckets = sorted(dict(buckets).iteritems(), key=operator.itemgetter(1), reverse=True)

    print "Total Minutes: {}\n".format(str(total_minutes))
    # print % of total time oncall
    for name, minutes in sorted_buckets:
        percent = float(minutes) / float(total_minutes)
        print "{}: {:.2%}".format(name, percent)
        


if __name__ == '__main__':
    main()
