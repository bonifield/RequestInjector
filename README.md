# RequestInjector
scan a URL using one or more given wordlists with optional URL transformations

### What is RequestInjector?
This tool scans a single URL at a time, using wordlists to try various path combinations and key/value query pairs. RequestInjector is a single standalone script that can be kept in a tools folder until needed, or installed directly via pip and accessed directly from $PATH.
- in `path` mode (`-m path`), try all words against a URL path, with optional mutations
	- given the URL "http://example.com/somepath/a/b/c", a wordlist to pull terms from, and -m/--mutate specified, worker threads will try each mutation of the URL and the current term (WORD):
		- "http://example.com/WORD", "http://example.com/somepath/WORD", "http://example.com/somepath/a/WORD", "http://example.com/somepath/a/b/WORD", "http://example.com/somepath/a/b/c/WORD"
- in `arg` mode (`-m arg`), try all words against a specified set of keys
	- using the `shotgun` attacktype (`-T shotgun`), provide a single wordlist against one or more keys (similar to Burp Suite's Intruder modes Sniper and Battering Ram)
	- using the `trident` attacktype (`-T trident`), provide one wordlist per key, and terminate upon reaching either the end of the shortest wordlist (default) or the longest (`--longest --fillvalue VALUE`) (similar to Burp Suite's Intruder mode Pitchfork)
- in `body` mode (`-m body`), use a template to submit dynamic body content to a given target, utilizing either the `shotgun` or `trident` attacktype (also supports URL-based modes above)
	- `body` is not yet implemented


### Installation [GitHub](https://github.com/bonifield/RequestInjector) [PyPi](https://pypi.org/project/requestinjector/)
```
pip install requestinjector
# will become available directly from $PATH as either "requestinjector" or "ri"
```

### Usage (Command Line Tool or Standalone Script Somewhere in $PATH)
```
v0.9.4
Last Updated: 2021-09-21

path mode (-M path):
	# NOTE - although -w accepts a comma-separated list of wordlists as a string, only the first one will be used for this mode
		requestinjector -u "http://example.com/somepath/a/b/c" \
		-M path \
		-w "/path/to/wordlist.txt" \
		-t 10 \
		-r 2 \
		-m \
		-p '{"http": "http://127.0.0.1:8080", "https": "https://127.0.0.1:8080"}' \
		-H '{"Content-Type": "text/plain"}' \
		--color

arg mode (-M arg) using shotgun attacktype (-T shotgun):
	# NOTE - shotgun is similar to Burp Suite's sniper and battering ram modes; provide one or more keys, and a single wordlist
	# NOTE - although -w accepts a comma-separated list of wordlists as a string, only the first one will be used for this attacktype
	# NOTE - mutations (-m) not yet available for arg mode
		requestinjector -u "http://example.com/somepath/a/b/c" \
		-M arg \
		-T shotgun \
		-K key1,key2,key3,key4 \
		-w "/path/to/wordlist.txt" \
		-S statickey1=staticval1,statickey2=staticval2 \
		-t 10 \
		-r 2 \
		-p '{"http": "http://127.0.0.1:8080", "https": "https://127.0.0.1:8080"}' \
		-H '{"Content-Type": "text/plain"}' \
		--color

arg mode (-M arg) using trident attacktype (-T trident), and optional static arguments (-S):
	# NOTE - trident is similar to Burp Suite's pitchfork mode; for each key specified, provided a wordlist (-w WORDLIST1,WORDLIST2,etc); specify the same wordlist multiple times if using this attacktype and you want the same wordlist in multiple positions
	# NOTE - this type will run through to the end of the shortest provided wordlist; use --longest and --fillvalue VALUE to run through the longest provided wordlist instead
	# NOTE - mutations (-m) not yet available for arg mode
		requestinjector -u "http://example.com/somepath/a/b/c" \
		-M arg \
		-T trident \
		-K key1,key2,key3,key4 \
		-w /path/to/wordlist1.txt,/path/to/wordlist2.txt,/path/to/wordlist3.txt,/path/to/wordlist4.txt \
		-S statickey1=staticval1,statickey2=staticval2 \
		-t 10 \
		-r 2 \
		-p '{"http": "http://127.0.0.1:8080", "https": "https://127.0.0.1:8080"}' \
		-H '{"Content-Type": "text/plain"}' \
		--color

arg mode (-M arg) using trident attacktype (-T trident), optional static arguments (-S), and  --longest and --fillvalue VALUE (itertools.zip_longest())
	# NOTE - trident is similar to Burp Suite's pitchfork mode; for each key specified, provided a wordlist (-w WORDLIST1,WORDLIST2,etc); specify the same wordlist multiple times if using this attacktype and you want the same wordlist in multiple positions
	# NOTE - --longest and --fillvalue VALUE will run through to the end of the longest provided wordlist, filling empty values with the provided fillvalue
	# NOTE - mutations (-m) not yet available for arg mode
		requestinjector -u "http://example.com/somepath/a/b/c" \
		-M arg \
		-T trident \
		-K key1,key2,key3,key4 \
		-w /path/to/wordlist1.txt,/path/to/wordlist2.txt,/path/to/wordlist3.txt,/path/to/wordlist4.txt \
		-S statickey1=staticval1,statickey2=staticval2 \
		--longest \
		--fillvalue "AAAA" \
		-t 10 \
		-r 2 \
		-p '{"http": "http://127.0.0.1:8080", "https": "https://127.0.0.1:8080"}' \
		-H '{"Content-Type": "text/plain"}' \
		--color

output modes: full (default), --simple_output (just status code and full url), --color (same as simple_output but the status code is colorized)

additional options:
	-d/--delay [FLOAT] = add a delay, per thread, as a float (default 0.0)

or import as a module (from requestinjector import RequestInjector)
```

### Usage (Importable Module)
```
from requestinjector import RequestInjector

proxy = {'http': 'http://127.0.0.1:8080', 'https': 'https://127.0.0.1:8080'}
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0', 'Accept': 'text/html'}
url = "http://example.com/somepath/a/b/c"
wordlist = ["/path/to/wordlist.txt"]

x = RequestInjector(url=url, wordlist=wordlist, threads=10, mutate_path=True, headers=headers, proxy=proxy, retries=1, staticargs="", injectkeys="", longest=None, fillvalue=None, simple_output=True)
x.run()
```

### Options (-h)
```
usage: requestinjector.py [-h] -u URL [-w WORDLIST] [-M MODE] [-H HEADERS]
                          [-p PROXY] [-r RETRIES] [-t THREADS] [-d DELAY] [-m]
                          [-T ATTACKTYPE] [--longest] [-F FILLVALUE]
                          [-S STATICARGS] [-K INJECTKEYS] [--color]
                          [--simple_output]

RequestInjector: scan a URL using a given wordlist with optional URL
transformations

optional arguments:
  -h, --help            show this help message and exit

required arguments:
  -u URL, --url URL     provide a URL to check

general arguments:
  -w WORDLIST, --wordlist WORDLIST
                        provide a wordlist (file) location, or multiple comma-
                        separated files in a string, ex. -w
                        /home/user/words1.txt or -w
                        /home/user/words1.txt,/home/user/words2.txt, etc
  -M MODE, --mode MODE  provide a mode (path|arg|body(NYI)) (default path)
  -H HEADERS, --headers HEADERS
                        provide a dictionary of headers to include, with
                        single-quotes wrapping the dictionary and double-
                        quotes wrapping the keys and values, ex. '{"Content-
                        Type": "application/json"}' (defaults to a Firefox
                        User-Agent and Accept: text/html) *note default is set
                        inside PathWorker class*
  -p PROXY, --proxy PROXY
                        provide a dictionary of proxies to use, with single-
                        quotes wrapping the dictionary and double-quotes
                        wrapping the keys and values, ex. '{"http":
                        "http://127.0.0.1:8080", "https":
                        "https://127.0.0.1:8080"}'
  -r RETRIES, --retries RETRIES
                        provide the number of times to retry a connection
                        (default 1)
  -t THREADS, --threads THREADS
                        provide the number of threads for making requests
                        (default 10)
  -d DELAY, --delay DELAY
                        provide a delay between requests, per thread, as a
                        float (default 0.0); use fewer threads and longer
                        delays if the goal is to be less noisy, although the
                        amount of requests will remain the same
  -m, --mutate          provide if mutations should be applied to the checked
                        URL+word (currently only supports path mode, arg mode
                        support nyi)

arg mode-specific arguments:
  -T ATTACKTYPE, --attacktype ATTACKTYPE
                        provide an attack type (shotgun|trident); shotgun is
                        similar to Burp Suite's sniper and battering ram
                        modes, and trident is similar to pitchfork (default
                        shotgun)
  --longest             provide if you wish to fully exhaust the longest
                        wordlist using the trident attacktype, and not stop
                        when the end of shortest wordlist has been reached
                        (zip() vis itertools.zip_longest()
  -F FILLVALUE, --fillvalue FILLVALUE
                        provide a string to use in null values when using
                        --longest with the trident attacktype (such as when
                        using two wordlists of differing lengths; the
                        fillvalue will be used when the shortest wordlist has
                        finished, but terms are still being used from the
                        longest wordlist)
  -S STATICARGS, --staticargs STATICARGS
                        provide a string of static key=value pairs to include
                        in each request, appended to the end of the query, as
                        a comma-separated string, ex. key1=val1,key2=val2 etc
  -K INJECTKEYS, --injectkeys INJECTKEYS
                        provide a string of keys to be used; using the shotgun
                        attacktype, each key will receive values from only the
                        first wordlist; using the trident attacktype, each key
                        must have a specifc wordlist specified in the matching
                        position with the -w WORDLIST option; ex. '-T trident
                        -K user,account,sid -w
                        userwords.txt,accountids.txt,sids.txt'

output arguments:
  --color               provide if stdout should have colorized status codes
                        (will force simple_output format)
  --simple_output       provide for simplified output, just status code and
                        URL, ex. 200 http://example.com
```

### Example Output
```
# Standard Format
# Provided URL: http://example.com/somepath/exists
# Note the IP and port reflect the proxy being used; without a proxy, this will reflect the external address being scanned
status_code:404 bytes:12 word:contactus ip:127.0.0.1 port:8080 url:http://example.com/contactus
status_code:404 bytes:12 word:contactus ip:127.0.0.1 port:8080 url:http://example.com/somepath/contactus
status_code:200 bytes:411 word:contactus ip:127.0.0.1 port:8080 url:http://example.com/somepath/exists/contactus
status_code:404 bytes:12 word:admin ip:127.0.0.1 port:8080 url:http://example.com/admin
status_code:200 bytes:556 word:admin ip:127.0.0.1 port:8080 url:http://example.com/somepath/admin
status_code:200 bytes:556 word:admin ip:127.0.0.1 port:8080 url:http://example.com/somepath/exists/admin

# Simplified Format (simple_output)
404 http://example.com/contactus
404 http://example.com/somepath/contactus
200 http://example.com/somepath/exists/contactus
404 http://example.com/admin
200 http://example.com/somepath/admin
200 http://example.com/somepath/exists/admin
```

### TODO
- preview mode
- body mode, recursive grep, method select/switching
- logfile dump for every execution
- redirect history handling
- body POST/PUT objects using a config
- optional encodings and obfuscation of words/terms
- better output handling to support response body content, headers sent/received, etc
- move more logic out of Worker classes and into pre-processing/Filler and post-processing/Drainer classes
- jitter, rotating user agents, arg mode mutations (duplicate keys, re-order, null bytes, etc)
- "real timeout" (-R) to use with requests