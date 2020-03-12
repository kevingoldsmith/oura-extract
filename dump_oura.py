#!/usr/bin/env python
import argparse
import configparser
import datetime
import os
import json
import time
from oura import OuraClient

DUMP_DIR = 'oura-dumps'
CONFIG_FILE = 'config.ini'

def mkdate(datestr):
    try:
        fulltime = time.strptime(datestr, '%Y-%m-%d')
        return datetime.date(fulltime.tm_year, fulltime.tm_mon, fulltime.tm_mday)
    except ValueError:
        raise argparse.ArgumentTypeError(datestr + ' is not a proper date string')


def logmsg(msg):
    time = datetime.datetime.now()
    print("[%04i/%02i/%02i %02i:%02i:%02i]: %s" % (time.year, time.month, time.day, time.hour, time.minute, time.second, msg))


def update_config(token_dict):
    global config_parser
    config_parser['Login Parameters']['refresh_token'] = token_dict['refresh_token']
    with open(CONFIG_FILE, 'w') as configfile:
        config_parser.write(configfile)


def dump_to_json_file(data_type, date, data):
    directory = "%s/%i/%s" % (DUMP_DIR, date.year, date)
    if not os.path.isdir(directory):
        os.makedirs(directory)
    with open("%s/%s.json" % (directory, data_type), "w") as f:
        f.write(json.dumps(data, indent=2))
    time.sleep(1)


def previously_dumped(date):
    return os.path.isdir("%s/%i/%s" % (DUMP_DIR, date.year, date))


def dump_day(c, date):
    sleep_data = c.sleep_summary(date)
    dump_to_json_file("sleep", date, sleep_data)

    activity_data = c.activity_summary(date)
    dump_to_json_file("activity", date, activity_data)

    readiness_data = c.readiness_summary(date)
    dump_to_json_file("readiness", date, readiness_data)

    return True


config_parser = configparser.ConfigParser()
config_parser.read(CONFIG_FILE)
client_id = config_parser.get('Login Parameters', 'client_id')
client_secret = config_parser.get('Login Parameters', 'client_secret')
access_token = config_parser.get('Login Parameters', 'access_token')
refresh_token = config_parser.get('Login Parameters', 'refresh_token')
refresh_callback = lambda x: update_config(x)

auth_client = OuraClient(
    client_id=client_id,
    client_secret=client_secret,
    access_token=access_token,
    refresh_token=refresh_token,
    refresh_callback=refresh_callback
    )

date = datetime.date.today()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Dump all oura data.')
    parser.add_argument('-d', '--date', type=mkdate)
    ns = parser.parse_args()
    if not ns.date is None:
        date = ns.date

while not previously_dumped(date):
    logmsg('dumping {}'.format(date))
    r = dump_day(auth_client, date)
    date -= datetime.timedelta(days=1)
    if not r:
        break
