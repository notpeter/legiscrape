import argparse
import logging
import json
from urllib.parse import parse_qsl, urlsplit

import requests
from legiscrape.video import es_search, remux, get
from legiscrape.captions import Teletext

def main():
    parser = argparse.ArgumentParser(description="Granicus video downloader")
    parser.add_argument("file", help="MP4 Output filename",
                        nargs='?', default="agency_clipid.mp4")
    parser.add_argument("url", help="Granicus Media Player full URL. Ex: http://oakland.granicus.com/MediaPlayer.php?view_id=2&clip_id=2147)")
    parser.add_argument('-v', '--verbose', action='count', default=0)
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    if args.file == 'agency_clipid.mp4':
        clip_id = dict(parse_qsl(urlsplit(args.url).query)).get('clip_id', 'clip')
        agency = urlsplit(args.url).netloc.replace('.granicus.com', '')
        args.file = "%s_%s.mp4" % (agency, clip_id)

    url = urlsplit(args.url)
    # ES index = subdomain.granicus.com
    es_index = url.netloc
    clip_id = dict(parse_qsl(url.query))['clip_id']
    video_url = es_search(es_index, clip_id)
    logging.info("Fetching Video MP4 %s", video_url)
    local_mp4 = get(video_url, args.file)

    try:
        # subtitle_url = "http://oakland.granicus.com/videos/%s/captions.vtt" % clip_id
        subtitle_url = "http://oakland.granicus.com/JSON.php?clip_id=%s" % clip_id
        logging.info("Fetching Subtitle from %s", subtitle_url)
        response = requests.get(subtitle_url)
        subtitle_json = json.loads(response.text)
        ttxt = Teletext(subtitle_json)
        # This creates SRT, WEBVTT, Chapters, etc.
        ttxt.export(args.file)
    except:
        logging.error("Error downloading subtitles. Skipping...", exc_info=True)

    remux(local_mp4, "%s_FINAL.mp4" % args.file,
          chapter_filename='%s.chapters.txt' % local_mp4,
          srt_filename='%s.vrt' % local_mp4)

if __name__ == '__main__':
    main()
