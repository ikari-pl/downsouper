#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import json
import math
import os
import re
import sys
from time import sleep

import requests

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


def get_post_ids(chunk):
    ids = set()
    for post in chunk['posts']:
        if not post['id']:
            print("Post has no id: ", post)
            continue
        # in my dump, two were marked as "mutlipost"
        # but soup never replied the same when I debugged it
        id = parse_int(post['id'].replace('multipost', '').replace('post', ''))
        if id:
            if not isinstance(id, int):
                print('Post id is not int: "%s"' % id)
                print(post)
            ids.add(id)
        else:
            print("Warning: weird post id %s" % post['id'])
    return ids


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
    known_post_ids = set()

    if args.cont or args.fix or args.newposts:
        # fix, new  and continuation mode require reopening last file
        with open(filename, 'r') as fp:
            chunks = json.load(fp)
            lowest = math.inf
            highest = 0
            for k, chunk in chunks.items():
                ids = get_post_ids(chunk)
                # add to known posts, to avoid duplicates
                known_post_ids |= ids
                # global min and max of post ids
                lowest = min(min(ids), lowest)
                highest = max(max(ids), highest)
                if args.fix:
                    chunks[k] = fix_chunk(chunk)
        if lowest == math.inf:
            print("Nothing to continue.")
            sys.exit(1)
        else:
            if args.cont:
                print("Getting post %s and older" % lowest)
                chunk_key = lowest - 1
                url = base_url + ('/since/%s?mode=own' % lowest)
            elif args.fix:
                print("Nothing more to fix. Writing.")
                with open(filename_temp, 'w') as fp:
                    json.dump(chunks, fp, indent=2)
                os.rename(filename_temp, filename)
                sys.exit(0)
        if args.newposts:
            if highest == 0:
                print("Cannot find newer posts if we don't know any")
                sys.exit(1)
            # best guess on what the new chunk should be
            url = base_url + ('/since/%s?mode=own' % (highest + 1000))

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

                    # filter duplicates, especially if we're looking for new posts
                    new_ids = get_post_ids(data)
                    dups = known_post_ids & new_ids
                    if len(dups) > 0:
                        print("%s posts are already known and will be skipped" % len(dups))
                        if len(dups) == len(new_ids):
                            print("All these are known, nothing left to do.")
                            url = None
                            data['more'] = None # don't go further
                        data['posts'] = [post for post in data['posts'] if
                                         parse_int(post['id'].replace('multipost', '').replace('post', '')) not in dups]

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
                    if os.path.exists(filename):
                        # windows needs this
                        os.remove(filename)
                    os.rename(filename_temp, filename)
                    sleep(1)

            elif b.status_code == 429:
                # too many requests
                print("Throttled. Sleeping 4 hours...")
                sleep(4 * 60 * 60)
                print("Woken up. Retrying now.")
            elif b.status_code > 500:
                print("Got a %s error code, waiting 10 seconds..." % b.status_code)
                sleep(10)
                print("Woken up. Retrying now.")
        except ConnectionError as err:
            print("Received the following error: %s" % err)
            sleep(10)
            print("Retrying...?")
