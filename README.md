# downsouper

So that when soup.io hits rock bottom, you don't have to.
 
After 11 years on soup.io, I am losing the portal that connected me to so many beautiful people and made me have some actual friends. I am a hoarded here. I don't wanna lose everything.  

This made me try to hack this script together super fast in one evening of despair and sadness.

This tool also got me banned for debugging :( So be careful.

### Whatizit

This is a python tool to back up your soup.io account, by creating a comprehensive JSON archive of well-formed, parsed, trash-free list of your posts and their metadata.

It will collect their publication time, content, who it was reposted from, etc.

**Generating a dump of 10 years of soup will take about 12 hours...** It also took 48 MB of JSON, and one post from 2013, somehow, is "broken" because it has very different HTML layout.

### Missing features

* Once we get the dump, it should be able to download all attachments
* Configurable retries?
* Converting it later to an export format other services will understand; honestly I'm good with just not losing the data for now.
* Dumping friends and followers list </3...

### Usage

* You need python 3
* Install requirements in a virtualenv:

  ```shell script
  python -m virtualenv .env 
  source .env/bin/activate  
  pip install -r requirements.txt
  ```
  
* Check usage:

```shell script
python -m downsouper.download -c ikari.soup.io
```

You can check what options *want to* be supported (not necessarily are):

```shell script
# python -m downsouper.download --help
usage: download.py [-h] [-a] [-o OUTPUT] [-r RETRIES] [-c] url

The tool to download soup before it's down

positional arguments:
  url

optional arguments:
  -h, --help            show this help message and exit
  -a, --attachments     Download attachments
  -o OUTPUT, --output OUTPUT
                        Output JSON file path/name, where the data will be
                        stored
  -r RETRIES, --retries RETRIES
                        How many times to retry if there's a 50X error
                        (defaults to 0, forever)
  -c, --continue        Detect oldest 'since' in output file and add older
                        entries

I'm sorry.
```

### Example JSON output posts

The examples here are stripped down to the most interesting fields.

#### Image

```json
  {
    "kind": "image",
    "source": [
      {
        "url": "https://parkaboy.soup.io/post/656261571/Image",
        "author": "parkaboy"
      },
      {
        "url": "https://kundel.soup.io/post/658268509/Image",
        "author": "kundel"
      }
    ],
    "permalink": "https://ikari.soup.io/post/658270875/Image",
    "title": "(Image)",
    "is_repost": true,
    "id": "post658270875",
    "timestamp": "Jun 20 2018 12:48:37 UTC",
    "content": {
      "full_res_images": [
        "https://asset.soup.io/asset/14385/6111_ca55.jpeg"
      ],
      "images": [
        {
          "width": 539,
          "src": "https://asset.soup.io/asset/14385/6111_ca55.jpeg",
          "ratio": 0.9472759226713533,
          "height": 569
        }
      ]
    }
  }
```

#### quote
```json
{
  "kind": "quote",
  "source": [
    {
      "url": "https://fajnychnielubie.soup.io/post/658082306/I-write-differently-from-what-I-speak",
      "author": "fajnychnielubie"
    }
  ],
  "is_repost": true,
  "timestamp": "Jun 19 2018 10:25:45 UTC",
  "content": {
    "images": [],
    "body": " I write differently from what I speak, I speak differently from what I think, I think differently from the way I ought to think, and so it all proceeds into deepest darkness.\n",
    "cite": "\u2014 Kafka, Letters to Ottla and the Family"
  }
}
```

#### reaction

```json
  {
    "kind": "regular",
    "permalink": "https://ikari.soup.io/post/679864405/let-me-just-lay-here-with-the",
    "author": "ikari",
    "id": "post679864405",
    "original_post": {
      "url": "https://my-great-inspirations.soup.io/post/676707442/Image",
      "author": "my-great-inspirations"
    },
    "timestamp": "Feb 05 2020 21:06:00 UTC",
    "content": {
      "body": " let me just... lay here... with the books\n",
      "images": []
    },
    "is_reaction": true
  }
```


## Bash tips and tricks when features are missing

So I figured: what if I want to make my soup preserved, but for my fav pornsoup I'm ok with just the files?


Install `jq` for fancy json querying, then:

```bash
# getting all video urls from a dump
cat souporn.soup.io.json | jq -r "keys[] as \$k | .[(\$k)].posts[].content.video[0].src" | grep -vP "^null$"
```
---
Go a step further and download all the videos:
```bash
mkdir porn
cd porn
cat ../souporn.soup.io.json | jq -r "keys[] as \$k | .[(\$k)].posts[].content.video[0].src" | grep -vP "^null$" | xargs wget -nc
```
---

Download all images in their full size (notice the script drops the _xxx resizing suffix and puts a nice full size images list when possible when making the soup dump)

```bash
mkdir porn
cd porn
cat ../souporn.soup.io.json | jq -r "keys[] as \$k | .[(\$k)].posts[].content.full_res_images[]?" | grep -vP "^null$" | xargs wget -nc 
```

Be careful, it will take a lot of space. Dump of images from ikari.soup.io takes 19GiB of disk space. 
