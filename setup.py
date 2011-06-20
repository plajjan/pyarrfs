#!/usr/bin/env python

from distutils.core import setup

from pyarrfs import pyarrfs

ver = pyarrfs.__version__
long_desc = open("README").read()
short_desc = long_desc.split('\n')[0].split(' - ')[1].strip()

setup(
    name = 'pyarrfs',
    version = pyarrfs.__version__,
    description = short_desc,
    long_description = long_desc,
    author = pyarrfs.__author__,
    license = pyarrfs.__license__,
    author_email = pyarrfs.__author_email__,
    url = pyarrfs.__url__,
    scripts = ['bin/pyarrfs'],
    packages = ['pyarrfs'],
    keywords = ['rar', 'fuse'],
    requires = ['rarfile (>= 2.3)'],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2',
        'Topic :: System :: Archiving :: Compression',
        'Topic :: System :: Filesystems'
    ]
)

