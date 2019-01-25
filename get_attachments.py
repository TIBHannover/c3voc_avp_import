#!/usr/bin/env python2
# -*- coding: UTF-8 -*-

import argparse
import getpass
import os
import pycurl
import sys
import time
import urllib
from cStringIO import StringIO
from datetime import datetime

import requests
from lxml import etree

reload(sys)
sys.setdefaultencoding('utf-8')

parser = argparse.ArgumentParser(description='Download slide pdfs directly from frab')
parser.add_argument('schedule', help='schedule.xml file name', default='schedule.xml')
parser.add_argument('--since', action='store', default=0, type=int)
parser.add_argument('--verbose', '-v', action='store_true', default=False)
parser.add_argument('--offline', action='store_true', default=True)
parser.add_argument('--published', action='store_true', default=False)

args = parser.parse_args()

offline = args.offline  # True -> Schedules nicht von frab.cccv.de herunterladen (benötigt Account)

schedule_xml = args.schedule

download_dir = 'videos'
# TODO Als Option?
# download_dir = args.download_dir

LOGIN_HOST = 'https://frab.cccv.de'
LOGIN_URL = '%s/users/sign_in' % LOGIN_HOST
LOGIN_SUBMIT = '%s/users/sign_in?locale=en' % LOGIN_HOST


# https://frab.cccv.de/en/17c3/public/schedule.xml
# SCHEDULE_URL = '%s/en/%s/public/schedule.xml'


def setup_curl(curl_instance, url):
    """
    Common ration for curl instances.

    @type curl_instance: pycurl.Curl
    @type url: str
    @rtype StringIO
    """
    buf = StringIO()
    curl_instance.setopt(pycurl.TIMEOUT, 1)
    curl_instance.setopt(pycurl.COOKIEFILE, './temp.txt')  # Turn on cookies
    curl_instance.setopt(pycurl.URL, url)
    curl_instance.setopt(pycurl.WRITEFUNCTION, buf.write)
    # curl.setopt(pycurl.HEADERFUNCTION, header)
    curl_instance.setopt(pycurl.CONNECTTIMEOUT, 0)
    curl_instance.setopt(pycurl.TIMEOUT, 0)
    # curl.setopt(pycurl.SSL_VERIFYPEER, 0)
    curl_instance.setopt(pycurl.POST, 0)
    return buf


def acquire_token(curl_instance):
    """
    Acquires a login token.

    @type curl_instance: pycurl.Curl
    """
    print('acquire login token')
    buf = setup_curl(curl_instance, LOGIN_URL)
    print('GET %s' % LOGIN_URL)
    curl_instance.perform()
    assert curl_instance.getinfo(pycurl.HTTP_CODE) == 200, 'failed to acquire login token'
    html_parser = etree.HTMLParser()
    buf.reset()
    tree = etree.parse(buf, parser=html_parser, base_url=LOGIN_URL)
    csrf_token = tree.xpath('.//meta[@name="csrf-token"]')
    return csrf_token[0].attrib['content']


def login(curl_instance, login_token, username, password):
    """
    Perform login on website.

    @type username: str
    @type password: str
    @type login_token: token
    @type curl_instance: pycurl.Curl
    """
    print 'login with token %s' % login_token
    setup_curl(curl_instance, LOGIN_SUBMIT)
    curl_instance.setopt(pycurl.POST, 1)
    curl_instance.setopt(
        pycurl.POSTFIELDS, 'authenticity_token=%s&user[email]=%s&user[password]=%s' % (login_token, username, password))
    print 'POST %s' % LOGIN_SUBMIT
    curl_instance.perform()
    assert curl_instance.getinfo(pycurl.HTTP_CODE) == 302, 'failed to login'


if __name__ == '__main__':
    curl = pycurl.Curl()
    if not args.published and not offline:
        token = acquire_token(curl)
        time.sleep(3)
        USERNAME = raw_input('Username: ')
        PASSWORD = getpass.getpass()
        login(curl, token, USERNAME, PASSWORD)
        time.sleep(6)

    ul = urllib.URLopener()

    schedule = None
    if offline:
        with open(schedule_xml) as f:
            buf = f.read()
            schedule = etree.fromstring(buf).getroottree()
    elif args.published:
        schedule = etree.fromstring(
            requests.get('http://events.ccc.de/congress/2017/Fahrplan/schedule.xml').content)

    count = 0
    count_missing = 0
    max_time = 0

    for attachments in schedule.xpath('.//event/attachments[count(*)>=1]'):
        count += 1

        event = attachments.xpath('..')[0]
        slug = event.find('slug').text.encode('utf-8').strip()

        if args.verbose:
            print(slug)

        pdf_count = 0
        pdfs = []
        # from 2
        download_urls = []
        for attachment in attachments:
            basename = os.path.basename(attachment.attrib['href']).split('?')[0]
            ext = os.path.splitext(basename)[1][1:].lower()

            # skip specific files
            if ext == 'torrent' or basename == 'missing.png':
                # if args.verbose: print('   ignoring: ' + basename)
                count_missing += 1
                continue

            title = attachment.text.encode('utf-8').strip()

            title_basename = (title + basename).lower()
            if 'abstract' in title_basename or 'paper' in title_basename or 'bierzerlegung' in title_basename:
                if args.verbose:
                    print('   ignoring: ' + basename).encode('utf-8').strip()
                continue

            file_path, time = attachment.attrib['href'].split('?')
            time = int(time)
            if time > max_time:
                max_time = time

            if ext == 'pdf' and time > args.since:
                pdf_count += 1
                # presentation, slide, folien
                if args.verbose:
                    print('   ' + ', '.join([ext, title, basename])).encode('utf-8').strip()

                file_url = LOGIN_HOST + file_path
                if args.verbose:
                    print('   ' + file_url + '\n')

                # from 2
                download_urls.append(file_url)

            else:
                if args.verbose:
                    print('   ignoring: ' + basename)
                continue

        if pdf_count > 1:
            print('     WARNING: multiple (%d) pdf files' % pdf_count)
            print('TARGET ' + download_dir)
            for url in download_urls:
                try:
                    ul.retrieve(url, download_dir + '/')
                except IOError:
                    sys.stderr.write('cannot download ' + url)
        elif pdf_count == 1:
            try:
                print('trying to download: ' + download_urls[0])
                filename = attachments.xpath('../slug')[0].text.strip()
                print(filename)
                if not os.path.exists(download_dir + '/' + filename):
                    os.mkdir(download_dir + '/' + filename)
                ul.retrieve(download_urls[0], download_dir + '/' + filename + '/_' + filename + '_.pdf')
            except IOError:
                sys.stderr.write('cannot download ' + download_urls[0])
        else:
            print('     slides pdf missing!')

    # Download-Statistiken ausgeben
    print('========================================\n' +
          '{:3d} events with attachments, '.format(count) +
          'and {:3d} missing.png – last change {}'.format(count_missing, datetime.fromtimestamp(max_time)))
