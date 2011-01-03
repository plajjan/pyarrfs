#!/usr/bin/python

import unittest
import math
import random
import rarfile
import os, sys


class PyarrCheck(unittest.TestCase):

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

		# make sure mount dir is empty
		os.system('fusermount -q -z -u ' + self.rarmntdir)
		try:
			os.system(self.pyarrpath + ' ' + self.rarmntdir)
		except:
			pass

		filedata = [
				[ 'test1',
					'this is testfile1 bla bla bla bla bla bla bla bla bla bla bla bla bla bla bla bla bla bla bla bla bla bla bla bla bla bla bla bla bla bla bla bla bla\n' ],
				[ 'test2',
					'crap crap crap crap\n' ]
				]
		filedata.append(['test3', self.generate_content(200000)])
		self.files = []
		for entry in filedata:
			self.files.append(entry[0])

		self.create_test_files(filedata)

		self.uncompressed_rar_archive = 'testarchive1.rar'
		self.create_uncompressed_rar_archive('testarchive1.rar', self.files)


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
		os.chdir(self.scriptdir)
		os.system('fusermount -q -z -u ' + self.rarmntdir)
		import shutil
#		shutil.rmtree(self.testdir)

	def generate_content(self, size = 0, population = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'):
		result = ''
		for i in xrange(0, size):
			result += str(random.choice(population))
		return result


	def generate_content_code(self, size = 0):
		# round off size to nearest number divisible by 10
		ns = size - ((size + 10) % 10)
		result = ''
		for i in xrange(0, size):
			result += "$%09d" % (i)
		return result




	def test_read_sequential(self):
		for file in self.files:
			rar_file = os.path.normpath(os.path.join(self.rarmntdir, '.' + self.testarchivedir, self.uncompressed_rar_archive, file))
			raw_file = os.path.normpath(os.path.join(self.testfiledir, file))

			rawf = open(raw_file, 'r')
			rarf = open(rar_file, 'r')
			self.assertEqual(rarf.read(), rawf.read(), 'mismatch in sequential read')
			rarf.close()
			rawf.close()


	def test_seek_whence0_1(self):
		"""Single seek from start (whence = 0) to random location in file
		"""
		for file in self.files:
			rar_file = os.path.normpath(os.path.join(self.rarmntdir, '.' + self.testarchivedir, self.uncompressed_rar_archive, file))
			raw_file = os.path.normpath(os.path.join(self.testfiledir, file))

			file_size = os.path.getsize(raw_file)
			rarf = open(rar_file, 'r')
			rawf = open(raw_file, 'r')
			for i in xrange(0, 10000):
				byte = random.randrange(0, file_size)
				rawf.seek(byte)
				rarf.seek(byte)
				self.assertEqual(rarf.read(1), rawf.read(1), 'mismatch in seek (whence = 0) test 1')
			rarf.close()
			rawf.close()


	def test_seek_whence0_2(self):
		"""Two reads, first from start (whence = 0) to random byte in first half of file and second seek() from start (whence = 0) to second half of file
		"""
		for file in self.files:
			rar_file = os.path.normpath(os.path.join(self.rarmntdir, '.' + self.testarchivedir, self.uncompressed_rar_archive, file))
			raw_file = os.path.normpath(os.path.join(self.testfiledir, file))

			file_size = os.path.getsize(raw_file)
			rarf = open(rar_file, 'r')
			rawf = open(raw_file, 'r')
			for i in xrange(0, 10000):
				byte = random.randrange(0, math.floor(file_size/2))
				rawf.seek(byte)
				rarf.seek(byte)
				self.assertEqual(rarf.read(1), rawf.read(1), 'mismatch in seek (whence = 0) test 2')
				byte = random.randrange(math.floor(file_size/2), file_size)
				rawf.seek(byte)
				rarf.seek(byte)
				self.assertEqual(rarf.read(1), rawf.read(1), 'mismatch in seek (whence = 0) test 2')
			rarf.close()
			rawf.close()


	def test_seek_whence0_3(self):
		"""Two reads, first from start (whence = 0) to random byte in second half of file and second seek() from start (whence = 0) to first half of file
		"""
		for file in self.files:
			rar_file = os.path.normpath(os.path.join(self.rarmntdir, '.' + self.testarchivedir, self.uncompressed_rar_archive, file))
			raw_file = os.path.normpath(os.path.join(self.testfiledir, file))

			file_size = os.path.getsize(raw_file)
			rarf = open(rar_file, 'r')
			rawf = open(raw_file, 'r')
			for i in xrange(0, 10000):
				byte = random.randrange(math.floor(file_size/2), file_size)
				rawf.seek(byte)
				rarf.seek(byte)
				self.assertEqual(rarf.read(1), rawf.read(1), 'mismatch in seek (whence = 0) test 3')
				byte = random.randrange(0, math.floor(file_size/2))
				rawf.seek(byte)
				rarf.seek(byte)
				self.assertEqual(rarf.read(1), rawf.read(1), 'mismatch in seek (whence = 0) test 3')
			rarf.close()
			rawf.close()


	def test_seek_whence2_1(self):
		"""Single seek from end (whence = 2) to random location in file
		"""
		for file in self.files:
			rar_file = os.path.normpath(os.path.join(self.rarmntdir, '.' + self.testarchivedir, self.uncompressed_rar_archive, file))
			raw_file = os.path.normpath(os.path.join(self.testfiledir, file))

			file_size = os.path.getsize(raw_file)
			rarf = open(rar_file, 'r')
			rawf = open(raw_file, 'r')
			for i in xrange(0, 10000):
				byte = random.randrange(0, file_size)
				rawf.seek(-byte, 2)
				rarf.seek(-byte, 2)
				self.assertEqual(rarf.read(1), rawf.read(1), 'mismatch in seek (whence = 2) test 1')
			rarf.close()
			rawf.close()


if __name__ == '__main__':
	unittest.main()

