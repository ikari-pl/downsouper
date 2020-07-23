# downsouper

So that when soup.io hits rock bottom, you don't have to.
 
After 11 years on soup.io, I am losing the portal that connected me to so many beautiful people and made me have some actual friends. I am a hoarded here. I don't wanna lose everything.  

This made me try to hack this script together super fast in one evening of despair and sadness.

**The output format of this script is supported by loforo.com without modifications; you will just have to share (host?) the files with them somehow, as of 23.07.2020 the JSON will be enough**. Example soup imported from this script's export: http://ikari.loforo.com/ 

### Whatizit

This is a python tool to back up your soup.io account, by creating a comprehensive JSON archive of well-formed, parsed, trash-free list of your posts and their metadata.

It will collect their publication time, content, who it was reposted from, etc.

**Generating a dump of 10 years of soup will take about 12 hours...** It also took 48 MB of JSON, and one post from 2013, somehow, is "broken" because it has very different HTML layout.

### Missing features

* Get reactions and what you reacted to (not just the links)
* Once we get the dump, it should be able to download all attachments; for now, use the shell commands provided (actually more reliable)
* Converting it later to an export format other services will understand; honestly I'm good with just not losing the data for now.
* Dumping friends and followers list </3...

### Usage

* You need python 3
* Install requirements in a virtualenv:

  ```shell script
  pip3 install virtualenv         # virtualenv is a python package to separate project and their requirements
  virtualenv -p python3 .env      # create one for this project
  source .env/bin/activate        # and use it
  pip install -r requirements.txt # and install the requirements (one is called BeautifulSoup)
  ```
  
* Check usage:

```shell script
python -m downsouper.download ikari.soup.io # use -c for continuing broken backups later
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

So I figured: what if I want to get the files as fast as possible?


Install `jq` for fancy json querying, then:

```bash
# getting all video urls from a dump
cat ikari.soup.io.json | jq -r "keys[] as \$k | .[(\$k)].posts[].content.video[0].src" | grep -vP "^null$"
```
---
Go a step further and download all the videos:
```bash
mkdir assets
cd assets
cat ../ikari.soup.io.json | jq -r "keys[] as \$k | .[(\$k)].posts[].content.video[0].src" | grep -vP "^null$" | xargs wget -nc
```
---

Download all images in their full size (notice the script drops the _xxx resizing suffix and puts a nice full size images list when possible when making the soup dump)

```bash
mkdir ikari
cd ikari
cat ../$(basename $(pwd)).soup.io.json | jq -r "keys[] as \$k | .[(\$k)].posts[].content.full_res_images[]?" | grep -vP "^null$" | xargs wget -nc 
```

Be careful, it will take a lot of space. Dump of images from ikari.soup.io takes 19GiB of disk space. 

# FAQ

1. **Why is the code so ugly?**
 
   Because I'm in a hurry. Need to download before soup gets DDoSed by the angry users. We have a week left only.

2. **I am getting error 429 and soup doesn't work**
    
   You got banned for making too many requests. Interestingly enough, this happens to me only if I open the web version of soup, not by testing the script. Turns out my browser makes a million retries on failing requests (and does so immediately). A buggy script or a browser extension would be to blame.
        
3. **I have the json, but I need the pictures**

   Download all the `full_size_image`, `video.src` and `audio.src` before soup goes down. On a fast connection, this worked suprisingly well (downloading 19 GB of my soup wasn't a problem on the server-side). You can do parallel requests.
   
4. **Why is it so slow?**

   It downloads your soup one page (screen) at a time, like you would with the browser. Each page takes 3-15 seconds to generate. Soup is under heavy stress now. My soup was 2151 pages long, which means 2151 requests, each taking ~10 seconds &emdash; should finish within 6 hours. In reality it took a little more.     
     
5. **How to convert it to Wordpress archive / tumblr??**

   Well, this is a problem to solve once we have the backup. It has enough metadata to do so.
   
6. **What's the file structure?**

   It's one huge JSON grouped into "chunks" which are exactly the pages as they loaded one by one. This also means adding new posts shifts EVERYTHING within the chunks. I tried to deal with it with the new `--newposts` option but it's not well tested at all.
   
   On the other side it helps group the results into smaller pages and was helping me continue from where it was interrupted previously easy. Each chunk ID relates to one `/since/{chunk}` request.
   
7. **What is `content.unkown`?**

   If a rare type of post appeared, I just dumped everything to be parseable later (with the `--fix` option).
   
8. **I cannot into computers, make it a button**

   I want to, but they didn't give us enough time. I can't right now. I have a job as well.
   
9. **Why are all timestamps `"?"`?**

   You have to enable showing them on your soup first, if you want them included.
   
   
## Update 2020-07-22: Pssst, it still works
(this entire section is stolen from a sister project [nathell/soupscraper](https://github.com/nathell/soupscraper/) )

Soup.io is officially <del>dead</del> in new hands now, but old servers haven’t been turned off yet. So apparently you still have a chance of backing up your soup.

Here’s how:

1. [Edit your hosts file](https://support.rackspace.com/how-to/modify-your-hosts-file/) ([instructions for macOS](https://www.imore.com/how-edit-your-macs-hosts-file-and-why-you-would-want)) and add the following entries:

```
45.153.143.247     soup.io
45.153.143.247     www.soup.io
45.153.143.247     YOURSOUP.soup.io
45.153.143.248     asset.soup.io
```

Put in your soup’s name in place of `YOURSOUP`.
