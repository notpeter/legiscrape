import json
import logging
import os
import shutil
import subprocess
from urllib.parse import parse_qsl, urlsplit

import requests


def es_search(index, clip_id):
    """Queries the elasticsearch for video metadata"""
    search_url = 'http://search.granicus.com/api/%s/_search' % index
    query = {'query': {'match': {'video_id': {'query': clip_id}}}, 'size': 1}
    query = json.dumps(query)
    result = requests.post(search_url, data=query)
    result = json.loads(result.content)
    # FIXME: This is fragile is fuck.
    try:
        video = result['hits']['hits'][0]['_source']['http']
    except KeyError:
        video = None
    return video


def get(url, filename=None):
    """Save contents of a URL to a file."""
    # TODO: Make this not require curl/wget/aria2c
    # Sadly resumable downloads with status updates is non-trivial with requests.
    # aria2c multi-connection is 3-4x faster because granicus servers are slow
    if not filename:
        filename = urlsplit(url).path.split('/')[-1]
    if shutil.which('aria2c'):
        conns = '4'
        cmd = ['aria2c', '--summary-interval', '0', '--auto-file-renaming=false',
               '-x', conns, '-s', conns, '-o', filename, url]
    elif shutil.which('wget'):
        cmd = ['wget', '-c', '-O', filename, url]
    elif shutil.which('curl'):
        cmd = ['curl', '-L', '-o', filename, '-O', '-C', '-', url]
    else:
        raise EnvironmentError("No curl or wget...what is this place?")
    logging.info('Running %s', " ".join(cmd))
    proc = subprocess.Popen(cmd)
    proc.communicate()
    return filename


def remux(filename, output_filename, srt_filename=None, chapter_filename=None):
    """Demux an MP4 file into aac audio and h264 video"""
    if not shutil.which('ffmpeg'):
        raise EnvironmentError("Couldn't find ffmpeg.")
    if not shutil.which('MP4Box'):
        raise EnvironmentError("Couldn't find  MP4Box.")
    cmd = ['ffmpeg', '-y', '-i', filename, '-vcodec', 'copy',
           '-an', '-bsf:v', 'h264_mp4toannexb', "%s.h264" % filename,
           '-vn', '-acodec', 'copy', "%s.aac" % filename]
    proc = subprocess.Popen(cmd)
    proc.communicate()
    logging.info('Demuxing: %s', " ".join(cmd))
    cmd = ["MP4Box", "-add", "%s.h264#video" % filename,
           "-add", "%s.aac#audio" % filename]
    if srt_filename and os.path.exists(srt_filename):
        cmd.extend(['-add', "%s#lang=eng" % srt_filename])
    if srt_filename and os.path.exists(chapter_filename):
        cmd.extend(['-chap', chapter_filename])
    cmd.extend(['-new', output_filename])
    logging.info('Remuxing: %s', " ".join(cmd))
    proc = subprocess.Popen(cmd)
    proc.communicate()
