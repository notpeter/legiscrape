#!/usr/bin/env python3
import argparse
import json
import logging
import os
import requests
from jsonschema import validate

class Teletext(object):
    """Granicus Video JSON Closed Captions to WEBVTT/SRT"""
    # Granicus JSON subtitle format is array containing an array of objects
    # e.g. [ [ {obj1}, {obj2} ] ] where obj is either text or meta:
    # * Text: {"type": "text", "time": 352.332, "text": "Hello"}
    # * Meta: {"type": "meta", "time": 123.123, ...}

    def __init__(self, captions, file_prefix):
        self.file_prefix = file_prefix
        filename = 'granicus-captions.schema.json'
        if os.path.dirname(__file__):
            filename = "%s/%s" % (os.path.dirname(__file__), filename)
        with open(filename) as jsonschema:
            schema = json.load(jsonschema)

        logging.info('Validating JSON...')
        # Raises ValidationError
        validate(captions, schema)
        self.captions = captions[0]
        # Evil 'unicode delete' character '\u007f' present in my test file.
        # TODO: Delete the character to the left instead of just stripping.
        #for sub in self.captions:
        #    if '\u007f' in sub.get('text'):
        #        sub['text'] = sub['text'].replace('\u007f', '')

    def filename(self, extension):
        """Returns extension appended to file_prefix"""
        return "%s.%s" % (self.file_prefix, extension)

    def export_json(self):
        """Exports Granicus JSON file"""
        logging.info('Exporting JSON...')
        with open(self.filename('json'), mode='wt') as output_file:
            json.dump(self.captions, output_file)

    def export_chapters(self):
        """Exports chapters.txt file, e.g. "00:04:20,000 Chapter 1"""
        logging.info('Exporting chapters.txt...')
        metadata = []
        for sub in self.captions:
            if sub['type'] == 'meta':
                chapter_title = ' '.join(sub['title'].splitlines()[0].split())
                metadata.append((timecode(sub['time']), chapter_title))
        with open(self.filename('chapters.txt'), mode='wt') as chapters:
            for chapter in metadata:
                chapters.write("%s %s\n" % chapter)
        return metadata

    def export_text(self):
        """Exports simple txt file with everything."""
        logging.info('Exporting text transcription...')
        with open(self.filename('txt'), mode='wt') as textfile:
            for sub in self.captions:
                fancy_time = timecode(sub['time'])
                if sub['type'] == 'meta':
                    chapter_title = ' '.join(sub['title'].splitlines()[0].split())
                    textfile.write("%s %s\n" % (fancy_time, chapter_title))
                    textfile.write("%s %s\n" % (fancy_time, sub['text']))
                    textfile.write("%s GUID:%s\n" % (fancy_time, sub['guid']))
                elif sub['type'] == 'text':
                    textfile.write("%s %s\n" % (fancy_time, sub['text']))

    def export_srt(self, ttl=3):
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
                title = sub2srt("\n".join(hold_text), hold_time, ttl)
                srt.append(title)
                hold_time = None
                hold_text = []
        logging.info('Exporting SRT and WEBVTT')
        with open(self.filename('vtt'), mode='wt') as srt_file:
            srt_file.write("WEBVTT\n\n")
            srt_file.write('\n'.join(srt))
        with open(self.filename('srt'), mode='wt') as srt_file:
            for num, sub in enumerate(srt):
                srt_file.write('%s\n%s\n' % (num + 1, sub))

    def export(self):
        """Export output files for supported filetype"""
        self.export_json()
        self.export_srt()
        self.export_chapters()
        self.export_text()


def timecode(seconds):
    """Takes seconds and returns SRT timecode format: e.g. 00:02:36,894"""
    # Leading & trailing zeros matter: 1.5 -> 00:00:01,500
    seconds = float(seconds)
    return "%(hour)02d:%(minute)02d:%(second)02d,%(ms)03d" % {'hour': seconds // 3600,
                                                              'minute': seconds // 60 % 60,
                                                              'second': seconds % 60,
                                                              'ms': seconds % 1 * 1000}


def sub2srt(title, seconds, ttl):
    """Generate an SRT stanza for a given subtitle"""
    tc1 = timecode(float(seconds))
    tc2 = timecode(float(seconds) + ttl)
    # "00:00:00,0000 --> 00:00:01,0000"
    return "%s --> %s\n%s\n" % (tc1, tc2, title)


def main():
    parser = argparse.ArgumentParser(description="Granicus subtitle converter")
    parser.add_argument("file", help="Output filename (without extension)")
    parser.add_argument("url", help="e.g. http://oakland.granicus.com/JSON.php?clip_id=2206")
    parser.add_argument('-v', '--verbose', action='count', default=0)
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    logging.info("Fetching JSON from %s", args.url)
    response = requests.get(args.url)
    json_data = json.loads(response.text)
    ttxt = Teletext(json_data, args.file)
    ttxt.export()


if __name__ == '__main__':
    main()
