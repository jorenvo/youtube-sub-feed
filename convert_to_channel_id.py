#!/usr/bin/env python3
from urllib import request
import sys
import json
import pprint

api_key = "AIzaSyDF98jSaJnjAI1PtG15GZqElPqzsHB3_ZQ"

def print_help():
    print("Usage: convert_to_channel_id.py channel-name")

try:
    channel_name = sys.argv[1]
except IndexError:
    print_help()
    sys.exit(1)

response = request.urlopen("https://www.googleapis.com/youtube/v3/channels?" +
                           "key=" + api_key +
                           "&part=id" +
                           "&forUsername=" + channel_name).read().decode("utf-8")
response = json.loads(response)

try:
    print(response['items'][0]['id'])
except IndexError:
    print(channel_name + " not found")
