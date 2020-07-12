#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import json
import math
import os
import sys
from time import sleep
import requests
import re
from .souparser import parse_soup, parse_int, parse_unknown_post

MORE_SINCE = re.compile(r'/since/(\d+)(\?mode=own)?')

# ...
parser = argparse.ArgumentParser(
    description="The tool to download soup before it's down",
    epilog="I'm sorry."
)
parser.add_argument(
    "-a",
    "--attachments",
    dest="attachments",
    action="store_true",
    help="Download attachments"
)
parser.add_argument(
    "-o",
    "--output",
    default="%s.json",
    help="Output JSON file path/name, where the data will be stored"
)
parser.add_argument(
    "-n",
    "--new",
    dest="newposts",
    help="Find new posts too (new since last dump)",
    action="store_true"
)
parser.add_argument(
    "-c",
    "--continue",
    dest="cont",
    help="Detect oldest 'since' in output file and add older entries",
    action="store_true"
)
parser.add_argument(
    "-f",
    "--fix",
    dest="fix",
    help="Fix the entries that have been previously been downloaded as 'unknown'.",
    action="store_true"
)
parser.add_argument(
    dest="url"
)

def fix_chunk(chunk):
    fixed = []
    for post in chunk.get('posts', []):
        fixed.append(parse_unknown_post(post))
    chunk['posts'] = fixed
    return chunk

if __name__ == '__main__':
    args = parser.parse_args()
    base_url = args.url
    if not (base_url.startswith("http://") or base_url.startswith("https://")):
        base_url = "http://" + base_url
    url = base_url

    chunks = {}
    chunk_key = "latest"
    data = None
    filename = args.output % args.url
    filename_temp = filename + '-incomplete'

    if args.cont or args.fix:
        # fix and continuation mode require reopening last file
        with open(filename, 'r') as fp:
            chunks = json.load(fp)
            lowest = math.inf
            highest = 0
            for k in chunks.keys():
                i = parse_int(k)
                if isinstance(i, int):
                    lowest = min(i, lowest)
                    highest = max(i, highest)
                    if args.fix:
                        chunks[k] = fix_chunk(chunks[k])
        if lowest == math.inf:
            print("Nothing to continue.")
            sys.exit(1)
        else:
            if args.cont:
                print("Getting post %s and older" % lowest)
                chunk_key = lowest
                url = base_url + ('/since/%s?mode=own' % lowest)
            else:
                print("Nothing more to fix. Writing.")
                with open(filename_temp, 'w') as fp:
                    json.dump(chunks, fp, indent=2)
                os.rename(filename_temp, filename)
                sys.exit(0)

    while data is None and url is not None:
        print("Downloading %s" % url)
        try:
            b = requests.get(url)
            print("Status: %s ; Elapsed: %s ; Got %s bytes" % (b.status_code, b.elapsed, len(b.text)))
            if b.status_code == 200:
                typ = b.headers.get('content-type', '')
                if typ.startswith('text/html'):
                    html = b.text
                    data = parse_soup(html)
                    chunks[chunk_key] = data
                    if data['more']:
                        m = MORE_SINCE.match(data['more'])
                        if m:
                            # next chunk will be XYZ from /since/XYZ?mode=own
                            chunk_key = m.group(1)
                        url = base_url + data['more']
                        print("Next page is: %s (since %s). Sleeping 1s" % (url, chunk_key))
                    else:
                        print("We are DONE!!! 🎉🥳 THIS WAS THE LAST PAGE!")
                        url = None
                    with open(filename_temp, 'w') as fp:
                        json.dump(chunks, fp, indent=2)
                        data = None
                    os.remove(filename)
                    os.rename(filename_temp, filename)
                    sleep(1)

            elif b.status_code == 429:
                # too many requests
                print("Throttled. Sleeping 4 hours...")
                sleep(4*60*60)
                print("Woken up. Retrying now.")
            elif b.status_code > 500:
                print("Got a %s error code, waiting 10 seconds..." % b.status_code)
                sleep(10)
                print("Woken up. Retrying now.")
        except ConnectionError as err:
            print("Received the following error: %s" % err)
            sleep(10)
            print("Retrying...?")
