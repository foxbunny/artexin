"""
fetch.py: fetch and process content from the web

Copyright 2014, Outernet Inc.
Some rights reserved.

This software is free software licensed under the terms of GPLv3. See COPYING
file that comes with the source code, or http://www.gnu.org/licenses/gpl.txt.
"""

import os
import shutil
from io import BytesIO
import tempfile
import time
from urllib.request import urlopen

from bs4 import BeautifulSoup
from PIL import Image
from selenium import webdriver

from . import __version__ as _version, __author__ as _author


__version__ = _version
__author__ = _author
__all__ = ('fetch_content', 'fetch_rendered', 'fetch_image', 'get_parsed')


AJAX_TIMEOUT = 5  # 5 seconds
GHOST_LOG_PATH = '/dev/null'  # Set this to a file to enable logging

IEXTENSIONS = {  # Image file extensions
    'BMP':   '.bmp',
    'DCX':   '.dcx',
    'EPS':   '.eps',
    'GIF':   '.gif',
    'IM':    '.im',
    'JPEG':  '.jpg',
    'PCD':   '.pcd',
    'PCX':   '.pcx',
    'PDF':   '.pdf',
    'PNG':   '.png',
    'PPM':   '.pbm',
    'PSD':   '.psd',
    'TIFF':  '.tif',
    'XBM':   '.xbm',
    'XPM':   '.xpm',
}


def fetch_content(url):
    """ Fetches content from specified URL

    The response is a raw bytestring::

        >>> c = fetch_content('http://www.example.com/')
        >>> b'<title>Example Domain</title>' in c
        True

    Failures are propagated as they are without any error trapping::

        >>> import urllib
        >>> try:
        ...     fetch_content('http://nonexistent/')
        ...     assert False, "Did not raise an exception"
        ... except urllib.error.URLError:
        ...     pass

    :param url:     Document's URL
    :returns:       Document contents as bytestring
    """
    return urlopen(url).read()


def fetch_rendered(url):
    """ Fetch content using headless browser

    The difference between this function and ``fetch_content()`` is that this
    function will render the page using QT4 WebKit browser instead of simply
    donwloading the HTML. This function is therefore more resource-intensive,
    but yields better results for pages that use JavaScript to modify the DOM
    in a significant way (loads relevant images or content, for instance).

    Let's compare the output of ``fetch_content()`` and ``fetch_rendered()``
    using a test page for Crowbar software::

        >>> url = 'http://simile.mit.edu/crowbar/test.html'
        >>> c = fetch_content(url)
        >>> s = BeautifulSoup(c)
        >>> s.h1.string
        'Hi lame crawler'
        >>> c = fetch_rendered(url)
        >>> s = BeautifulSoup(c)
        >>> s.h1.string
        'Hi Crowbar!'

    :param url:     Document's URL
    :returns:       Document contents as bytestring
    """
    driver = webdriver.PhantomJS(service_log_path=GHOST_LOG_PATH)
    driver.get(url)
    time.sleep(AJAX_TIMEOUT)  # Wait for AJAX events to occur
    html = driver.page_source
    driver.quit  # This is correct usage, not a function call by design
    return html


def fetch_image(url, path):
    """ Fetches image from given URL

    When image cannot be fetched or not usable, it propagates appropriate
    exceptions from ``urllib2`` or Pillow/PIL.

    Example::

        >>> url = 'https://www.outernet.is/img/logo.png'
        >>> fmt, full_path = fetch_image(url, '/tmp/logo')
        >>> fmt
        'PNG'
        >>> full_path
        '/tmp/logo.png'

        # Trying to fetch non-existent image
        >>> url = 'http://nonexistent/'
        >>> import urllib
        >>> try:
        ...     fetch_image(url, '/tmp/logo')
        ...     assert False, "Did not raise an exception"
        ... except urllib.error.URLError:
        ...     pass


        # Trying to fetch something that isn't a file
        >>> url = 'http://www.outernet.is/'
        >>> fetch_image(url, '/tmp/nonimage')
        Traceback (most recent call last):
        OSError: ...

    :param url:     Image's URL
    :param path:    Image path without extension
    :returns:       Tuple containing image format and temporary image path
    """
    content = fetch_content(url)

    # Store the content in temporary file
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.write(content)
    tmp.close()
    assert os.path.exists(tmp.name), 'Missing temp file %s' % tmp.name

    # Open the content as image and deduce its format
    img = Image.open(BytesIO(content))
    img.verify()  # caller will have to trap exceptions
    fmt = img.format

    # Calculate the full path of the image and move the temporary file there
    full_path = "%s%s" % (path, IEXTENSIONS[fmt])
    shutil.move(tmp.name, full_path)
    assert os.path.exists(full_path), 'Missing image at %s' % full_path
    assert not os.path.exists(tmp.name), 'Temp file not removed'

    return fmt, full_path


def get_parsed(url):
    """ Fetches content from specified URL and returns beautiful soup

    This function retuns a BeautifulSoup-wrapped object representing the
    fetched HTML content.

    For instance::

        >>> b = get_parsed('http://www.example.com/')
        >>> isinstance(b, BeautifulSoup)
        True

    :param url:                 Document's URL
    :returns BeautifulSoup:     Parsed document as Soup object
    """
    c = fetch_content(url)
    return BeautifulSoup(c)


if __name__ == '__main__':
    import doctest
    # We use optionflags=doctest.IGNORE_EXCEPTION_DETAIL to ignore the
    # slight differences between Python 2.7.x and Python 3.x URLError
    # exception.
    flags = doctest.IGNORE_EXCEPTION_DETAIL | doctest.ELLIPSIS
    doctest.testmod(optionflags=flags)
