################################
# Author: hambster@gmail.com
# Date: 2015/09/19
################################
import argparse
import httplib
import re
import os
import urllib
import hashlib
import sys
from HTMLParser import HTMLParser

HOST_NAME = 'thecodinglove.com'
URI_PATTERN = '/page/{0}'
STAT_NONE = 0x0000
STAT_H3 = 0x0001
STAT_ANCHOR = 0x0002
STAT_BODY_TYPE = 0x0004
STAT_FOOTER = 0x0008
TAG_H3 = 'h3'
TAG_IMG = 'img'
TAG_DIV = 'div'
TAG_ANCHOR = 'a'
ATTR_CLASS = 'class'
ATTR_SRC = 'src'
CLASS_BODY_TYPE = 'bodytype'
CLASS_FOOTER = 'footer'
TEXT = 'text'
IMAGE = 'image'
IMGCAT = 'imgcat'
IMG_DIR = 'img'

class CodingLoveParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.stat = STAT_NONE
        self.item_list = []
        self.curr_item = {}

    def get_item_list(self):
        return self.item_list

    def handle_starttag(self, tag, attrs):
        if TAG_H3 == tag:
            # step into h3
            self.stat |= STAT_H3
        elif TAG_ANCHOR == tag and self.is_stat_enabled(STAT_H3):
            # step into a in h3
            self.stat |= STAT_ANCHOR
        elif TAG_IMG == tag and self.is_stat_enabled(STAT_BODY_TYPE):
            # step into img in div with class as bodytype
            img_src = self.get_attr_value(ATTR_SRC, attrs)
            self.curr_item[IMAGE] = img_src
            # insert item into list
            self.item_list.append(self.curr_item)
            self.curr_item = {}
        elif TAG_DIV == tag:
            class_val = self.get_attr_value(ATTR_CLASS, attrs)
            if CLASS_BODY_TYPE == class_val:
                # div with class as bodytype
                self.stat |= STAT_BODY_TYPE
            elif CLASS_FOOTER == class_val:
                # div with class as footer
                self.stat |= STAT_FOOTER

    def handle_endtag(self, tag):
        if TAG_H3 == tag and self.is_stat_enabled(STAT_H3):
            self.stat &= ~STAT_H3
        elif TAG_ANCHOR == tag and self.is_stat_enabled(STAT_ANCHOR):
            self.stat &= ~STAT_ANCHOR
        elif TAG_DIV == tag:
            if STAT_BODY_TYPE == self.is_stat_enabled(STAT_BODY_TYPE):
                self.stat &= ~STAT_BODY_TYPE
            elif STAT_FOOTER == self.is_stat_enabled(STAT_FOOTER):
                self.stat &= ~STAT_FOOTER
            
    def handle_data(self, data):
        if self.is_stat_enabled(STAT_H3) and self.is_stat_enabled(STAT_ANCHOR):
            self.curr_item[TEXT] = data

    def is_stat_enabled(self, stat_to_check):
        ret = False
        if stat_to_check == (self.stat & stat_to_check):
            ret = True

        return ret

    def get_attr_value(self, attr_name, attrs):
        ###################################
        # get value of given attr name,
        # return none if attr not exists
        ###################################
        ret = None
        for attr in attrs:
            if attr[0] == attr_name:
                ret = attr[1]
                break

        return ret

def download_image(img_url, file_path):
    if os.path.exists(file_path):
        return

    gif_file = urllib.URLopener()
    gif_file.retrieve(img_url, file_path)
    
def show_image(image_path):
    imgcat_bin = get_base_dir() + "/" + IMGCAT
    os.system(imgcat_bin + " " + image_path)

def get_base_dir():
    return os.path.dirname(os.path.abspath(__file__))

def get_page_content(page_idx = 1):
    ret = None
    try:
        conn = httplib.HTTPConnection(HOST_NAME)
        conn.request(
            "GET",
            get_page_uri(page_idx)
        )
        rsp = conn.getresponse()
        ret = rsp.read()
    except:
        ret = None

    return ret

def get_page_uri(page_idx = 1):
    ret = "/"
    if 1 < page_idx:
        ret = URI_PATTERN.format(page_idx)

    return ret

def parse_args():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--page', type=int, help='index of page to show')
    ret = arg_parser.parse_args()

    return ret

def start():
    args = parse_args()
    rsp_text = get_page_content(args.page)
    codinglove_parser = CodingLoveParser()
    codinglove_parser.feed(rsp_text)
    item_list = codinglove_parser.get_item_list()
    img_dir = get_base_dir() + '/' + IMG_DIR
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)

    for item in item_list:
        if TEXT not in item:
            continue

        sha256_handle = hashlib.sha256()
        sha256_handle.update(item[IMAGE])
        image_path = img_dir + "/" + sha256_handle.hexdigest() + ".gif"
        download_image(item[IMAGE], image_path)
        print item[TEXT]
        show_image(image_path)

if '__main__' == __name__:
    start()
