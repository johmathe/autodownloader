#!/usr/bin/python
# This script auto downloads stuff by reading a list in a RSS feed.
# 1. Look for your show in http://ezrss.it/search/index.php
# 2. Add your rss feed into the tvshows.txt file (one feed per line)
# 3. Add the watch and finish feature in your rtorrent confi
# 4. run this script periodically from a cronjob
#
# Author: johan.mathe@gmail.com (Johan Mathe).

# Configuration fields

# TODO(johmathe): prefix all the globals w/ g_
user_emails = ['johan.mathe@gmail.com']
g_feeds_file = '/home/johmathe/autodownload/tvshows2.txt'
destination_path = '/home/johmathe/torrents/watch/'
cache_dir = '/home/johmathe/cache/'
cache_file_urls = 'cache_urls'
cache_file_downloaded = 'cache_finished'
wget_path = '/usr/bin/wget'
send_email = True
sendmail = '/usr/sbin/sendmail'
path_download_completed = '/home/johmathe/public_html/'
mail_subject_download_started = 'New download started'
mail_subject_download_finished = 'New download finished'
mail_body_download_started = 'New download started.\nURL is:\n %s'
mail_body_download_finished = 'A new download is available.\nPath is:\n %s'

import feedparser
import sys
import os
import pickle
import glob
from os import path


def LoadCache(file):
    """Loads a cache file to a datastructure."""
    fd = open(file, 'rb')
    cache = pickle.load(fd)
    fd.close()
    return cache


def SaveCache(file, cache):
    """Saves a datastructure to a cache file."""
    fd = open(file, 'wb')
    pickle.dump(cache, fd)
    fd.close()


def SendEmail(subject, body, destinations):
    """Sends an email to the destination address."""
    for d in destinations:
        p = os.popen('%s -t' % sendmail, 'w')
        p.write('To: %s\n' % d)
        p.write('Subject: %s\n' % subject)
        p.write('\n')
        p.write('%s' % body)
        p.write('\n\nYours friendly, the downloadator')
        p.close()


def CheckForNewDownloads(cache_file, new_dl_path):
    """Checks for new downloads in a dir against a cache file."""
    if path.isfile(cache_file):
        cache_downloaded = LoadCache(cache_file)
    else:
        cache_downloaded = set([])
    files_list = set(glob.glob('%s/*' % new_dl_path))
    new_files = files_list - cache_downloaded
    for f in new_files:
        SendEmail(mail_subject_download_finished,
                  mail_body_download_finished % f, user_emails)
    SaveCache(cache_file, files_list)


def CheckForNewTorrentsToDownload(feeds_file, cache_file, destination):
    """Checks for new torrents to download from a txt file containin rss
    feeds."""
    fd_feeds = open(feeds_file, 'r')
    feeds = [feedparser.parse(f) for f in fd_feeds if f != '\n']

    # We use a cache file to avoid downloading twice the same torrent
    if path.isfile(cache_file):
        cache = LoadCache(cache_file)
    else:
        cache = {}

    for f in feeds:
        torrent_url = f['items'][0]['enclosures'][0]['href']
        # Quick and dirty: call wget. I'm to lazy to do the whole urllib thing.
        # put the torrent url in the watch rtorrent directory
        if torrent_url not in cache:
            wget_string = '%s \"%s\" -P %s' % (wget_path, torrent_url,
                                               destination_path)
            os.system(wget_string)
            cache[torrent_url] = 1
            SendEmail(mail_subject_download_started,
                      mail_body_download_started % torrent_url, user_emails)
    SaveCache(cache_file, cache)

    fd_feeds.close()


def main():
    if not path.isdir(cache_dir):
        print ('cache directory %s does not exist. '
               'Please create it.' % cache_dir)
        sys.exit(1)
    if not path.isfile(g_feeds_file):
        print 'Global configuration doesn\'t seem right. Please edit me.'
        print('Please create %s with a list of RSS feeds containing torrents.'
              % g_feeds_file)
        sys.exit(1)

    CheckForNewTorrentsToDownload(g_feeds_file,
                                  '%s/%s' % (cache_dir, cache_file_urls),
                                  destination_path)
    CheckForNewDownloads('%s/%s' % (cache_dir, cache_file_downloaded),
                         path_download_completed)


main()
