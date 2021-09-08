#!/usr/bin/python3

#=======================================================
#
#	Request Injector by Bonifield (https://github.com/bonifield)
#
#	v0.9.3
#	Last Updated: 2021-09-08
#
#	requestinjector.py -u "http://example.com/somepath/a/b/c" -w "/path/to/wordlist.txt" -t 10 -m -r 2 \
#	-p '{"http": "http://127.0.0.1:8080", "https": "https://127.0.0.1:8080"}' \
#	-H '{"Content-Type": "text/plain"}' \
#	--color --simple_output
#
#	or import as a module (from requestinjector import RequestInjector)
#
#=======================================================

import argparse
import json
import os
import sys
import threading
import queue
import sys
import time
from pathlib import Path
import requests
from urllib.parse import urlparse
# suppress warning
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



class Filler(threading.Thread):
	"""fills a queue with words from the provided wordlist"""
	def __init__(self, queue, wordlist):
		threading.Thread.__init__(self)
		self.setDaemon(True)
		self.name = threading.current_thread().name
		self.queue = queue
		self.wordlist = wordlist
		# check if the wordlist is a list or string, and if it's a string, check if it's a file that exists
		if isinstance(self.wordlist, list):
#			print("list")
			self.wordtype = "list"
		elif isinstance(self.wordlist, str):
			if Path(self.wordlist).is_file():
#				print("file")
				self.wordtype = "file"
		else:
			print("please provide a filename string or a list of words to request")
			sys.exit(2)

	def run(self):
		if self.wordtype == "file":
#			print(f"\033[95m{self.name}\033[0m opening {self.wordlist}") # purple
			with open(self.wordlist, "r") as f:
				for line in f:
					line = str(line).strip()
					self.queue.put(line)
#					print(f"\033[95m{self.name}\033[0m placed {line} into queuein") # purple
			f.close()
#			print(f"\033[95m{self.name}\033[0m closed {self.wordlist}") # purple
		if self.wordtype == "list":
			for i in self.wordlist:
				i = str(i).strip()
				self.queue.put(i)
#				print(f"\033[95m{self.name}\033[0m placed {i} into queuein") # purple



class PathWorker(threading.Thread):
	"""pulls a word from the queue, requests the URL+word for each URL, and places the results into the output queue"""
	def __init__(self, queuein, queueout, urls, proxy={}, headers={}, retries=None, url_encode=False):
		threading.Thread.__init__(self)
		self.setDaemon(True)
		self.queuein = queuein
		self.queueout = queueout
		self.urls = urls
		self.header_default_useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0"
		self.header_default_accept = "text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8"
		if len(headers) == 0:
			self.headers = {'User-Agent':self.header_default_useragent, 'Accept':self.header_default_accept}
		else:
			self.headers = headers
			if "User-Agent" not in self.headers:
				self.headers["User-Agent"] = self.header_default_useragent
			if "Accept" not in self.headers:
				self.headers["Accept"] = self.header_default_accept
		self.proxy = proxy
		if retries is None:
			self.retries = 1
		elif isinstance(retries, int):
			self.retries = retries
		else:
			self.retries = 1
		if url_encode:
			self.url_encode = True
		self.name = threading.current_thread().name
		self.bad_domains = {} # tracks domains that raise requests.exceptions.ReadTimeout

	def badDomainCheker(self, domain):
		"""tracks domains that raise requests.exceptions.ReadTimeout"""
		if domain not in self.bad_domains.keys():
			#sys.stderr.write(f"\033[91mINFO {self.name}: BAD DOMAIN ADDED: {domain}\033[0m\n") # red
			self.bad_domains[domain] = 1
		elif domain in self.bad_domains.keys():
			self.bad_domains[domain] += 1
			#sys.stderr.write(f"\033[91mINFO {self.name}: BAD DOMAIN COUNT FOR: {domain} {self.bad_domains[domain]}\033[0m\n") # red

	def makeRequest(self, url, item):
		"""handles web request logic"""
		try:
			# set a flag that determines if the request gets made or not, depending on if a domain is responsive or not
			execute = "yes"
			domain = urlparse(url).netloc
			# check if the domain is in a thread-internal "known bad / unresponsive" dictionary
			if domain in self.bad_domains.keys():
				if self.bad_domains[domain] >= self.retries:
					execute = "no"
			if execute == "yes":
				# extra logic to double-check that the URL has a trailing slash, but ProcessUrlPath should handle this properly
				if not url.endswith("/"):
					url = url + "/"
				# word (current queue item) is appended to the URL here
				url = url+item
#				print(f"\033[94m{self.name}\033[0m requesting website: {url}") # blue
				# make the request, using given (or default) headers, allowing redirects, no TLS validation, given proxies, 3-second timeout, and streaming data
				# stream=True means the response body content is not downloaded until the .content attribute is accessed, plus raw info (IP etc) can be accessed
				# https://docs.python-requests.org/en/master/user/advanced/#body-content-workflow
				r = requests.get(url, headers=self.headers, allow_redirects=True, verify=False, proxies=self.proxy, timeout=3, stream=True)
				# handle response content
				# future: send all content to another object for processing
				ip = r.raw._fp.fp.raw._sock.getpeername() # socket into only accessible if stream=True and before .content attribute is called (note this will be the proxy IP/port if one is used)
				sc = r.status_code
				sz = len(r.content) # length of body content, which should (but will not always) match the Content-Length header
				r.close() # ALWAYS close a streaming connection
				return(f"status_code:{sc} bytes:{sz} word:{item} ip:{ip[0]} port:{ip[1]} url:{url}")
			else:
				return(f"EXCEPTION {self.name}: {url} REASON: requests.exceptions.ReadTimeout EXTRA: hit max internal allowed retries: ({self.retries})") # note this pseudo-exception will get displayed on stderr by Drainer
		except Exception as e:
		#except requests.exceptions.ReadTimeout as e:
			# if the domain generates an exception, increment its counter in the dictionary
			self.badDomainCheker(domain)
			return(f"EXCEPTION {self.name}: {url} REASON: requests.exceptions.ReadTimeout EXTRA: count: {self.bad_domains[domain]}, max allowed: {self.retries}") # note this exception will get displayed on stderr by Drainer

	def run(self):
		while True:
			# get item to work on from first queue
			item = self.queuein.get()
#			print(f"\033[94m{self.name}\033[0m got item from queuein: {item}") # blue
			# process that item for each URL variation
			for url in self.urls:
				result = self.makeRequest(url, item)
				# put the result of each url+item request into the second queue
				self.queueout.put(result)
#				s = f"\033[94m{self.name}\033[0m put item into queueout: {result}" # blue
			# tell queuein the task is finished (for the queue.join() at the end)
			self.queuein.task_done()



class Drainer(threading.Thread):
	"""provides output management"""
	def __init__(self, queue, color=False, output_file="", simple_output=False):
		threading.Thread.__init__(self)
		self.setDaemon(True)
		self.queue = queue
		self.name = threading.current_thread().name
		self.color = color
		self.output_file = output_file
		self.simple_output = simple_output

	def printToTerminal(self, item):
		if "EXCEPTION" not in str(item) and "REASON" not in str(item) and "INFO" not in str(item):
			if self.simple_output or self.color:
				s = str(item).split()[0].split("status_code:")[1]
				u = str(item).split("url:")[1]
				item = s + " " + u
			if self.color:
				if str(item)[0].isdigit():
					item = str(item).split()
					if item[0][0] == "1":
						item[0] = "\033[94m" + item[0] + "\033[0m" # blue + reset code
					elif item[0][0] == "2":
						item[0] = "\033[92m" + item[0] + "\033[0m" # green + reset code
					elif item[0][0] == "3":
						item[0] = "\033[93m" + item[0] + "\033[0m" # yellow + reset code
					elif item[0][0] == "4":
						item[0] = "\033[91m" + item[0] + "\033[0m" # red + reset code
					elif item[0][0] == "5":
						item[0] = "\033[95m" + item[0] + "\033[0m" # purple + reset code
					# rejoin into a single string
					item = " ".join(item)
			print(item)
		else:
			sys.stderr.write(f"{item}\n")

	def run(self):
		"""this emulates output handling"""
		while True:
			item = self.queue.get()
#			print(f"\033[33m{self.name}\033[0m removed from queueout:\t{item}") # gold
			if item is None:
				break
			self.printToTerminal(item)
			self.queue.task_done()



class ProcessUrlPath:
	"""preps URL variations/mutations"""
	def __init__(self, url="", mutate_path=False):
		self.output = []
		self.url = self.run(url)
		self.output.append(self.url)
		if mutate_path:
			self.output = self.mutate(self.url)
			self.output.append(self.url)
			self.output = sorted(list(set(self.output)), key=len)

	def mutate(self, url) -> list:
		"""produces a list of each URL variation based on trimming paths down to the base URL"""
		# example: https://example.internal/a/b/c --> https://example.internal/, https://example.internal/a/, https://example.internal/a/b/, https://example.internal/a/b/c/
		l = []
		u = urlparse(url)
		if len(u.path) > 1 and "/" in u.path:
			pathsplit = [i for i in u.path.split("/") if len(i) > 0] # a leading slash makes an entry 0 bytes long at index 0
			baseurl = u.scheme+"://"+u.netloc+"/" # baseurl now ends with a slash
			l.append(self.run(baseurl))
			for p in pathsplit:
				baseurl = self.run(baseurl+p) # additional checking
				l.append(baseurl)
		# no "else" logic becuase __init__ already puts the checked URL into the list after this function is called
		return(l)

	def run(self, url) -> str:
		"""ensure that a given URL is stripped to just the path, and ends in a trailing slash, ex. https://example.internal/a/b/c --> https://example.internal/a/b/c/"""
		u = urlparse(url)
		p = u.path
		if not p.endswith("/"):
			p = p + "/"
		uu = u.scheme+"://"+u.netloc+p
		return(uu)
		
	def __repr__(self) -> str:
		return(self.url)



class RequestInjector:
	"""main handler to dispatch threaded objects"""
	def __init__(self, url, wordlist, threads=5, mutate_path=False, headers={}, proxy={}, retries=None, url_encode=False, simple_output=False, color=False):
		#self.queuein = queuein
		#self.queueout = queueout
		self.wordlist = wordlist
		self.threads = threads
		self.mutate_path = mutate_path
		self.url = ProcessUrlPath(url=url, mutate_path=mutate_path).output # list
		self.headers = headers
		self.proxy = proxy
		self.retries = retries
		self.url_encode = url_encode
		self.simple_output = simple_output
		self.color = color

	def run(self):
		# this queue gets filled with words from the wordlist
		queuein = queue.Queue()
		# this queue gets filled with the web request results
		queueout = queue.Queue()
		# hold thread objects here to be joined
		threads = []
		# begin loading words into queuein
		f = Filler(queuein, self.wordlist)
		f.name = "Filler"
		f.start()
		threads.append(f)
		# worker threads read from queuein and send results to queueout
		# each thread gets a word and checks it against all URLs
		for i in range(self.threads):
			s = PathWorker(queuein, queueout, urls=self.url, headers=self.headers, proxy=self.proxy, retries=self.retries)
			s.name = f"Worker-{i}"
			s.start()
			threads.append(s)
		# thread to handle output
		d = Drainer(queueout, simple_output=self.simple_output, color=self.color)
		d.name = "Drainer"
		d.start()
		threads.append(d)
		# do not join daemon threads, but do check queue sizes
		# ensure the daemon threads have finished by checking that the queues are empty
		queuein.join()
		#print("\033[33;7mqueuein is empty\033[0m") # gold background
		queueout.join()
		#print("\033[33;7mqueueout is empty\033[0m") # gold background



def tool_entrypoint():
	"""this function handles argparse arguments and serves as the entry_points reference in setup.py"""
	# collect command line arguments
	parser = argparse.ArgumentParser(description="RequestInjector: scan a URL using a given wordlist with optional URL transformations")
	# optional arguments
	parser.add_argument("-H", "--headers", dest="headers", default={}, type=json.loads, help="provide a dictionary of headers to include, with single-quotes wrapping the dictionary and double-quotes wrapping the keys and values, ex. '{\"Content-Type\": \"application/json\"}' (defaults to a Firefox User-Agent and Accept: text/html) *note default is set inside PathWorker class*")
	parser.add_argument("-m", "--mutate_path", dest="mutate_path", action="store_true", help="provide True if all parts of the URL path should be checked")
	parser.add_argument("-p", "--proxy", dest="proxy", default={}, type=json.loads, help="provide a dictionary of proxies to use, with single-quotes wrapping the dictionary and double-quotes wrapping the keys and values, ex. '{\"http\": \"http://127.0.0.1:8080\", \"https\": \"https://127.0.0.1:8080\"}'")
	parser.add_argument("-r", "--retries", dest="retries", default=1, type=int, help="provide the number of times to retry a connection (default 1)")
	parser.add_argument("-t", "--threads", dest="threads", default=10, type=int, help="provide the number of threads to use (default 10)")
	parser.add_argument("--color", dest="color", action="store_true", help="provide True if stdout should have colorized status codes (will force simple_output")
	parser.add_argument("--simple_output", dest="simple_output", action="store_true", help="provide True for simplified output, just status code and URL")
	# required arguments
	req = parser.add_argument_group("required arguments")
	req.add_argument("-u", "--url", dest="url", type=str, help="provide a URL to check", required=True)
	req.add_argument("-w", "--wordlist", dest="wordlist", type=str, help="provide a file location or a Python list containing words/terms to check", required=True)
	# get arguments as variables
	args = vars(parser.parse_args())
	headers = args["headers"]
	mutate_path = args["mutate_path"]
	proxy = args["proxy"]
	retries = args["retries"]
	threads = args["threads"]
	url = args["url"]
	wordlist = args["wordlist"]
	color = args["color"]
	simple_output = args["simple_output"]
	x = RequestInjector(url=url, wordlist=wordlist, threads=threads, mutate_path=mutate_path, headers=headers, proxy=proxy, retries=retries, simple_output=simple_output, color=color) #, simple_output=True)
	x.run()



#=========================================



# this allows the script to be invoked directly (if the repo was cloned, if just this file was downloaded and placed in some bin path, etc)
# note the time message gets sent to stderr, just 2> /dev/null or comment it out if undesired
if __name__ == "__main__":

	# time script execution
	startTime = time.time()

	tool_entrypoint()

	# time script execution
	endTime = time.time()
	totalTime = endTime - startTime
	sys.stderr.write(f"took {totalTime} seconds\n")
	sys.exit(0)