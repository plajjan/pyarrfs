#!/usr/bin/env python
# vim: et ts=4 :
#
# PyarrFS - a RAR reading file system
# Copyright (c) 2010-2012 Kristian Larsson <kristian@spritelink.net>
#
# This file is licensed under the X11/MIT license, please see the file COPYING,
# distributed with PyarrFS for more details.
#

import os, sys
import errno
import fcntl
import re
import stat
import logging
import logging.handlers

try:
    import fuse
except:
    print >> sys.stderr, "You do not have the Python module for FUSE lib installed"
    import os.path
    if os.path.exists('/etc/debian_version'):
        print >> sys.stderr, "HINT: sudo apt-get install python-fuse"
    sys.exit(1)
try:
    import rarfile
except:
    print >> sys.stderr, "You do not have the Python module for the library rarfile installed"
    print >> sys.stderr, "Please use your distributions package manager or easy_install to get it. Note\nthat you need version 2.3 or later. To install using easy_install:\n  easy_install rarfile"
    sys.exit(1)

rarfile.NEED_COMMENTS = 0

__version__         = '0.8.0'
__author__          = 'Kristian Larsson'
__author_email__    = 'kristian@spritelink.net'
__license__         = 'MIT'
__url__             = 'http://labs.spritelink.net/pyarrfs'


# log settings
log_format = "%(levelname)-8s %(message)s"
logger = logging.getLogger()

fuse.fuse_python_api = (0, 2)

fuse.feature_assert('stateful_files', 'has_init')


def isRarFilePath(path):
    if re.match(r'.*\.rar$', path, re.IGNORECASE):
        return True
    return False


def isRarDirPath(path):
    (a, b) = rarDirSplit(path)
    if a is False or b is False:
        return False
    return True

def rarDirSplit(path):
    m = re.match(r'(.*\.rar)/(.+)', path, re.IGNORECASE)
    if m is not None:
        return m.group(1), m.group(2)
    # FIXME: should raise exception instead?
    return False, False


class Pyarr(fuse.Fuse):
    def __init__(self, *args, **kw):
        logger.info("init!")

        fuse.Fuse.__init__(self, *args, **kw)

        self.no_compressed = False
        self.debug = False
        self.pydebug = False
        self.foreground = False
        self.root = '/'



    def fsinit(self):
        """Called once for initialising things after FUSE itself has been brought up
        """
        os.chdir(self.root)



    def access(self, path, mode):
        """Returns whether a user has access to performing certain operations
        """
        logger.info("access -- " + path)

        # test for write access, PyarrFS is incapable of doing writes, so no axx
        if mode == os.W_OK:
            return -errno.EACCES

        # allow the rest
        # FIXME: do more granular access control, based on RAR file?
        if isRarFilePath(path): # it's a rar file
            # writing is already disallowed and for directories we allow both
            # reading and execution for all users, ie all other modes
            return

        if isRarDirPath(path):  # inside rar archive
            # we allow access to everything (except write, which has already
            # been disallowed) inside rar files
            return

        # files not inside of a rar archive, do passthrough to os.access()
        if not os.access('.' + path, mode):
            return -errno.EACCES



    def getattr(self, path):
        """FS equivalent of stat - returns attributes for object at path
        """
        logger.info("getattr -- " + str(path))
        if isRarFilePath(path): # is a rarfile
            logging.debug("getattr: on rar archive for path " + str(path))

            # if we run with the no_compressed option and files in a rar file
            # are compressed, we just present it as a ordinary directory
            rf = rarfile.RarFile(path)
            for n in rf.namelist():
                inf = rf.getinfo(n)
                if self.no_compressed and int(chr(inf.compress_type)) > 0:
                    return os.lstat('.' + path)

            original_stat = os.lstat('.' + path)
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

        elif isRarDirPath(path):    # is inside a rar file
            logging.debug("getattr: we need to check inside rar archive for path " + str(path))
            (rar_file, rar_path) = rarDirSplit(path)

            original_stat = os.lstat('.' + rar_file)
            rf = rarfile.RarFile('.' + rar_file, 'r', None, None, False)
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
            if rft_second > 59:
                rft_second = 59
            rft_time = datetime.datetime(rft_year, rft_month, rft_day, rft_hour, rft_minute, rft_second)
            fake_stat.st_atime = int(rft_time.strftime('%s'))
            fake_stat.st_mtime = int(rft_time.strftime('%s'))
            fake_stat.st_ctime = int(rft_time.strftime('%s'))
            logger.debug("getattr: returning fake_stat for " + str(rar_path) + " inside rar " + str(rar_file))
            return fake_stat
     
        # normal file outside of any rar file
        logger.debug("getattr: returning normal os.lstat() for path " + str(path))
        return os.lstat('.' + path)



    def readdir(self, path, offset):
        """readdir - return directory listing
        """
        logger.info("readdir -- path: " + str(path) + "  offset: " + str(offset) )
        dirent = [ '.', '..' ]

        if isRarFilePath(path):
            logger.debug("readdir: on rar archive, using rarfile")
            rf = rarfile.RarFile('.' + path, 'r', None, None, False)
            for e in rf.namelist():
                dirent.append(str(e))
        else:
            logger.debug("readdir: normal dir, using os.listdir()")
            try:
                os.listdir('.' + path)
            except:
                return

            for e in os.listdir('.' + path):
                dirent.append(e)

        for e in dirent:
            yield fuse.Direntry(e)



    def readlink(self, path):
        """ path is a symbolic link and readlink returns where it points too

            Symbolic links are not supported within rar files and so we will
            never find one there, thus this is just a wrapper for the normal os
            call readlink().
        """
        logger.info("readlink -- " + path)
        return os.readlink('.' + path)



    def statfs(self):
        # TODO: what is this used for? ;)
        logger.info("statfs -- " + path)
        return os.statvfs('.')



    class PyarrFile(object):
        """ Class representing a file opened somewhere in a PyarrFS file system

            Returning a class to represent a file will result in stateful
            handling of the file from FUSE. The instantiated object will
            persist over the entire period the file is open and any state held
            within will thus also persist.

            This class is used both for non-rar files as well as rar files and
            thus needs to check what kind of file we're dealing with.
        """
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

            if isRarDirPath(path):
                (rar_file, rar_path) = rarDirSplit(path)
                self.rf = rarfile.RarFile('.' + rar_file, 'r', None, None, False)
                self.file = self.rf.open(rar_path)
            else:
                self.file = open('.' + path)


        def read(self, length, offset):
            """ read length amount of data from a file and from a given offset
            """
            self.file.seek(offset)
            return self.file.read(length)


        def release(self, flags):
            """ release, or close, a file
            """
            self.file.close()



    def main(self, *a, **kw):
        self.file_class = self.PyarrFile
        return fuse.Fuse.main(self, *a, **kw)




def main():
    usage = """
PyarrFS mirror the filesystem tree from some point on, allowing RAR archives to be treated as directories and files within those RAR archives to be read as regular files.

""" + fuse.Fuse.fusage

    server = Pyarr(version="PyarrFS " + __version__,
                 usage=usage)

    # TODO: what does multithreaded really mean?
    #       just run many requests in parallel? We have no real dependancies
    #       between calls so we could probably enable this to increase
    #       throughput in environments with lots of simultaneous requests.
    #       Looks like it needs PyarrFile to be locked, what's the point then?
    server.multithreaded = False

    server.parser.add_option('-r', '--root', dest='root', metavar="PATH", default=server.root, help="mirror filesystem from under PATH [default: %default]")
    server.parser.add_option('-n', '--no-compressed', action='store_true', dest='no_compressed', default=False, help="Disable compressed files")
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


