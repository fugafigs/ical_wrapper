#!/usr/bin/env python3

import flask
from typing import Iterator
from ics import Calendar,Event
import requests
import re
import os

class ICalWrapper():
    FETCH_URLS = os.environ.get('FETCH_URLS','')
    BEGIN_HOUR = int(os.environ.get('BEGIN_HOUR', 10))
    INTERVAL_HOURS = int(os.environ.get('INTERVAL_HOURS', 9))
    DEFAULT_TIMEZONE = os.environ.get('DEFAULT_TIMEZONE', 'UTC')

    def __init__(self, fetch_urls: str=FETCH_URLS):
        if not fetch_urls:
            raise RuntimeError('Please set FETCH_URLS correctly.')

        ical = Calendar()
        for url in map(str.strip, fetch_urls.split(',')):
            text = requests.get(url).text
            c = self.convert_calender(text)
            if not ical.events:
                ical = c
            else:
                ical.events = ical.events.union(c.events)

        self.ical = ical

    def __str__(self):
        return str(self.ical)

    def convert_calender(self, text: str) -> Calendar:
        ical = Calendar(text)
        timezone = self.extract_timezone(text)

        converted_events = set()
        for event in ical.events:
            if event.all_day:
                event.begin = event.begin.replace(hour=self.BEGIN_HOUR).to(timezone)
                event.end = event.begin.shift(hours=self.INTERVAL_HOURS)
            converted_events.add(event)

        ical.events = converted_events
        
        return ical

    def extract_timezone(self, text: str) -> str:
        matched = re.search(r'^X-WR-TIMEZONE:\s*(.*?)\s*$', text, re.MULTILINE)
        if matched:
            timezone = matched.group(1).strip()
        else:
            timezone = self.DEFAULT_TIMEZONE
        
        return timezone

app = flask.Flask(__name__)

@app.route('/')
def main():
    fetch_urls = flask.request.args.get('url', '')
    ical = ICalWrapper(fetch_urls)

    return str(ical)

if __name__ == '__main__':
    app.run()
