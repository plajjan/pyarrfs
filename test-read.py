#!/usr/bin/python

import unittest
import random
import rarfile
import os, sys


class PyarrCheck(unittest.TestCase):
	files = [ [ './rarmnt/home/kll/Zathura.DVDRip.XviD-DiAMOND/dmd-zathura.rar/dmd-zathura.avi', '/home/kll/Zathura.DVDRip.XviD-DiAMOND/dmd-zathura.avi' ]
			]

	def setUp(self):
		self.scriptdir = os.path.realpath(os.path.dirname(sys.argv[0]))
		_, self.scriptname = os.path.split(sys.argv[0])
		self.scriptpath = os.path.normpath(os.path.join(self.scriptdir, self.scriptname))
		pathname, scriptname = os.path.split(sys.argv[0])
		self.testdir = os.path.join(self.scriptdir, 'rartest')
		self.rarmntdir = os.path.join(self.testdir, 'rarmnt')
		self.testfiledir = os.path.join(self.testdir, 'testfiles')
		self.testarchivedir = os.path.join(self.testdir, 'testarchives')
		self.pyarrpath = '/home/kll/kod/pyarrfs/pyarrfs'

		self.mkdir(self.testdir)
		self.mkdir(self.rarmntdir)
		self.mkdir(self.testfiledir)
		self.mkdir(self.testarchivedir)

#		os.system('fusermount -u ' + self.rarmntdir)
		try:
			os.system(self.pyarrpath + ' ' + self.rarmntdir)
		except:
			pass

	def mkdir(self, path):
		if not os.path.exists(path):
			os.mkdir(path)
			self.assertTrue(os.path.exists(path))

	def create_test_files(self, filedata):
		for entry in filedata:
			filename = entry[0]
			filedata = entry[1]
			f = open(os.path.join(self.testfiledir, filename), 'w')
			f.write(filedata)
			f.close()

	def create_uncompressed_rar_archive(self, rarfile, files):
		os.chdir(self.testarchivedir)
		for file in files:
			filepath = os.path.join(self.testfiledir, file)
			#cmd = 'rar a -inul -ep ' + os.path.join(self.testarchivedir, rarfile) + ' ' + filepath
			cmd = 'rar a -inul -ep -m0 ' + os.path.join(self.testarchivedir, rarfile) + ' ' + filepath
			os.system(cmd)


	def tearDown(self):
		import time
		time.sleep(1)
		os.system('fusermount -z -u ' + self.rarmntdir)
		import shutil
#		shutil.rmtree(self.testdir)

	def generate_content(self, size = 0, population = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'):
		result = ''
		for i in xrange(0, size):
			result += str(random.choice(population))
		return result



	def test_sequential_read(self):
		filedata = [
				[ 'test1',
					'this is testfile1 bla bla bla bla bla\n' ],
				[ 'test2',
					'crap crap crap crap\n' ]
				]
		filedata.append(['test3', self.generate_content(200000)])
		files = []
		for entry in filedata:
			files.append(entry[0])


		self.create_test_files(filedata)
		rar_archive = 'testarchive1.rar'
		self.create_uncompressed_rar_archive('testarchive1.rar', files)
		for file in files:
			rar_file = os.path.normpath(os.path.join(self.rarmntdir, '.' + self.testarchivedir, rar_archive, file))
			raw_file = os.path.normpath(os.path.join(self.testfiledir, file))
			self.verify_read_sequential(rar_file, raw_file)
			self.verify_read_random(rar_file, raw_file)

	def verify_read_sequential(self, rar_file, raw_file):
		file_size = os.path.getsize(raw_file)
		rarf = open(rar_file, 'r')
		rawf = open(raw_file, 'r')
		self.assertEqual(rarf.read(), rawf.read(), 'mismatch in sequential read')
		rarf.close()
		rawf.close()

	def verify_read_random(self, rar_file, raw_file):
		file_size = os.path.getsize(raw_file)
		rarf = open(rar_file, 'r')
		rawf = open(raw_file, 'r')
		for i in xrange(0, file_size):
			byte = random.randrange(0, file_size)
			rawf.seek(byte)
			rarf.seek(byte)
			self.assertEqual(rarf.read(1), rawf.read(1), 'mismatch in random read')
		rarf.close()
		rawf.close()


if __name__ == '__main__':
	unittest.main()

