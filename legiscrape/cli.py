import argparse
import logging
import json
from urllib.parse import parse_qsl, urlsplit

import requests
from legiscrape.video import es_search, remux, get
from legiscrape.captions import Teletext

def main():
    parser = argparse.ArgumentParser(description="Granicus video downloader")
    parser.add_argument("filename", help="MP4 Output filename")
    parser.add_argument("url", help="Granicus Media Player full URL. Ex: http://oakland.granicus.com/MediaPlayer.php?view_id=2&clip_id=2147)")
    parser.add_argument('-v', '--verbose', action='count', default=0)
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    url = urlsplit(args.url)
    # ES index = subdomain.granicus.com
    es_index = url.netloc
    clip_id = dict(parse_qsl(url.query))['clip_id']
    video_url = es_search(es_index, clip_id)
    subtitle_url = "%s://%s/JSON.php?clip_id=%s" % (url.scheme, url.netloc, clip_id)

    logging.info("Fetching Video MP4 %s", video_url)
    local_mp4 = get(video_url)
    logging.info("Fetching JSON from %s", subtitle_url)
    response = requests.get(subtitle_url)
    json_data = json.loads(response.text)
    ttxt = Teletext(json_data, local_mp4)
    # This creates SRT, WEBVTT, Chapters, etc.
    ttxt.export()

    remux(local_mp4, args.filename,
          chapter_filename='%s.chapters.txt' % local_mp4,
          srt_filename='%s.srt' % local_mp4)

if __name__ == '__main__':
    main()
