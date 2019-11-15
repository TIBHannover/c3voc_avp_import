#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import argparse
import cgi
import json
import re

import magic
import os
import shutil
import sys
import urllib

import lxml.etree
import lxml.html
import lxml.html.clean
import requests

from config import MAX_FILENAME_SIZE

parser = argparse.ArgumentParser(description='TIB AV Portal: Upload and metadata generation ')
parser.add_argument('schedule', help='schedule.xml file name', default='schedule.xml')
parser.add_argument('--verbose', '-v', action='store_true', default=False)
args = parser.parse_args()

# lxml does only support http and not https, compare https://stackoverflow.com/a/26164472
# schedule = etree.fromstring(requests.get("https://events.ccc.de/congress/2017/Fahrplan/schedule.xml").content)
# schedule = lxml.etree.parse("temp/schedule.xml")
schedule = lxml.etree.parse(args.schedule)

acronym = schedule.find('conference').find('acronym').text

# TODO: use argument parser?
ignore_license = True

download_dir = 'videos_c3voc'

mime = magic.Magic(mime=True)


def escape_html_sc(event, element):
    return cgi.escape(event.find(element).text.encode('utf-8').strip())


def main():
    errors = []
    for event_id in schedule.xpath(u'day/room/event/@id'):
        event = schedule.xpath('day/room/event[@id="' + event_id + '"]')[0]
        slug = event.find('slug').text.encode('utf-8').strip()  # slug will be escaped below in xml
        slug_short = slug[0:MAX_FILENAME_SIZE]

        title = ''
        try:
            title = escape_html_sc(event, 'title')
            if args.verbose:
                print('\n== ' + title)
        except:
            sys.stderr.write(' \033[91mWARNING: ' + slug + ' Title not found. \033[0m\n')

        subtitle = ''
        try:
            subtitle = escape_html_sc(event, 'subtitle')
        except:
            sys.stderr.write(' \033[91mWARNING: ' + slug + ' Subtitle not found. \033[0m\n')

        link = ''
        try:
            link = escape_html_sc(event, 'url')
        except:
            sys.stderr.write(' \033[91mWARNING: ' + slug + ' Link not found. \033[0m\n')

        try:
            optout = event.find('recording').find('optout').text
        except:
            sys.stderr.write(' \033[91mERROR: No optout information for ' + slug + ' \033[0m\n')
            errors.append('ERROR: ' + event_id + ' : "' + slug + '" : No optout information found.')
            continue

        if optout == 'true':
            sys.stderr.write(' \033[91mERROR: Ignoring ' + slug + ' due to optout. \033[0m\n')
            errors.append('ERROR: ' + event_id + ' : "' + slug + '" : Ignored due to optout.')
            continue

        if not ignore_license and event.find('recording').find('license').text is None:
            sys.stderr.write(' \033[91mERROR: ' + slug + ' has empty recording license. \033[0m\n')
            errors.append('ERROR: ' + event_id + ' : "' + slug + '" : Empty recording license.')
            continue

        # request recording from voctoweb aka media.ccc.de
        guid = event.attrib['guid']
        try:
            recording = find_recoding(guid)
            file_url = recording['recording_url']
        except:
            sys.stderr.write(' INFO: ' + slug + ' : Using alternative video repository (live.ber.c3voc.de).\n')
            file_url = 'http://live.ber.c3voc.de/releases/{}/{}-hd.mp4'.format(acronym, event_id)

        # open file url
        download_path = download_dir + '/{0}'.format(slug_short)
        try:
            if not os.path.exists(download_path):
                os.mkdir(download_path)
            video_filename = download_dir + '/{0}/{0}.mp4'.format(slug_short)
            urllib.urlretrieve(file_url, video_filename)
            mime_type = mime.from_file(video_filename)
            #print(mime_type)
            if mime_type != 'video/mp4':
                shutil.rmtree(download_path)
                sys.stderr.write(' \033[91mERROR: ' + slug + ' : Video is not valid mp4. \033[0m\n')
                errors.append('ERROR: ' + event_id + ' : "' + slug + '" : Video is not valid mp4.')
                continue
        except:
            if os.path.exists(download_path):
                shutil.rmtree(download_path)
            sys.stderr.write(' \033[91mERROR: ' + slug + ' : HTTPError ocurred. \033[0m\n')
            errors.append('ERROR: ' + event_id + ' : "' + slug + '" : HTTPError ocurred.')
            continue

        # format person names to library conventions – random search result:
        # https://books.google.de/books?id=wJyoBgAAQBAJ&pg=PA68&lpg=PA68&dq=bibliotheken+mehrere+vornamen&source=bl&ots=bP4gjj1Zft&sig=2HxD9qHWHzo7Z0kMc5vMITo83ps&hl=en&sa=X&redir_esc=y#v=onepage&q=bibliotheken%20mehrere%20vornamen&f=false
        persons = []
        for p in event.find('persons'):
            p = cgi.escape(p.text)
            p = p.split(' ')
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
        pdfs = [f for f in os.listdir(download_path) if os.path.isfile(f) and mime.from_file(f) == 'application/pdf']
        if pdfs is not None and len(pdfs) > 0:
            for pdf in pdfs:
                pdf_formatted = pdf[:-4] + '.pdf'  # extension is already checked in get_attachments.py
                material.append(('File', 'Slides as PDF', pdf_formatted))

        lang = event.find('language').text
        if lang == 'en':
            lang = 'eng'
        elif lang == 'de':
            lang = 'ger'
        else:
            lang = ''

        # no escaping for abstract, will be placed in <![CDATA[]]>
        abstract = ''
        try:
            abstract = event.find('abstract').text.encode('utf-8').strip()
        except:
            try:
                # use description when abstract is empty
                abstract = event.find('description').text.encode('utf-8').strip()
            except:
                sys.stderr.write(' \033[91mWARNING: ' + slug + ' has empty abstract. \033[0m\n')

        track = ''
        try:
            track = escape_html_sc(event, 'track')
        except:
            sys.stderr.write(' \033[91mWARNING: ' + slug + ' : Track not found. \033[0m\n')

        links = []
        try:
            links = event.find('links')
        except:
            sys.stderr.write(' \033[91mWARNING: ' + slug + ' : Links not found. \033[0m\n')

        with open(download_dir + '/{0}/{0}.xml'.format(slug_short), 'wt') as f:
            # TODO: Test if XML generation via external library e.g. via LXML produces nicer code
            metadata = '''<?xml version="1.0" encoding="UTF-8" ?>
            <resource xmlns="http://www.tib.eu/fileadmin/extern/knm/NTM-Metadata-Schema_v_2.2.xsd">
            <externalLocalID externalLocalIDType="local-frab-event-id">''' + guid + '''</externalLocalID>
            <titles><title language="''' + lang + '''">''' + title + '''</title>
            <title titleType="Subtitle" language="''' + lang + '''">''' + subtitle + '''</title></titles>
            <creators>''' + '\n    '.join(
                ['<creator><creatorName>{}</creatorName></creator>'.format(cgi.escape(p.encode('utf-8').strip()))
                 for p in persons])\
                       + '''</creators><language>''' + lang + '''</language><genre>Conference</genre>'''

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
                        cgi.escape(a.text.encode('utf-8').strip().replace('"', '')), cgi.escape((a.attrib['href']).encode('utf-8').strip())) for a in links])
            metadata = metadata + '''<additionalMaterial additionalMaterialType="URL" additionalMaterialTitle="media.ccc.de" relationType="isCitedBy">https://media.ccc.de/v/'''\
                       + cgi.escape(slug) + '''</additionalMaterial>'''
            if link != '':
                r = re.search('(https?://)((\w+\.)+\w+)?(/\S+)?', link)
                try:
                    additional_material_title_link = r.group(2)
                except IndexError:
                    sys.stderr.write(' \033[91mWARNING: ' + slug + ' : Link for additional material title could not be extracted. \033[0m\n')
                if additional_material_title_link is None or additional_material_title_link == '':
                    sys.stderr.write(' \033[91mWARNING: ' + slug + ' : Link for additional material title is empty and won\'t be added. \033[0m\n')
                else:
                    additional_material_title_link = '''additionalMaterialTitle="''' + additional_material_title_link + '''" '''
                    metadata = metadata + '''<additionalMaterial additionalMaterialType="URL" ''' + additional_material_title_link + '''relationType="isCitedBy">''' + link + '''</additionalMaterial>'''
            metadata = metadata + '''</additionalMaterials>
            
            <keywords><keyword language="''' + lang + '''">''' + track + '''</keyword></keywords>
            <publishers><publisher><publisherName>Chaos Computer Club e.V.</publisherName></publisher></publishers>
            <publicationYear>2017</publicationYear></resource>'''
            # TODO get year from event date
            f.write(metadata)

    if errors != '':
        with open('errors_' + acronym + '.txt', 'w') as error_file:
            error_file.write('\n'.join(errors))


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
                return False
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
