#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict
from datetime import datetime

parser = argparse.ArgumentParser(
    description="Once you downloaded your soup already, let's play with it",
    epilog="Thank you for the decade of posting the best content."
)
parser.add_argument(
    "-o",
    "--output",
    default="%s.json",
    help="JSON file path pattern, applied to the soup name you give me"
)
parser.add_argument(
    dest="url",
    help="It's more like what you used to download it"
)

# TODO: do cool things in a way that doesn't look like a 12-year old wrote it
# Use pandas for playing with the data easier
if __name__ == '__main__':
    args = parser.parse_args()
    base_url = args.url
    url = base_url
    filename = args.output % args.url
    with open(filename, 'r') as fp:
        chunks = json.load(fp)

    print("%s has %s pages of content" % (url, len(chunks.keys())))
    posts_by_date = defaultdict(dict)
    total = 0
    for since, chunk in chunks.items():
        for post in chunk['posts']:
            when = post['timestamp']
            if when != '?':
                ts = datetime.strptime(when, '%b %d %Y %H:%M:%S UTC')
                posts_by_date[ts.year]['total'] = (posts_by_date[ts.year].get('total', 0)) + 1
            total += 1
    print("%s post count by year:" % url)
    for year in sorted(posts_by_date.keys()):
        print("%s - %s posts" % (year, posts_by_date[year]['total']))
    print("Total: %d" % total)