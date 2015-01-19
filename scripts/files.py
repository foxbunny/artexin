#!/usr/bin/env python

import sys
import os
from os.path import dirname, join, abspath
import json
import zipfile
from datetime import datetime
import logging
from logging.config import dictConfig as log_config

import bottle
from bottle import request, template

PKGDIR = abspath(dirname(os.path.realpath(__file__)))
PROJDIR = join(PKGDIR, '..')
CONFPATH = join(PKGDIR, '../artexin_webui/artexin.ini')

bottle.default_app().config.load_config(CONFPATH)
config = bottle.default_app().config
sys.path.insert(0, PROJDIR)

content_dir = join(PROJDIR, config['content.contentdir'])

from artexin_webui.utils import squery

db = squery.Database(join(PROJDIR, config['database.path']))

TABLE_COLS = (
    'id', 'md5', 'url', 'title', 'archive', 'is_sponsored', 'is_partner', 
    'partner', 'created', 'updated')
METADATA_KEYS = (
    'url', 'title', 'images', 'created', 'is_partner', 'is_sponsored',
    'archive', 'partner')
COL_LABELS = {
    'id': 'ID', 
    'md5': 'md5', 
    'url': 'URL', 
    'title': 'Title', 
    'archive': 'Archive', 
    'is_sponsored': 'Sponsored?', 
    'is_partner':'Partner?', 
    'partner': 'Partner Organization', 
    'created': 'Date Created', 
    'updated': 'Last Update', 
}

ADD_QUERY = """
REPLACE INTO content
(md5, url, title, created, updated, is_partner, is_sponsored, archive, 
partner, images)
VALUES
(:md5, :url, :title, :created, :updated, :is_partner, :is_sponsored, 
:archive, :partner, :images);
"""


class ContentError(BaseException):
    """ Exception related to content decoding, file extraction, etc """

    def __init__(self, msg, path):
        self.message = msg
        self.path = path
        super(ContentError, self).__init__(msg)


def extract_file(path, filename):
    """ Extract a single file from a zipball into memory
    This function is cached using in-memory cache with arguments as keys.
    You can read more about the caching in Python documentation.
    https://docs.python.org/3/library/functools.html#functools.lru_cache

    :param path: path to the zip file
    :param filename: name of the file to extract
    :returns: two-tuple in ``(metadata, content)`` format, containing
    ``zipfile.ZipInfo`` object and file content respectively 
    """

    try:
        with open(path, 'rb') as f:
            with zipfile.ZipFile(f) as content:
                metadata = content.getinfo(filename)
                content = content.open(filename, 'r').read()
    except zipfile.BadZipfile:
        raise ContentError("'%s' is not a valid zipfile" % path, path)
    except Exception as err:
        raise ContentError("'%s' could not be opened: %s" % (path, err), path)
    return metadata, content

def get_file(path, filename):
    """ Extract a single file from a zipball into memory
    This function is cached using in-memory cache with arguments as keys.
    You can read more about the caching in Python documentation.
    https://docs.python.org/3/library/functools.html#functools.lru_cache

    :param path: path to the zip file
    :param filename: name of the file to extract
    :extractxtractreturns: two-tuple in ``(metadata, content)`` format, containing
    ``zipfile.ZipInfo`` object and file content
    respectively
    """
   
    # TODO: Add caching
    dirname = os.path.basename(os.path.splitext(path)[0])
    filename = '%s/%s' % (dirname, filename) # we always use forward slash
    return extract_file(path, filename)

def get_metadata(path):
    """ Extract metadata file from zipball and return its content
    The extraction happens in-memory, so no files are written out. Files
    without metadata will be treated as bad files, but will not be
    automatically removed. Decision to remove such files is left to the user.

    :param path: path to the zip file
    :returns: metadata dict
    """
    
    meta_filename = config['content.metadata']
    metadata, content = get_file(path, meta_filename)
    try: 
        content = str(content.decode('utf-8'))
    except UnicodeDecodeError as err:
        raise ContentError("Failed to decode metadata: '%s'" % err)
    try:
        return json.loads(content)
    except ValueError as err:
        raise ContentError("Bad metadata for '%s'" % path, path)

def add_to_database(files):
    """
    Takes list of zip file names (eg. md5.zip) and adds metadata from info.json
    to the database, adding potentially empty keys from METADATA_KEYS

    :param files: takes list of zip file names
    """
    
    # TODO add filesize to meta
    metadata = []
    for md5 in files:
        path = join(content_dir, '%s' % md5)
        meta = get_metadata(path)
        for key in METADATA_KEYS:
            if key not in meta:
                meta[key] = None
        meta['md5'] = md5
        meta['updated'] = datetime.now()
        metadata.append(meta)
    with db.transaction() as cur:
        cur.executemany(ADD_QUERY, metadata)
    logging

def main():
    """
    Main function, lists files in content_dir and puts them into
    add_to_database. No arguments taken, all configuration is done in
    artexin_webui/artexin.ini
    """
    file_list = []
    for f in os.listdir(content_dir):
        file_list.append(f)
    add_to_database(file_list)
    logging.debug("Finished adding metadata successfully")


if __name__ == '__main__':
    main()
