#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import argparse
import json
import os
import sys
import urllib

import lxml.etree
import lxml.html
import lxml.html.clean
import requests

parser = argparse.ArgumentParser(description='TIB AV Portal: Upload and metadata generation ')
parser.add_argument('schedule', help='schedule.xml file name', default='schedule.xml')
parser.add_argument('--mediaccc', action='store_true', default=True)
parser.add_argument('--verbose', '-v', action='store_true', default=False)
args = parser.parse_args()

# lxml does only support http and not https, compare https://stackoverflow.com/a/26164472
# schedule = etree.fromstring(requests.get("https://events.ccc.de/congress/2017/Fahrplan/schedule.xml").content)
# schedule = lxml.etree.parse("temp/schedule.xml")
schedule = lxml.etree.parse(args.schedule)

mediaccc = args.mediaccc

acronym = schedule.find('conference').find('acronym').text

# TODO: use argument parser?
ignore_license = True

download_dir = 'videos'


def main():
    for event_id in schedule.xpath(u'day/room/event/@id'):
        event = schedule.xpath('day/room/event[@id="' + event_id + '"]')[0]
        slug = event.find('slug').text.encode('utf-8').strip()

        title = ''
        try:
            title = event.find('title').text.encode('utf-8').strip()
            if args.verbose:
                print('\n== ' + title)
        except:
            sys.stderr.write(' \033[91mWARNING: Title not found. \033[0m\n')

        subtitle = ''
        try:
            subtitle = event.find('subtitle').text.encode('utf-8').strip()
        except:
            sys.stderr.write(' \033[91mWARNING: Subtitle not found. \033[0m\n')

        link = ''
        try:
            link = event.find('url').text
        except:
            sys.stderr.write(' \033[91mWARNING: Link not found. \033[0m\n')

        if event.find('recording').find('optout').text == 'true':
            sys.stderr.write(' INFO: Ignoring '' + title + '' due to optout\n')
            continue

        if not ignore_license and event.find('recording').find('license').text is None:
            sys.stderr.write(' \033[91mERROR: ' + title + ' has empty recording license \033[0m\n')
            continue

        if mediaccc:
            # request recording from voctoweb aka media.ccc.de
            try:
                recording = find_recoding(event.attrib['guid'])
                file_url = recording['recording_url']
            except:
                file_url = False
        else:
            # download file directly from our intermediate upload host. But not for C3...
            file_url = 'http://live.ber.c3voc.de/releases/{}/{}-hd.mp4'.format(acronym, event_id)

        # open file url
        try:
            if not os.path.exists(download_dir + '/{0}'.format(slug)):
                os.mkdir(download_dir + '/{0}'.format(slug))
            urllib.urlretrieve(file_url, download_dir + '/{0}/{0}.mp4'.format(slug))
        except:
            sys.stderr.write(' \033[91mERROR: HTTPError ocurred. \033[0m\n')
            continue

        # format person names to library conventions – random search result:
        # https://books.google.de/books?id=wJyoBgAAQBAJ&pg=PA68&lpg=PA68&dq=bibliotheken+mehrere+vornamen&source=bl&ots=bP4gjj1Zft&sig=2HxD9qHWHzo7Z0kMc5vMITo83ps&hl=en&sa=X&redir_esc=y#v=onepage&q=bibliotheken%20mehrere%20vornamen&f=false
        persons = []
        for p in event.find('persons'):
            p = p.text.split(' ')
            if len(p) > 3:
                print('   \033[91mWARNING: Person name consists of more than three parts: ' + str(p) + '\033[0m')
            if len(p) == 1:
                persons.append(p[0])
            elif len(p) == 2:
                persons.append(p[1] + ', ' + p[0])
            else:
                persons.append(p[-1] + ', ' + p[0] + ' ' + p[1])

        # see https://github.com/voc/scripts/blob/master/slides/get_attachments.py
        material = []
        if os.path.isfile(download_dir + '/{0}/_{0}_.pdf'.format(slug)):
            material.append(('File', 'Slides as PDF', '_{}_.pdf'.format(slug)))

        lang = event.find('language').text
        if lang == 'en':
            lang = 'eng'
        elif lang == 'de':
            lang = 'ger'
        else:
            lang = ''

        abstract = ''
        try:
            abstract = strip_tags(event.find('abstract').text).encode('utf-8').strip()
        except:
            try:
                # use description when abstract is empty
                abstract = strip_tags(event.find('description').text).encode('utf-8').strip()
            except:
                sys.stderr.write(' \033[91mWARNING: ' + title + ' has empty abstract. \033[0m\n')

        track = ''
        try:
            track = event.find('track').text.encode('utf-8').strip()
        except:
            sys.stderr.write(' \033[91mWARNING: Track not found. \033[0m\n')

        links = []
        try:
            links = event.find('links')
        except:
            sys.stderr.write(' \033[91mWARNING: Links not found. \033[0m\n')

        if not os.path.exists(download_dir + '/{0}'.format(slug)):
            os.mkdir(download_dir + '/{0}'.format(slug))
        with open(download_dir + '/{0}/{0}.xml'.format(slug), 'wt') as f:
            # TODO: Test if XML generation via external library e.g. via LXML produces nicer code
            metadata = '''<?xml version="1.0" encoding="UTF-8" ?>
            <resource xmlns="http://www.tib.eu/fileadmin/extern/knm/NTM-Metadata-Schema_v_2.2.xsd">
            <alternateIdentifiers><alternateIdentifier alternateIdentifierType="local-frab-event-id">''' \
                       + event_id + '''</alternateIdentifier></alternateIdentifiers>
            <titles><title language="''' + lang + '''">''' + title + '''</title>
            <title titleType="Subtitle" language="''' + lang + '''">''' + subtitle + '''</title></titles>
            <creators>''' + '\n    '.join(
                ['<creator><creatorName>{}</creatorName></creator>'.format(p.encode('utf-8').strip()) for p in
                 persons]) + '''</creators><language>''' + lang + '''</language><genre>Conference</genre>'''

            if abstract:
                metadata = metadata \
                           + '''<descriptions><description descriptionType="Abstract" language="''' \
                           + lang + '''"><![CDATA[''' \
                           + abstract + ''']]></description></descriptions>'''

            metadata = metadata + '''<additionalMaterials>'''

            if material is not None:
                metadata = metadata + '\n    '.join([
                    '<additionalMaterial additionalMaterialType="{a[0]}" additionalMaterialTitle="{a[1]}" relationType="isSupplementedBy">{a[2]}</additionalMaterial>'.format(
                        a=a) for a in material])
            if links is not None:
                metadata = metadata + '\n    '.join([
                    '<additionalMaterial additionalMaterialType="URL" additionalMaterialTitle="{0}" relationType="isSupplementedBy">{1}</additionalMaterial>'.format(
                        a.text.encode('utf-8').strip(), (a.attrib['href']).encode('utf-8').strip()) for a in links])

            metadata = metadata + '''<additionalMaterial additionalMaterialType="URL" additionalMaterialTitle="media.ccc.de" relationType="isCitedBy">https://media.ccc.de/v/''' +\
                       slug + '''</additionalMaterial>'''

            if link != '':
                metadata = metadata + '''<additionalMaterial additionalMaterialType="URL" additionalMaterialTitle="fahrplan.events.ccc.de" relationType="isCitedBy">''' + link + '''</additionalMaterial>'''

            metadata = metadata + '''</additionalMaterials>
            <keywords><keyword language="''' + lang + '''">''' + track + '''</keyword></keywords>
            <publishers><publisher><publisherName>Chaos Computer Club e.V.</publisherName></publisher></publishers>
            <publicationYear>2017</publicationYear></resource>'''

            f.write(metadata)


def find_recoding(guid):
    # request event + recordings from voctoweb aka media.ccc.de
    global voctoweb_event
    voctoweb_url = 'https://media.ccc.de/public/events/' + guid
    guid_exist = True
    try:
        voctoweb_event = requests.get(voctoweb_url).json()
    except:
        guid_exist = False

    if not guid_exist:
        return False
    else:
        results = []

        print('GUID: ' + guid)

        try:
            for r in voctoweb_event['recordings']:
                # select mp4 which contains only the orginal language
                if r['folder'] == 'h264-hd' and r['mime_type'] == 'video/mp4' and r['language'] == voctoweb_event['original_language']:
                    # and 'slides' not in r['folder']:
                    results.append(r)

            if len(results) > 1:
                sys.stderr.write('\033[91mFATAL: API returned multiple recordings: {} \033[0m\n'.format(voctoweb_url))
                sys.stderr.write(json.dumps(results, indent=4))
                exit()
            elif len(results) == 1:
                return results[0]

            return None
        except:
            event_exist = False
        if not event_exist:
            return False


# from https://stackoverflow.com/a/42461722/521792
def strip_tags(string):
    tree = lxml.html.fromstring(string)
    clean_tree = lxml.html.clean.clean_html(tree)
    return clean_tree.text_content()


if __name__ == '__main__':
    if not os.path.exists(download_dir):
        os.mkdir(download_dir)
    main()
