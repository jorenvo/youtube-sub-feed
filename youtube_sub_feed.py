#!/usr/bin/env python3
# Copyright 2014 Joren Van Onder
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import urllib.request
import threading
import queue
import cgi
import json
import pprint

api_key = "AIzaSyDF98jSaJnjAI1PtG15GZqElPqzsHB3_ZQ"

class Entry:
    """Grabs the data we need and escapes it"""
    def __init__(self, entry=None):
        if entry is not None:
            self.channel_id = entry['snippet']['channelId']

            if entry['snippet']['channelTitle']:
                self.channel_title = entry['snippet']['channelTitle']
            else:
                self.channel_title = get_channel_title(self.channel_id)

            self.video_title = entry['snippet']['title']
            self.video_url = "https://www.youtube.com/watch?v=" + entry['id']['videoId']
            self.thumbnail_url = entry['snippet']['thumbnails']['medium']['url']
            self.publishedAt = entry['snippet']['publishedAt']

    def escape(self):
        self.channel_title = cgi.escape(self.channel_title)
        self.video_title = cgi.escape(self.video_title)

def write_file_to_fd(path):
    f = open(path, 'r')
    print(f.read(), end="", file=output_fd)
    f.close()

def write_html_header():
    abs_path = os.path.join(os.path.dirname(__file__), 'header.html')
    write_file_to_fd(abs_path)

def write_html_footer():
    abs_path = os.path.join(os.path.dirname(__file__), 'footer.html')
    write_file_to_fd(abs_path)

def print_progress(finished_one=True):
    total_amount_of_channels = len(channels)

    if finished_one:
        print_progress.amount_finished += 1

    percent_done = int((print_progress.amount_finished / total_amount_of_channels) * 100)

    print("\r[", end="")

    for i in range(0, total_amount_of_channels):
        if i < print_progress.amount_finished:
            print("#", end="")
        else:
            print(" ", end="")

    print("] " + str(percent_done) + "%", end="", flush=True)

    # print newline if we're done
    if percent_done == 100:
        print()

print_progress.amount_finished = 0 # function attribute

def get_channel_title(channel_name):
    "Required for some channels that for whatever reason do not set their channelTitle"

    response = urllib.request.urlopen("https://www.googleapis.com/youtube/v3/channels?" +
                                      "key=" + api_key +
                                      "&id=" + channel_name +
                                      "&fields=items/snippet/title" +
                                      "&part=snippet").read().decode("utf-8")
    response = json.loads(response)

    return response['items'][0]['snippet']['title']


def create_channel_vid_links():
    while True:
        max_results = 3
        channel_name = queue.get()

        response = urllib.request.urlopen("https://www.googleapis.com/youtube/v3/search?" +
                                          "key=" + api_key +
                                          "&maxResults=" + str(max_results) +
                                          "&channelId=" + channel_name +
                                          "&fields=items/id/videoId,items/snippet(title,channelId,channelTitle,publishedAt,thumbnails/medium/url)" +
                                          "&order=date" +
                                          "&type=video" +
                                          "&part=snippet").read().decode("utf-8")
        response = json.loads(response)

        for item in response['items']:
            entry = Entry(item)

            lock.acquire()
            try:
                entries.append(entry)
            finally:
                lock.release()

        print_progress()
        queue.task_done()

def get_channel_list_from_file(file_path):
    channels = []
    channels_fd = open(file_path, 'r')

    for line in channels_fd:
        if len(line) != 0:
            channels.append(line.rstrip('\n'))

    channels_fd.close()

    return channels

def prettyPrint(obj):
    pp = pprint.PrettyPrinter(indent = 4)
    pp.pprint(obj)

def print_help():
    print("Usage: youtube_sub_feed.py channels-file [output-file]")

########
# MAIN #
########
try:
    channels_file_path = sys.argv[1]
except IndexError:
    print_help()
    sys.exit(1)

try:
    output_fd = open(sys.argv[2], 'w')
except IndexError:
    output_fd = sys.stdout

entries = []
channels = get_channel_list_from_file(channels_file_path)

lock = threading.Lock()
queue = queue.Queue()
num_worker_threads = 8

print_progress(False)

# init and start the worker threads
for i in range(num_worker_threads):
     t = threading.Thread(target=create_channel_vid_links)
     t.daemon = True
     t.start()

# give the worker threads work
for channel in channels:
    queue.put(channel)

# wait until all the work in the queue is done
queue.join()

entries = sorted(entries, key=lambda entry: entry.publishedAt, reverse=True)

write_html_header()

print('\t<table style="margin:0px auto">', file=output_fd)

entry_nr = 0

for entry in entries:
    entry.escape()

    if (entry_nr < 8):
        image = '\t\t\t<td class="video_column"><img src="' + entry.thumbnail_url + '" alt="' + entry.video_title + ' thumbnail"/>'
    else:
        image = '\t\t\t<td></td>'

    print('\t\t<tr>', file=output_fd)
    print('\t\t\t<td class="channel_column" rowspan="2"><a class="channel_name" href="https://www.youtube.com/channel/'
          + entry.channel_id + '/videos">[' + entry.channel_title + ']</a></td>', file=output_fd)
    print('\t\t\t<td class="video_column"><a href="' + entry.video_url + '">' + entry.video_title + '</a></td>', file=output_fd)
    print('\t\t</tr>', file=output_fd)

    print('\t\t<tr>', file=output_fd)
    print(image, file=output_fd)
    print('\t\t</tr>', file=output_fd)

    entry_nr += 1

print('\t</table>', file=output_fd)

write_html_footer()

output_fd.close()
