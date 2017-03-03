import os
import re
import pandas as pd
import dateutil
import logging
import hashlib
import string
import datetime
import time

import bs4
import dateutil.parser

DATA_DIR='/Users/altaf/Datasets/dnmarchives/agora-forums'
MAX_TOPICS = 100000
TRACE_TOPICS = 5000

def str_clean(s):
    return(s.encode('ascii',errors='ignore').strip())

def file_checksum(path, block_size=32*128, hex=False):
    '''
    Block size directly depends on the block size of your filesystem
    to avoid performances issues
    Here I have blocks of 4096 octets (Default NTFS)
    '''
    md5 = hashlib.md5()
    with open(path,'rb') as f:
        for chunk in iter(lambda: f.read(block_size), b''):
             md5.update(chunk)
    if hex:
        return md5.hexdigest()
    return md5.digest()

class Topic(object):
    def __init__(self):
        self.title = None
        self.pages = list()
        self.posters = dict()

    def add_page(self, filename, page_id):
        if page_id in self.pages:
            return

        soup = bs4.BeautifulSoup(open(filename), 'html.parser')
        forumposts = soup.find('div', id='forumposts')

        if not forumposts:
            return

        title = str_clean(forumposts.select("div h3")[0].contents[-1])
        match = re.match(r'^Topic\:(.*?)\(Read \d+ times\)$', title)

        if not match:
            return

        self.title = str_clean(match.group(1))

        for posts in forumposts.find_all('div', class_='post_wrapper'):
            poster = posts.find('div', class_="poster")
            h4 = poster.find('h4')
            poster_tag = h4.find('a')
            if not poster_tag:
                poster_tag = h4

            poster_id = str_clean(poster_tag.get_text())
            if not poster_id in self.posters:
                self.posters[poster_id] = poster_id

        self.pages.append(page_id)

class App(object):

    def __init__(self):
        self.topics = dict()

    def dbg_trace(self):
        num_topics = len(self.topics)

        if num_topics and not (num_topics % TRACE_TOPICS):
            print("Topics %d" % num_topics)

    def run(self):
        folders = os.listdir(DATA_DIR)
        folder_dates = sorted([dateutil.parser.parse(f) for f in folders if re.match(r'^\d{4}-\d{2}-\d{2}$', f)], reverse=True)

        for folder_date in folder_dates:
            if len(self.topics) >= MAX_TOPICS:
                break

            folder = "%4s-%02d-%02d" % (folder_date.year, folder_date.month, folder_date.day)

            #if not re.match(r'^\d{4}-\d{2}-\d{2}$', folder):
            #    continue

            index_php = os.path.join(DATA_DIR, folder, 'index.php')
            if not os.path.exists(index_php):
                continue

            for filename in os.listdir(index_php):
                self.dbg_trace()

                if len(self.topics) >= MAX_TOPICS:
                    break

                match = re.match(r'^topic\,(\d+)\.(\d+)\.html$', filename)
                if not match:
                    continue

                topic_id = int(match.group(1))
                page_id = int(match.group(2))

                if topic_id in self.topics:
                    topic = self.topics[topic_id]
                else:
                    topic = Topic()
                    self.topics[topic_id] = topic

                topic.add_page(os.path.join(index_php, filename), page_id)


if __name__=='__main__':
    print("START: %s" % time.ctime())
    app = App()
    %time app.run()
    print("FINISH: %s" % time.ctime())
