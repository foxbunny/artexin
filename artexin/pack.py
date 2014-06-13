"""
pack.py: package files for transport over Outernet

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import os
import shutil
import zipfile
import hashlib
import tempfile
import datetime

from fetch import fetch_rendered
from extract import *


__author__ = 'Outernet Inc <branko@outernet.is>'
__version__ = 0.1
__all__ = ('zipdir', 'collect')


COMPRESSION = zipfile.ZIP_DEFLATED
BASE_DIR = tempfile.gettempdir()
TS_FORMAT = '%Y-%m-%d %H:%M:%S UTC'


def zipdir(path, dirpath):
    """ Create a zipball at ``path`` containing the directory at ``dirpath``

    :param path:        Path of the zipball
    :param dirpath:     Path of the directory to zip up
    """
    # Get the path of the directory's parent
    basepath = os.path.dirname(dirpath)

    # Compress all directory contents
    with zipfile.ZipFile(path, 'w', COMPRESSION) as zipball:
        for content in os.listdir(dirpath):
            cpath = os.path.join(dirpath, content)
            if os.path.isdir(cpath):
                continue  # Skip directories
            zipball.write(cpath, os.path.relpath(cpath, basepath))
        zipball.testzip()


def collect(url, prep=[], base_dir=BASE_DIR, keep_dir=False):
    """ Collect at ``url`` into a directory within ``base_dir`` and zip it

    The directory is created within ``base_dir`` that is named after the md5
    checksum of the ``identifier``.

    If the target directory already exists, it will be unlinked first.

    :param url:         Identifier for the batch (usually URL of the page)
    :param prep:        Iterable containing HTML preprocessors from
                        ``artexin.preprocessors``
    :param base_dir:    Base directory in which to operate
    :param keep_dir:    Keep the directory in which content was collected
    :returns:           Full path of the newly created zipball
    """
    # Create the destination directory
    md5 = hashlib.md5()
    md5.update(url)
    checksum = md5.hexdigest()
    dest = os.path.join(base_dir, checksum)
    if os.path.exists(dest):
        shutil.rmtree(dest)
    os.mkdir(dest)

    # Fetch and prepare the HTML
    page = fetch_rendered(url)
    timestamp = datetime.datetime.utcnow().strftime(TS_FORMAT)
    for preprocessor in prep:
        page = preprocessor(page)
    title, html = extract(page)
    html = strip_links(html)

    # Process images
    html, images = process_images(html, url, imgdir=dest)

    # Write file metadata
    with open(os.path.join(dest, 'info.txt'), 'w') as f:
        f.write(('%s\n%s\n' % (title, timestamp)).encode('utf-8'))

    # Write the HTML file
    with open(os.path.join(dest, 'index.html'), 'w') as f:
        f.write(html.encode('utf-8'))

    # Create a zip file
    zippath = os.path.join(base_dir, '%s.zip' % checksum)
    zipdir(zippath, dest)

    # Clean-up
    if not keep_dir:
        shutil.rmtree(dest)

    return zippath


if __name__ == '__main__':
    import doctest
    doctest.testmod()