import json
import sys
from collections import defaultdict
from copy import deepcopy

from bs4 import BeautifulSoup
import re

POST_KIND = re.compile(r'^post[-_]([a-z]+)$')
IMAGE_RESIZEABLE = re.compile(r'([a-z0-9]{4}_[a-z0-9]{4})_[a-z0-9]{3}')


def parse_soup(html):
    print("Parsing %s bytes" % len(html))
    soup = BeautifulSoup(html, 'html.parser')
    meta = {
        "title": soup.title.string,
        "description": soup.head.select_one('meta[name="description"]').get('content')
    }
    posts_div = soup.select_one("#posts")
    posts = posts_div.select(".post")
    more_link = soup.select_one("a.more")
    posts_list = [post_to_json(post) for post in posts] if posts else []
    return {
        "meta": meta,
        "posts": posts_list,
        "more": more_link.get('href') if more_link else None
    }


def parse_int(str_maybe):
    try:
        return int(str_maybe)
    except ValueError:
        return str_maybe


def post_to_json(post):
    meta = extract_post_meta(post)
    content = post.select_one('.content')
    if not content:
        print("Old format post! Results might be a little broken")
        content = post
    content_json = extract_content(meta, content)

    post_json = meta
    post_json.update({
        "id": post.attrs.get('id'),
        "content": content_json
    })
    return post_json


def parse_unknown_post(post):
    if 'unknown' not in post['content']:
        return post
    # otherwise this was not a supported kind of post the last time we ran the export
    content = BeautifulSoup(post['content']['unknown'])
    fixed = deepcopy(post)
    fixed['content'] = extract_content(post, content)
    if fixed != post:
        print("A post was fixed and parsed in a new way. It's not unknown, it's %s" % fixed['content'].keys())
        print(json.dumps(fixed, indent=2))
    return fixed


def extract_content(meta, content):
    images = content.select('.imagecontainer img')
    videos = content.select('video')
    caption = content.select_one('.caption')
    content_json = {
        "images": [{"src": img.get('src'),
                    "width": parse_int(img.get('width', None)),
                    "height": parse_int(img.get('height', None))} for img
                   in images] if images else [],
    }
    for img in content_json['images']:
        full_res_images = []
        if img['src'].startswith('https://asset'):
            full_res_images.append(IMAGE_RESIZEABLE.sub('\\1', img['src']))
        else:
            full_res_images.append(img)
        if img['width'] and img['height']:
            # store aspect ratio to be happier
            img['ratio'] = img['width'] / img['height']
        content_json['full_res_images'] = full_res_images
    if caption:
        # some old captions (2013 and earlier) don't have links...
        # they are actual captions, apparently
        caption_link = caption.select_one('a')
        if not caption_link:
            content_json['cite'] = caption.text.strip()
            print("! skipping source_link as it seems a source cite: %s" % content_json['cite'])
        else:
            content_json['source_link'] = caption_link.get('href')
    if videos:
        content_json['video'] = [{
            "src": video.get('src'),
            "width": video.get('width', None),
            "height": video.get('height', None)
        } for video in videos]
    descr = content.select_one('.description')
    if descr:
        content_json['description'] = descr.encode_contents(2, 'utf-8').decode()
    body = content.select_one('.body')
    if body:
        content_json['body'] = body.encode_contents(2, 'utf-8').decode()
    if meta['kind'] == 'quote':
        # this is likely a tumblr-imported post
        # it has a .body, already extracted, and may have a source (cite)
        cite = content.select_one('cite')
        content_json['cite'] = cite.text.strip() if cite else None
    if meta['kind'] == 'link':
        link = content.select_one('h3 a')
        if link:
            content_json['link'] = {
                "url": link.get('href'),
                "title": link.text
            }
        # links can have a full post body too, but this is covered by .body already
    if meta['kind'] not in ('image', 'regular', 'video', 'quote', 'link'):
        content_json['unknown'] = content.encode_contents(2, 'utf-8').decode()
    return content_json


def extract_post_meta(post):
    meta = defaultdict(None)

    classes = post.attrs.get('class', [])
    meta['is_reaction'] = 'post_reaction' in classes
    meta['is_repost'] = 'post_repost' in classes
    meta['is_nsfw'] = 'f_nsfw' in classes
    meta['own'] = 'author-self' in classes
    meta['kind'] = 'unknown'
    meta['original_post'] = None
    meta['permalink'] = None
    meta['title'] = None
    meta['author'] = None
    meta['author_url'] = None
    for klass in post.attrs.get('class', []):
        m = POST_KIND.match(klass)
        if m:
            # does it look like a post type? (overkill with regex, I know)
            maybe_kind = m.group(1)
            # don't let reaction flag override post type
            if maybe_kind not in ('reaction', 'repost'):
                meta['kind'] = maybe_kind

    # if it's a reaction, what was the original post?
    # TODO: discussions?
    if meta['is_reaction']:
        original = post.select_one('a.original_link')
        meta['original_post'] = {
            "author": original.select_one('.user_container .name').text,
            "url": original.get('href')
        }

    # get permalink and title from the post icon, or from '#' if this fails
    post_icon = post.select_one('.icon.type a')
    if post_icon:
        meta['permalink'] = post_icon.get('href')
        meta['title'] = post_icon.get('title')
    if not meta['permalink']:
        perma = post.select_one('.permalink a')
        if perma:
            meta['permalink'] = perma.get('href')
        else:
            print("! missing permalink for post?")

    # get post author (soup owner in most cases) info
    author_icon = post.select_one('.icon.author')
    if author_icon:
        meta['author'] = author_icon.select_one('.user_container img').get('alt')
        meta['author_url'] = author_icon.select_one('.url').get('href')

    # get timestamp from the microformat tag (if user enabled it)
    time = post.select_one('.time abbr')
    if time:
        meta['timestamp'] = time.get('title')
    else:
        meta['timestamp'] = '?'

    # for reposts,
    # source is either one item (of url+author) - reposted from
    # or two items - reposted from [0] via [1]
    # --
    # for 'original' posts, source contains a list of reposters
    source = post.select_one('.source')
    if source:
        if 'reposted_by' in source.attrs['class']:
            meta['reposted_by'] = [source_url.select_one('img.photo').get('alt')
                                   for source_url in source.select('.url')]
        else:
            meta['source'] = [{
                "url": source_url.get('href'),
                "author": source_url.select_one('img.photo').get('alt')
            } for source_url in source.select('.url')]
    else:
        meta['source'] = None
    return meta
