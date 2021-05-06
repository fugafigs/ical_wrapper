#!/usr/bin/env python3

import flask
from typing import Iterator
from ics import Calendar,Event
import requests
import re
import os
from uuid import uuid4

class ICalWrapper():
    BEGIN_HOUR = int(os.environ.get('BEGIN_HOUR', 10))
    INTERVAL_HOURS = int(os.environ.get('INTERVAL_HOURS', 9))
    TIMEZONE = os.environ.get('TIMEZONE', 'UTC')

    def __init__(self, fetch_urls: str):
        if not fetch_urls:
            raise RuntimeError('Please set FETCH_URLS correctly.')

        ical = Calendar()
        for url in map(str.strip, fetch_urls.split(',')):
            c = self.convert_calender(url)
            if not ical.events:
                ical = c
            else:
                ical.events = ical.events.union(c.events)

        self.ical = ical

    def __str__(self):
        text = str(self.ical)
        text = re.sub(r'^METHOD:.*$', '', text, 0, re.MULTILINE)
        text = re.sub(r'^CLASS:.*$', '', text, 0, re.MULTILINE)
        text = re.sub(r'^SEQUENCE:.*$', '', text, 0, re.MULTILINE)

        return text

    def convert_calender(self, url: str) -> Calendar:
        text = requests.get(url).text
        text = re.sub(r'^X-WR.*?:.*$', '', text, 0, re.MULTILINE)
        text = re.sub(r'^STATUS:.*$', '', text, 0, re.MULTILINE)
        text = re.sub(r'^PRODID:(.{,5}).*$', r'PRODID:-//IcalWrapper \1//EN', text, 0, re.MULTILINE)

        ical = Calendar(text)

        converted_events = set()
        for event in ical.events:
            if event.all_day:
                event.name = f'[(終日の予定) {event.name}]'
                event.begin = event.begin.to(self.TIMEZONE).replace(hour=self.BEGIN_HOUR).to('UTC')
                event.end = event.begin.shift(hours=self.INTERVAL_HOURS)
                event.created = event.begin
                event.last_modified = event.begin
                event.transparent = False
                event.description = "(終日)" + event.description or ""
                event.uid = str(uuid4())
            converted_events.add(event)

        ical.events = converted_events
        
        return ical

app = flask.Flask(__name__)

@app.route('/')
def main():
    fetch_urls = flask.request.args.get('url', 'https://calendar.google.com/calendar/ical/ja.japanese%23holiday%40group.v.calendar.google.com/public/basic.ics')
    ical = ICalWrapper(fetch_urls)

    return str(ical)

if __name__ == '__main__':
    app.run()
