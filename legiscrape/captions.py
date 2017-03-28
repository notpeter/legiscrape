#!/usr/bin/env python3
import argparse
import json
import html
import logging
import os
from urllib.parse import parse_qsl, urlsplit

import jsonschema
import requests


class Teletext(object):
    """Granicus Video JSON Closed Captions to WEBVTT/SRT"""
    # Granicus JSON subtitle format is array containing an array of objects
    # e.g. [ [ {obj1}, {obj2} ] ] where obj is either text or meta:
    # * Text: {"type": "text", "time": 352.332, "text": "Hello"}
    # * Meta: {"type": "meta", "time": 123.123, ...}

    def __init__(self, captions):
        filename = 'granicus-captions.schema.json'
        if os.path.dirname(__file__):
            filename = "%s/%s" % (os.path.dirname(__file__), filename)
        with open(filename) as json_schema:
            schema = json.load(json_schema)

        logging.info('Validating JSON...')
        # Raises ValidationError
        jsonschema.validate(captions, schema)
        self.captions = captions[0]
        # clean_title escapes invalid characters
        for sub in self.captions:
            sub['text'] = clean_title(sub['text'])
            if 'title' in sub:
                sub['title'] = clean_title(sub['title'])
        logging.info('Gathering metadata...')

    def export_json(self, filename):
        """Exports Granicus JSON file"""
        logging.info('Exporting JSON...')
        with open(filename, mode='wt') as output_file:
            json.dump(self.captions, output_file)

    def export_text_chapters(self, filename):
        """Exports chapters.txt file, e.g. "00:04:20,000 Chapter 1"""
        logging.info('Exporting chapters.txt...')
        metadata = []
        for sub in self.captions:
            if sub['type'] == 'meta':
                chapter_title = ' '.join(sub['title'].splitlines()[0].split())
                metadata.append((timecode(sub['time'], seperator=','), chapter_title))
        with open(filename, mode='wt') as output:
            for chapter in metadata:
                output.write("%s %s\n" % chapter)

    def export_webvtt_chapters(self, filename):
        """Exports chapters.vtt file, e.g. "00:00:00.000 --> 00:04:20.000\nChapter 1"""
        template = "\n".join(["%s", "%s --> %s", "%s"])
        logging.info('Exporting chapters.vtt...')
        metadata = []
        for sub in self.captions:
            if sub['type'] == 'meta':
                chapter_title = ' '.join(sub['title'].splitlines()[0].split())
                metadata.append((sub['time'], chapter_title))
        with open(filename, mode='wt') as output:
            output.write("WEBVTT\n\n")
            for chapter_num, chapter in enumerate(metadata):
                title = chapter[1]
                tc1 = timecode(chapter[0])
                # VTT Chapters are ranges (incl end time) so calculate that.
                if chapter_num == len(metadata) - 1:
                    tc2 = timecode(self.captions[-1]['time']) # Time of last subtitle
                else:
                    tc2 = timecode(metadata[chapter_num+1][0]) # Time of next chapter
                output.write("\n".join(["%s", "%s --> %s", "%s", "\n"]) %
                               (chapter_num, tc1, tc2, title))

    def export_text(self, filename):
        """Exports simple txt file with everything."""
        logging.info('Exporting text transcription...')
        with open(filename, mode='wt') as textfile:
            for sub in self.captions:
                fancy_time = timecode(sub['time'])
                if sub['type'] == 'meta':
                    chapter_title = ' '.join(sub['title'].splitlines()[0].split())
                    textfile.write("%s %s\n" % (fancy_time, chapter_title))
                    textfile.write("%s %s\n" % (fancy_time, sub['text']))
                    textfile.write("%s GUID:%s\n" % (fancy_time, sub['guid']))
                elif sub['type'] == 'text':
                    textfile.write("%s %s\n" % (fancy_time, sub['text']))

    def export_webvtt(self, filename, ms_per_char=60):
        """Export WebVTT to filename"""
        # Unlike SRT, WebVTT can have overlapping cues. 40chars x 60ms = ~2.4sec
        with open(filename, mode='wt') as out_file:
            out_file.write("WEBVTT\n\n")
            for num, sub in enumerate(self.captions):
                title = sub['text']
                ttl = len(html.unescape(title)) * ms_per_char * .001
                # TODO: decide whether varibale length ttls is preferrable
                ttl = 3.0
                tc1 = timecode(float(sub['time']))
                tc2 = timecode(float(sub['time']) + ttl)
                # Three lines [counter, "00:00:00,0000 --> 00:00:03,0000", title]
                entry = (num + 1, tc1, tc2, sub['text'])
                out_file.write("\n".join(["%s", "%s --> %s", "%s"]) % entry)
                out_file.write("\n\n")

    def export_srt(self, filename, ttl=3):
        """Exports SRT with each title onscreen for specified TTL"""
        # TODO: Replace naive joining & fixed ttl with something more dynamic
        #       Sadly SRT only supports one title on the screen at a time,
        #       and input titles are fragments with no specified duration.
        srt = []
        hold_time = None
        hold_text = []
        subs = self.captions
        for num, sub in enumerate(subs):
            hold_text.append(sub['text'])
            if not hold_time:
                hold_time = float(sub['time'])
            if num < len(subs) - 1 and (float(subs[num+1]['time']) - hold_time > ttl):
                title = "\n".join(hold_text)
                tc1 = timecode(float(hold_time), seperator=',')
                tc2 = timecode(float(hold_time) + ttl, seperator=',')
                entry = (tc1, tc2, title)
                srt.append("\n".join(["%s --> %s", "%s", "\n"]) % entry)
                hold_time = None
                hold_text = []
        logging.info('Exporting SRT')
        with open(filename, mode='wt') as srt_file:
            for num, sub in enumerate(srt):
                srt_file.write('%s\n%s' % (num + 1, sub))

    def export(self, file_prefix="pooppants"):
        """Export output files for supported filetype"""
        self.export_json("%s.%s" % (file_prefix, 'json'))
        self.export_srt("%s.%s" % (file_prefix, 'srt'))
        self.export_webvtt("%s.%s" % (file_prefix, 'vtt'))
        self.export_webvtt_chapters("%s.%s" % (file_prefix, 'chapters.vtt'))
        self.export_text_chapters("%s.%s" % (file_prefix, 'chapters.txt'))
        self.export_text("%s.%s" % (file_prefix, 'txt'))


def clean_title(title):
    """Remove/replace invalid characters from a string"""
    # https://developer.mozilla.org/en-US/docs/Web/API/WebVTT_API#Cue_payload
    title = title.replace('&', '&amp;')
    title = title.replace('<', '&lt;')
    title = title.replace('>', '&gt;')
    # '\u007f' (unicode delete' character) in my test file. Not invalid, but evil.
    title = title.replace('\u007f', '')
    return title


def timecode(seconds, seperator="."):
    """Takes seconds and returns SRT timecode format: e.g. 00:02:36,894"""
    # Leading & trailing zeros matter: 1.5 -> 00:00:01,500
    # SRT uses ',' before fractional seconds seperator, WebVTT uses '.'
    seconds = float(seconds)
    timecode_fmt = "%(hour)02d:%(minute)02d:%(second)02d%(ms_seperator)s%(ms)03d"
    return timecode_fmt % {'hour': seconds // 3600,
                           'minute': seconds // 60 % 60,
                           'second': seconds % 60,
                           'ms': seconds % 1 * 1000,
                           'ms_seperator': seperator}


def main():
    """CLI Usage"""
    parser = argparse.ArgumentParser(description="Granicus subtitle converter")
    parser.add_argument("file", help="Output filename prefix (without ext)",
                        nargs='?', default="agency_clipid")
    parser.add_argument("url", help="e.g. http://oakland.granicus.com/JSON.php?clip_id=2206")
    parser.add_argument('-v', '--verbose', action='count', default=0)
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    if args.file == 'agency_clipid':
        clip_id = dict(parse_qsl(urlsplit(args.url).query)).get('clip_id', 'clip')
        agency = urlsplit(args.url).netloc.replace('.granicus.com', '')
        args.file = "%s_%s" % (agency, clip_id)
    logging.info("Fetching JSON from %s", args.url)
    response = requests.get(args.url)
    json_data = json.loads(response.text)
    ttxt = Teletext(json_data)
    ttxt.export(args.file)


if __name__ == '__main__':
    main()
