#!/usr/bin/env python3

import flask
from ics import Calendar,Event
import requests

app = flask.Flask(__name__)

@app.route('/')
def main():
    def make_allday_event_readable(timeline):
        for e in timeline:
            if e.all_day:
                e.begin = e.begin.replace(hour=10, tzinfo='Asia/Tokyo')
                e.end = e.end.replace(hour=19, tzinfo='Asia/Tokyo')
            yield e

    url = flask.request.args.get('url', 'https://calendar.google.com/calendar/ical/ja.japanese%23holiday%40group.v.calendar.google.com/public/basic.ics')
    ical = Calendar(requests.get(url).text)
    ical.timeline = list(make_allday_event_readable(ical.timeline))

    return str(ical)

if __name__ == '__main__':
    app.run()
