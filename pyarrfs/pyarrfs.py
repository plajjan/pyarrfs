#!/usr/bin/env python
#
# PyarrFS - a RAR reading file system
# Copyright (c) 2010, 2011 Kristian Larsson <kristian@spritelink.net>
#
# This file is license under the X11/MIT license, please see the file COPYING
# distributed with PyarrFS for more details.
#

import os, sys
import errno
import fcntl
import re
import stat
import logging
import logging.handlers

import fuse
import rarfile

__version__         = '0.6.0'
__author__          = 'Kristian Larsson'
__author_email__    = 'kristian@spritelink.net'
__license__         = 'MIT'
__url__             = 'http://labs.spritelink.net/pyarrfs'


# log settings
log_format = "%(levelname)-8s %(message)s"
logger = logging.getLogger()

fuse.fuse_python_api = (0, 2)

fuse.feature_assert('stateful_files', 'has_init')


class Pyarr(fuse.Fuse):
    def __init__(self, *args, **kw):
        logger.info("init!")

        fuse.Fuse.__init__(self, *args, **kw)

        self.debug = False
        self.pydebug = False
        self.foreground = False
        self.root = '/'


    def fsinit(self):
        os.chdir(self.root)




    def access(self, path, mode):
        """Returns whether a user has access to performing 
        """
        logger.info("access -- " + path)

        # test for write access, PyarrFS is incapable of do writes, so no axx
        if mode == os.W_OK:
            return -errno.EACCES

        # allow the rest
        # FIXME: do more granular access control, based on RAR file?
        return

        # this only works for files not inside a rar archive
        if not os.access("." + path, mode):
            return -errno.EACCES

    def getattr(self, path):
        logger.info("getattr -- " + str(path))
        if re.match('.*\.rar$', path):
            logging.debug("getattr: on rar archive for path " + str(path))
            original_stat = os.lstat("." + path)
            fake_stat = fuse.Stat()
            fake_stat.st_mode = stat.S_IFDIR | 0755
            fake_stat.st_ino = 0
            fake_stat.st_dev = 0
            fake_stat.st_rdev = 0
            fake_stat.st_nlink = 2
            fake_stat.st_uid = original_stat.st_uid
            fake_stat.st_gid = original_stat.st_gid
            fake_stat.st_size = 4096
            fake_stat.st_atime = original_stat.st_atime
            fake_stat.st_mtime = original_stat.st_mtime
            fake_stat.st_ctime = original_stat.st_ctime
            logging.debug("getattr: returning fake_stat for " + str(path))
            return fake_stat

        elif re.match('.*\.rar/.+', path):
            logging.debug("getattr: we need to check inside rar archive for path " + str(path))
            m = re.match('(.*\.rar)/(.+)', path)
            rar_file = m.group(1)
            rar_path = m.group(2)

            original_stat = os.lstat("." + rar_file)
            rf = rarfile.RarFile(rar_file, 'r', None, None, False)
            try:
                rfi = rf.getinfo(rar_path)
            except:
                # FIXME: add DEBUG log entry
                return -errno.ENOENT

            fake_stat = fuse.Stat()
            fake_stat.st_mode = stat.S_IFREG | 0444
            fake_stat.st_ino = 0
            fake_stat.st_dev = 0
            fake_stat.st_rdev = 0
            fake_stat.st_nlink = 1
            fake_stat.st_uid = original_stat.st_uid
            fake_stat.st_gid = original_stat.st_gid
            fake_stat.st_size = rfi.file_size
            fake_stat.st_blocks = (fake_stat.st_size + 511) / 512
            fake_stat.st_blksize = 4096

            import datetime
            (rft_year, rft_month, rft_day, rft_hour, rft_minute, rft_second) = rfi.date_time
            rft_time = datetime.datetime(rft_year, rft_month, rft_day, rft_hour, rft_minute, rft_second)
            fake_stat.st_atime = int(rft_time.strftime('%s'))
            fake_stat.st_mtime = int(rft_time.strftime('%s'))
            fake_stat.st_ctime = int(rft_time.strftime('%s'))
            logger.debug("getattr: returning fake_stat for " + str(rar_path) + " inside rar " + str(rar_file))
            return fake_stat
     
        logger.debug("getattr: returning normal os.lstat() for path " + str(path))
        return os.lstat("." + path)

    # get a directory listing
    # doesn't need changes in yarrfs compatibility mode
    def readdir(self, path, offset):
        logger.info("readdir -- path: " + str(path) + "  offset: " + str(offset) )
        dirent = [ '.', '..' ]

        if re.match('.*\.rar$', path):
            logger.debug("readdir: on rar archive, using rarfile")
            rf = rarfile.RarFile(path, 'r', None, None, False)
            for e in rf.namelist():
                dirent.append(str(e))
        else:
            logger.debug("readdir: normal dir, using os.listdir()")
            try:
                os.listdir("." + path)
            except:
                return

            for e in os.listdir("." + path):
                dirent.append(e)

        for e in dirent:
            yield fuse.Direntry(e)


    def readlink(self, path):
        logger.info("readlink -- " + path)
        return os.readlink("." + path)

    def statfs(self):
        logger.info("statfs -- " + path)
        return os.statvfs(".")


    class PyarrFile(object):
        def __init__(self, path, flags, *mode):
            # Enabling direct_io disables the kernels page cache.
            # Since the content of our RAR files should be pretty stable, we do
            # NOT enable this, ie we allow the kernel to cache all data.
            # This means we get both the .rar file and the file inside the RAR 
            # archive in the block cache which might affect performance 
            # negatively. On the other hand, the kernel could purge the .rar 
            # file from its block cache and just keep the inside file. 
            # It's likely mostly a performance thing. I'm guessing it's good
            # to let the kernel decide on what to cache and what not too, so we
            # set it to False. Some benchmarking should really be done to prove
            # either setting is better than the other
            self.direct_io = False
            # keep_cache means the kernel is allowed to cache content of a file
            # after its been closed an reopened. You only want to disable this
            # if the content of the file might change without the kernel knowing
            # about it, which would be typical for a networked file system.
            # That's not the case with PyarrFS so we enable it.
            self.keep_cache = True
            # TODO: *embarrassing*, PyarrFile is initiated for all files and
            # not just .rar files but code assumes it is always a rar file and
            # so it is unable to work with normal files
            # FIXME: other .rar file names?
            m = re.match(r'(.*\.rar)/(.+)', path, re.IGNORECASE)
            if m is not None:   # rar file!
                self.rar_file = m.group(1)
                self.rar_path = m.group(2)
                self.rf = rarfile.RarFile('.' + self.rar_file, 'r', None, None, False)
                self.file = self.rf.open(self.rar_path)
            else:
                self.file = open('.' + path)
            self.fd = 0

        def read(self, length, offset):
            self.file.seek(offset)
            return self.file.read(length)

        def release(self, flags):
            self.file.close()


    def main(self, *a, **kw):
        self.file_class = self.PyarrFile
        return fuse.Fuse.main(self, *a, **kw)


def main():
    usage = """
PyarrFS mirror the filesystem tree from some point on, allowing RAR archives to be treated as directories and files within those RAR archives to be read as regular files.

""" + fuse.Fuse.fusage

    server = Pyarr(version="PyarrFS 0.1",
                 usage=usage)

    # TODO: what does multithreaded really mean?
    #       just run many requests in parallel? We have no real dependancies
    #       between calls so we could probably enable this to increase
    #       throughput in environments with lots of simultaneous requests.
    #       Looks like it needs PyarrFile to be locked, what's the point then?
    server.multithreaded = False

    server.parser.add_option('-r', '--root', dest='root', metavar="PATH", default=server.root, help="mirror filesystem from under PATH [default: %default]")
    server.parser.add_option('-D', '--pydebug', action='store_true', dest='pydebug', default=False, help="enable debug for just PyarrFS (not FUSE) (implies -f)")
    server.parse(values=server, errex=1)

    # always log to syslog
    log_syslog = logging.handlers.SysLogHandler(address = '/dev/log')
    log_syslog.setFormatter(logging.Formatter(log_format))
    log_syslog.setLevel(logging.WARNING)
    logger.addHandler(log_syslog)

    opts = {}
    # FIXME: why doesn't optdict work?
    for o in server.parser.fuse_args.optlist:
        opts[o] = True

    if server.pydebug:
        server.parser.fuse_args.modifiers['foreground'] = True

    if server.parser.fuse_args.modifiers['foreground'] or opts.has_key('debug') or server.pydebug:
        log_stream = logging.StreamHandler()
        log_stream.setFormatter(logging.Formatter("%(asctime)s: " + log_format))
        log_stream.setLevel(logging.DEBUG)
        if opts.has_key('debug') or server.pydebug:
            # FIXME: this isn't working, why? we only get WARNING messages
            log_stream.setLevel(logging.DEBUG)
        logger.addHandler(log_stream)

    # and go!
    server.main()




if __name__ == '__main__':
    main()


#
# vim: et ts=4 :
#
