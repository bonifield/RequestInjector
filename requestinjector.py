#!/usr/bin/python3

#=======================================================
#
#	Request Injector by Bonifield (https://github.com/bonifield)
#
#	v0.9.4
#	Last Updated: 2021-09-21
#
#	path mode (-M path):
#		# NOTE - although -w accepts a comma-separated list of wordlists as a string, only the first one will be used for this mode
#			requestinjector.py -u "http://example.com/somepath/a/b/c" \
#			-M path \
#			-w "/path/to/wordlist.txt" \
#			-t 10 \
#			-r 2 \
#			-m \
#			-p '{"http": "http://127.0.0.1:8080", "https": "https://127.0.0.1:8080"}' \
#			-H '{"Content-Type": "text/plain"}' \
#			--color
#
#	arg mode (-M arg) using shotgun attacktype (-T shotgun):
#		# NOTE - shotgun is similar to Burp Suite's sniper and battering ram modes; provide one or more keys, and a single wordlist
#		# NOTE - although -w accepts a comma-separated list of wordlists as a string, only the first one will be used for this attacktype
#		# NOTE - mutations (-m) not yet available for arg mode
#			requestinjector.py -u "http://example.com/somepath/a/b/c" \
#			-M arg \
#			-T shotgun \
#			-K key1,key2,key3,key4 \
#			-w "/path/to/wordlist.txt" \
#			-S statickey1=staticval1,statickey2=staticval2 \
#			-t 10 \
#			-r 2 \
#			-p '{"http": "http://127.0.0.1:8080", "https": "https://127.0.0.1:8080"}' \
#			-H '{"Content-Type": "text/plain"}' \
#			--color
#
#	arg mode (-M arg) using trident attacktype (-T trident), and optional static arguments (-S):
#		# NOTE - trident is similar to Burp Suite's pitchfork mode; for each key specified, provided a wordlist (-w WORDLIST1,WORDLIST2,etc); specify the same wordlist multiple times if using this attacktype and you want the same wordlist in multiple positions
#		# NOTE - this type will run through to the end of the shortest provided wordlist; use --longest and --fillvalue VALUE to run through the longest provided wordlist instead
#		# NOTE - mutations (-m) not yet available for arg mode
#			requestinjector.py -u "http://example.com/somepath/a/b/c" \
#			-M arg \
#			-T trident \
#			-K key1,key2,key3,key4 \
#			-w /path/to/wordlist1.txt,/path/to/wordlist2.txt,/path/to/wordlist3.txt,/path/to/wordlist4.txt \
#			-S statickey1=staticval1,statickey2=staticval2 \
#			-t 10 \
#			-r 2 \
#			-p '{"http": "http://127.0.0.1:8080", "https": "https://127.0.0.1:8080"}' \
#			-H '{"Content-Type": "text/plain"}' \
#			--color
#
#	arg mode (-M arg) using trident attacktype (-T trident), optional static arguments (-S), and  --longest and --fillvalue VALUE (itertools.zip_longest())
#		# NOTE - trident is similar to Burp Suite's pitchfork mode; for each key specified, provided a wordlist (-w WORDLIST1,WORDLIST2,etc); specify the same wordlist multiple times if using this attacktype and you want the same wordlist in multiple positions
#		# NOTE - --longest and --fillvalue VALUE will run through to the end of the longest provided wordlist, filling empty values with the provided fillvalue
#		# NOTE - mutations (-m) not yet available for arg mode
#			requestinjector.py -u "http://example.com/somepath/a/b/c" \
#			-M arg \
#			-T trident \
#			-K key1,key2,key3,key4 \
#			-w /path/to/wordlist1.txt,/path/to/wordlist2.txt,/path/to/wordlist3.txt,/path/to/wordlist4.txt \
#			-S statickey1=staticval1,statickey2=staticval2 \
#			--longest \
#			--fillvalue "AAAA" \
#			-t 10 \
#			-r 2 \
#			-p '{"http": "http://127.0.0.1:8080", "https": "https://127.0.0.1:8080"}' \
#			-H '{"Content-Type": "text/plain"}' \
#			--color
#
#	output modes: full (default), --simple_output (just status code and full url), --color (same as simple_output but the status code is colorized)
#
#	additional options:
#		-d/--delay [FLOAT] = add a delay, per thread, as a float (default 0.0)
#
#	or import as a module (from requestinjector import RequestInjector)
#
#=======================================================

import argparse
import itertools
import json
import os
import sys
import threading
import queue
import sys
import time
from contextlib import ExitStack
from pathlib import Path
import requests
from urllib.parse import urlparse
# suppress warning
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)



#================================================
#
# Filler Classes
#
#================================================



class Filler(threading.Thread):
	"""provides the parent class to fill a queue with provided wordlists, key/value pairs, or other items as provided"""
	def __init__(self, *args, **kwargs):
		threading.Thread.__init__(self)
		self.setDaemon(True)
		self.name = threading.current_thread().name
		self.queue = kwargs.get("queue")
		self.wordlist = kwargs.get("wordlist") # a list of wordlist files
		self.attacktype = kwargs.get("attacktype")
		self.staticargs = kwargs.get("staticargs")
		self.injectkeys = kwargs.get("injectkeys")
		self.longest = kwargs.get("longest")
		self.fillvalue = kwargs.get("fillvalue")



class PathFiller(Filler):
	"""fills the queue based on path mode requirements"""
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def run(self):
		# self.wordlist is a list, and this mode only accepts the first wordlist
		with open(self.wordlist[0], "r") as f:
			for line in f:
				line = str(line).strip()
				self.queue.put(line)
#				print(f"\033[95m{self.name}\033[0m placed {line} into queuein") # purple
		f.close()



class ArgShotgunFiller(Filler):
	"""fills the queue based on arg mode + shotgun attacktype requirements"""
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def makeArg(self, word):
		l = []
		for i in self.injectkeys:
			# make into key=value format
			# TODO: encodings and obfuscations
			i = i.strip() + "=" + word.strip()
			l.append(i)
		#
		# append static args to the ones generated above
		if isinstance(self.staticargs, list):
			l = l + self.staticargs
		return(l)

	def run(self):
#		print(f"\033[95m{self.name}\033[0m opening {self.wordlist}") # purple
		# self.wordlist is a list, and this attacktype only accepts the first wordlist
		with open(self.wordlist[0], "r") as f:
			for line in f:
				line = str(line).strip()
				line = self.makeArg(line)
				#
				# build a new list not containing empty values
				l = [i for i in line if len(i) > 0]
				#
				# take the list and turn it into a format ready to be pasted onto a URL
				if len(l) > 1:
					xxx = "&".join(l) # a query string ready to be appended
				else:
					xxx = "".join(l) # smash the list into an empty string or a string containing just the first element
				self.queue.put(xxx)
#				print(f"\033[95m{self.name}\033[0m placed {line} into queuein") # purple
		f.close()



class ArgTridentFiller(Filler):
	"""fills the queue based on arg mode + trident attacktype requirements"""
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def run(self):
		with ExitStack() as stack:
			# open all files at once using the ExitStack context manager
			files = [stack.enter_context(open(fname, "r")) for fname in self.wordlist]
			# in each file, get a row at the same time, zip() them, and put the output into the queue
			for (rows) in zip(*files):
				# clean each item
				rows = [r.strip() for r in rows]
				# zip the keys and row items into a new tuple
				x = [x for x in zip(self.injectkeys,rows)]
				# turn the tuples into key=value pairs for using in a URL query
				xx = ["=".join(a) for a in x]
				#
				# append static args to the ones generated above
				if isinstance(self.staticargs, list):
					xx = xx + self.staticargs
				#
				# build a new list not containing empty values
				l = [i for i in xx if len(i) > 0]
				#
				# take the list and turn it into a format ready to be pasted onto a URL
				if len(l) > 1:
					xxx = "&".join(l) # a query string ready to be appended
				else:
					xxx = "".join(l) # smash the list into an empty string or a string containing just the first element
				# place the key1=value1&key2=value2... string into the queue
				self.queue.put(xxx)


class ArgTridentLongestFiller(Filler):
	"""fills the queue based on arg mode + trident attacktype + --longest requirements"""
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def run(self):
		with ExitStack() as stack:
			# open all files at once using the ExitStack context manager
			files = [stack.enter_context(open(fname, "r")) for fname in self.wordlist]
			# in each file, get a row at the same time, itertools.zip_longest() them, and put the output into the queue
			for (rows) in itertools.zip_longest(*files, fillvalue=self.fillvalue):
				# clean each item
				rows = [r.strip() for r in rows]
				# zip the keys and row items into a new tuple
				x = [x for x in zip(self.injectkeys,rows)]
				# turn the tuples into key=value pairs for using in a URL query
				xx = ["=".join(a) for a in x]
				#
				# append static args to the ones generated above
				if isinstance(self.staticargs, list):
					xx = xx + self.staticargs
				#
				# build a new list not containing empty values
				l = [i for i in xx if len(i) > 0]
				#
				# take the list and turn it into a format ready to be pasted onto a URL
				if len(l) > 1:
					xxx = "&".join(l) # a query string ready to be appended
				else:
					xxx = "".join(l) # smash the list into an empty string or a string containing just the first element
				# place the key1=value1&key2=value2... string into the queue
				self.queue.put(xxx)



#================================================
#
# Processing Classes
#
#================================================



class ProcessUrl:
	"""preps URL variations/mutations for different modes"""
	def __init__(self, url="", mutate=False, mode=None):
		self.output = []
		self.url = self.run(url, mode) # preps/fixes the URL according to the mode
		self.output.append(self.url)
		self.mode = mode
		if not self.mode:
			print("EXCEPTION: ProcessUrl requires a mode argument")
			sys.exit(1)
		if mutate:
			self.output = self.mutate(self.url, self.mode)
			self.output.append(self.url)
			self.output = sorted(list(set(self.output)), key=len)
	
	def mutate(self, url, mode) -> list:
		"""handles mutations and returns a list, to later be placed into the queue"""
		if mode == "path":
			return(self.mutatePath(url, mode))
		elif mode == "arg":
			return(self.mutateArg(url, mode))

	def mutatePath(self, url, mode) -> list:
		"""produces a list of each URL variation based on trimming paths down to the base URL"""
		# example: https://example.internal/a/b/c --> https://example.internal/, https://example.internal/a/, https://example.internal/a/b/, https://example.internal/a/b/c/
		l = []
		u = urlparse(url)
		if len(u.path) > 1 and "/" in u.path:
			pathsplit = [i for i in u.path.split("/") if len(i) > 0] # a leading slash makes an entry 0 bytes long at index 0
			baseurl = u.scheme+"://"+u.netloc+"/" # baseurl now ends with a slash
			l.append(self.run(baseurl, mode))
			for p in pathsplit:
				baseurl = self.run(baseurl+p, mode) # additional checking
				l.append(baseurl)
		# no "else" logic becuase __init__ already puts the checked URL into the list after this function is called
		return(l)

	def mutateArg(self, url, mode) -> list:
		"""nyi"""
		return([url])

	def run(self, url, mode) -> str:
		"""prep the URL for mutations and queue placement"""
		# ensure that a given URL is stripped to just the path, and ends in a trailing slash, ex. https://example.internal/a/b/c --> https://example.internal/a/b/c/
		if mode == "path":
			u = urlparse(url)
			p = u.path
			if not p.endswith("/"):
				p = p + "/"
			uu = u.scheme+"://"+u.netloc+p
			return(uu)
		elif mode == "arg":
			# nyi, prep URL fix actions here before sending to mutate
			return(url)

	def __repr__(self) -> str:
		return(self.url)



#================================================
#
# Worker Classes
#
#================================================



class Worker(threading.Thread):
	"""parent class that retrieves an item from the input queue, makes a web request, and places the results into an output queue"""
	def __init__(self, *args, **kwargs):
		threading.Thread.__init__(self)
		self.setDaemon(True)
		self.name = threading.current_thread().name
		self.queuein = kwargs.get("queuein")
		self.queueout = kwargs.get("queueout")
		self.urls = kwargs.get("urls")
		self.proxy = kwargs.get("proxy")
		self.headers = kwargs.get("headers")
		if not self.headers:
			self.headers = {}
		self.header_default_useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0"
		self.header_default_accept = "text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8"
		self.url_encode = kwargs.get("url_encode")
		self.retries = kwargs.get("retries")
		self.delay = kwargs.get("delay")
		if len(self.headers) == 0:
			self.headers = {'User-Agent':self.header_default_useragent, 'Accept':self.header_default_accept}
		else:
			if "User-Agent" not in self.headers:
				self.headers["User-Agent"] = self.header_default_useragent
			if "Accept" not in self.headers:
				self.headers["Accept"] = self.header_default_accept
		if not self.retries:
			self.retries = 1
		self.bad_domains = {} # tracks domains that raise requests.exceptions.ReadTimeout

	def badDomainChecker(self, domain):
		"""tracks domains that raise requests.exceptions.ReadTimeout"""
		if domain not in self.bad_domains.keys():
			#sys.stderr.write(f"\033[91mINFO {self.name}: BAD DOMAIN ADDED: {domain}\033[0m\n") # red
			self.bad_domains[domain] = 1
		elif domain in self.bad_domains.keys():
			#sys.stderr.write(f"\033[91mINFO {self.name}: BAD DOMAIN COUNT FOR: {domain} {self.bad_domains[domain]}\033[0m\n") # red
			self.bad_domains[domain] += 1

	def prepareUrl(self, url):
		"""this will be inherited downstream for modification"""
		return(url)

	def makeRequest(self, url, item):
		"""handles web request logic"""
		try:
			# set a flag that determines if the request gets made or not, depending on if a domain is responsive or not based on self.badDomainChecker() and self.bad_domains
			execute = "yes"
			domain = urlparse(url).netloc
			# check if the domain is in a thread-internal "known bad / unresponsive" dictionary
			if domain in self.bad_domains.keys():
				if self.bad_domains[domain] >= self.retries:
					execute = "no"
			if execute == "yes":
				# word (current queue item) is appended to the URL here
				url = url+item
				#print(f"\033[94m{self.name}\033[0m requesting website: {url}") # blue
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
				#print(f"status_code:{sc} bytes:{sz} word:{item} ip:{ip[0]} port:{ip[1]} url:{url}")
				return(f"status_code:{sc} bytes:{sz} word:{item} ip:{ip[0]} port:{ip[1]} url:{url}")
			else:
				return(f"EXCEPTION {self.name}: {url} REASON: requests.exceptions.ReadTimeout EXTRA: hit max internal allowed retries: ({self.retries})") # note this pseudo-exception will get displayed on stderr by Drainer
		except Exception as e:
			# if the domain generates an exception, increment its counter in the dictionary
			self.badDomainChecker(domain)
			return(f"EXCEPTION {self.name}: {url} REASON: requests.exceptions.ReadTimeout EXTRA: count: {self.bad_domains[domain]}, max allowed: {self.retries}") # note this exception will get displayed on stderr by Drainer


	def run(self):
		"""invoke the request"""
		while True:
			# get item to work on from first queue
			item = self.queuein.get()
#			print(f"\033[94m{self.name}\033[0m got item from queuein: {item}") # blue
			# process that item for each URL variation
			for url in self.urls:
				# prepareUrl() will be different for each type (path, arg, etc) and is modified in the subclass
				url = self.prepareUrl(url)
#				print(f"\033[94m{self.name}\033[0m prepped {url}") # blue
				if self.delay:
					time.sleep(self.delay)
				result = self.makeRequest(url, item)
				# put the result of each url+item request into the second queue
				self.queueout.put(result)
#				s = f"\033[94m{self.name}\033[0m put item into queueout: {result}" # blue
			# tell queuein the task is finished (for the queue.join() at the end)
			self.queuein.task_done()



class PathWorker(Worker):
	"""performs web requests according to path mode requirements"""
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def prepareUrl(self, url):
	# extra logic to double-check that the URL has a trailing slash, but ProcessUrl should handle this properly
		if not url.endswith("/"):
			url = url + "/"
		return(url)



class ArgWorker(Worker):
	"""performs web requests according to arg mode requirements"""
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def prepareUrl(self, url):
	# extra logic to double-check that the URL has no trailing slash
		if url.endswith("/"):
			url = url.rstrip("/")
		if not url.endswith("?"):
			url = url + "?"
		return(url)



#================================================
#
# Drainer Classes (Output Handlers)
#
#================================================



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
		"""handles sending full and condensed output to stdout/stderr"""
		if "EXCEPTION" not in str(item) and "REASON" not in str(item) and "INFO" not in str(item):
			if self.simple_output or self.color:
				s = str(item).split()[0].split("status_code:")[1]
				u = str(item).split("url:")[1]
				# rejoin into a single string
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
		"""dispatches output handling"""
		while True:
			item = self.queue.get()
#			print(f"\033[33m{self.name}\033[0m removed from queueout:\t{item}") # gold
			if item is None:
				break
			self.printToTerminal(item)
			self.queue.task_done()



#================================================
#
# Primary Object
#
#================================================



class RequestInjector:
	"""main handler to dispatch threaded objects"""
	def __init__(self, url, wordlist, staticargs, injectkeys, longest, fillvalue, delay=0.0, mode="path", attacktype=None, threads=5, mutate=False, headers={}, proxy={}, retries=None, url_encode=False, simple_output=False, color=False):
		self.wordlist = wordlist
		self.mode = mode
		self.attacktype = attacktype
		self.staticargs = staticargs
		self.injectkeys = injectkeys
		self.longest = longest
		self.fillvalue = fillvalue
		self.delay = delay
		self.threads = threads
		self.mutate = mutate
		# convert the url to a list of url(s)
		# TODO - self.url depends on the mode, and ProcessUrl should be called in the handlers
		self.url = ProcessUrl(url=url, mutate=self.mutate, mode=self.mode).output # list
		self.headers = headers
		self.proxy = proxy
		self.retries = retries
		self.url_encode = url_encode
		self.simple_output = simple_output
		self.color = color

	def preflightChecks(self):
		"""sanity checks for various mode requirements"""
		# check that mode is approved
		if not self.mode in ["path", "arg", "body"]:
			print("Error: mode not one of: path, arg, body")
			sys.exit(1)
		# checks for path mode
		if not self.wordlist and self.mode == "path":
			print("Error: mode set to path, but no wordlist provided (-w/--wordlist WORDLIST)")
			sys.exit(1)
		# check that if --longest is used, --fillvalue VALUE is also specified
		if self.longest and self.fillvalue == "":
			print("Error: --longest was specified, but no filler value was provided for inevitable nulls (-F/--fillvalue VALUE)")
			sys.exit(1)
		# TODO - ADD MODE HANDLERS HERE SO run() CAN DISPATCH THESE FOR READABILITY

	def run(self):
		"""dispatch threads to perform specified actions"""
		# sanity checks first
		self.preflightChecks()
		# this queue gets filled with words from the wordlist
		queuein = queue.Queue()
		# this queue gets filled with the web request results
		queueout = queue.Queue()
		# hold thread objects here to be joined
		threads = []
		# begin loading words into queuein using Fillers
		# worker threads read from queuein and send results to queueout
		# each thread gets a word and checks it against all URLs
		#
		# path mode
		if self.mode == "path":
			f = PathFiller(queue=queuein, wordlist=self.wordlist)
			f.name = "PathFiller"
			f.start()
			threads.append(f)
			for i in range(self.threads):
				w = PathWorker(queuein=queuein, queueout=queueout, delay=self.delay, urls=self.url, headers=self.headers, proxy=self.proxy, retries=self.retries)
				w.name = f"Worker-{i}"
				#print(f"starting Worker-{i}")
				w.start()
				threads.append(w)
		#
		# arg mode
		elif self.mode == "arg":
			#
			# shotgun attacktype
			if self.attacktype == "shotgun":
				f = ArgShotgunFiller(queue=queuein, wordlist=self.wordlist, injectkeys=self.injectkeys, staticargs=self.staticargs)
				f.name = "ArgShotgunFiller"
			#
			# trident attacktype
			elif self.attacktype == "trident":
				if not self.longest:
					f = ArgTridentFiller(queue=queuein, wordlist=self.wordlist, injectkeys=self.injectkeys, staticargs=self.staticargs)
				else:
					f = ArgTridentLongestFiller(queue=queuein, wordlist=self.wordlist, injectkeys=self.injectkeys, staticargs=self.staticargs, longest=self.longest, fillvalue=self.fillvalue)
				f.name = "ArgTridentFiller"
			f.start()
			threads.append(f)
			for i in range(self.threads):
				w = ArgWorker(queuein=queuein, queueout=queueout, delay=self.delay, urls=self.url, headers=self.headers, proxy=self.proxy, retries=self.retries)
				w.name = f"Worker-{i}"
				#print(f"starting Worker-{i}")
				w.start()
				threads.append(w)
		#
		# thread to handle output
		d = Drainer(queueout, simple_output=self.simple_output, color=self.color)
		d.name = "Drainer"
		d.start()
		threads.append(d)
		#
		# do not join daemon threads, but do check queue sizes
		# ensure the daemon threads have finished by checking that the queues are empty
		#print("\033[33;7mqueuein is empty\033[0m") # gold background
		queuein.join()
		#print("\033[33;7mqueueout is empty\033[0m") # gold background
		queueout.join()



#================================================
#
# Entrypoint Functions
#
#================================================



def tool_entrypoint():
	"""this function handles argparse arguments and serves as the entry_points reference in setup.py"""
	# collect command line arguments
	parser = argparse.ArgumentParser(description="RequestInjector: scan a URL using one or more given wordlists with optional URL transformations")
	# required arguments
	req = parser.add_argument_group("required arguments")
	req.add_argument("-u", "--url", dest="url", type=str, help="provide a URL to check", required=True)
	# general arguments
	gen = parser.add_argument_group("general arguments")
	gen.add_argument("-w", "--wordlist", dest="wordlist", type=str, help="provide a wordlist (file) location, or multiple comma-separated files in a string, ex. -w /home/user/words1.txt or -w /home/user/words1.txt,/home/user/words2.txt, etc")
	gen.add_argument("-M", "--mode", dest="mode", default="path", type=str, help="provide a mode (path|arg|body(NYI)) (default path)")
	gen.add_argument("-H", "--headers", dest="headers", default={}, type=json.loads, help="provide a dictionary of headers to include, with single-quotes wrapping the dictionary and double-quotes wrapping the keys and values, ex. '{\"Content-Type\": \"application/json\"}' (defaults to a Firefox User-Agent and Accept: text/html) *note default is set inside PathWorker class*")
	gen.add_argument("-p", "--proxy", dest="proxy", default={}, type=json.loads, help="provide a dictionary of proxies to use, with single-quotes wrapping the dictionary and double-quotes wrapping the keys and values, ex. '{\"http\": \"http://127.0.0.1:8080\", \"https\": \"https://127.0.0.1:8080\"}'")
	gen.add_argument("-r", "--retries", dest="retries", default=1, type=int, help="provide the number of times to retry a connection (default 1)")
	gen.add_argument("-t", "--threads", dest="threads", default=10, type=int, help="provide the number of threads for making requests (default 10)")
	gen.add_argument("-d", "--delay", dest="delay", default=0.0, type=float, help="provide a delay between requests, per thread, as a float (default 0.0); use fewer threads and longer delays if the goal is to be less noisy, although the amount of requests will remain the same")
	gen.add_argument("-m", "--mutate", dest="mutate", action="store_true", help="provide if mutations should be applied to the checked URL+word (currently only supports path mode, arg mode support nyi)")
	# arg mode-specific arguments
	ams = parser.add_argument_group("arg mode-specific arguments")
	ams.add_argument("-T", "--attacktype", dest="attacktype", default="shotgun", type=str, help="provide an attack type (shotgun|trident); shotgun is similar to Burp Suite's sniper and battering ram modes, and trident is similar to pitchfork (default shotgun)")
	ams.add_argument("--longest", dest="longest", action="store_true", help="provide if you wish to fully exhaust the longest wordlist using the trident attacktype, and not stop when the end of shortest wordlist has been reached (zip() vis itertools.zip_longest()")
	ams.add_argument("-F", "--fillvalue", dest="fillvalue", default="", type=str, help="provide a string to use in null values when using --longest with the trident attacktype (such as when using two wordlists of differing lengths; the fillvalue will be used when the shortest wordlist has finished, but terms are still being used from the longest wordlist)")
	ams.add_argument("-S", "--staticargs", dest="staticargs", default="", type=str, help="provide a string of static key=value pairs to include in each request, appended to the end of the query, as a comma-separated string, ex. key1=val1,key2=val2 etc")
	ams.add_argument("-K", "--injectkeys", dest="injectkeys", default="", type=str, help="provide a string of keys to be used; using the shotgun attacktype, each key will receive values from only the first wordlist; using the trident attacktype, each key must have a specifc wordlist specified in the matching position with the -w WORDLIST option; ex. '-T trident -K user,account,sid -w userwords.txt,accountids.txt,sids.txt'")
	# output arguments
	ota = parser.add_argument_group("output arguments")
	ota.add_argument("--color", dest="color", action="store_true", help="provide if stdout should have colorized status codes (will force simple_output format)")
	ota.add_argument("--simple_output", dest="simple_output", action="store_true", help="provide for simplified output, just status code and URL, ex. 200 http://example.com")
	# get arguments as variables
	args = vars(parser.parse_args())
	headers = args["headers"]
	mutate = args["mutate"]
	proxy = args["proxy"]
	retries = args["retries"]
	threads = args["threads"]
	delay = args["delay"]
	url = args["url"]
	wordlist = args["wordlist"].split(",")
	mode = args["mode"]
	attacktype = args["attacktype"]
	staticargs = args["staticargs"].split(",")
	injectkeys = args["injectkeys"].split(",")
#	injectvalues = args["injectvalues"].split(",")
	color = args["color"]
	simple_output = args["simple_output"]
	longest = args["longest"]
	fillvalue = args["fillvalue"]
	#
	# initialize and run the primary object (RequestInjector)
	x = RequestInjector(url=url, wordlist=wordlist, mode=mode, attacktype=attacktype, staticargs=staticargs, injectkeys=injectkeys, threads=threads, delay=delay, longest=longest, fillvalue=fillvalue, mutate=mutate, headers=headers, proxy=proxy, retries=retries, simple_output=simple_output, color=color) #, simple_output=True)
	x.run()



#================================================
#
# Execution Guard
#
#================================================



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