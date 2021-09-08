# RequestInjector
scan a URL using a given wordlist with optional URL transformations

### Installation [GitHub](https://github.com/bonifield/RequestInjector) [PyPi](https://pypi.org/project/requestinjector/)
```
pip install requestinjector
```

### Usage (Command Line Tool or Standalone Script Somewhere in $PATH)
```
requestinjector -u "http://example.com/somepath/a/b/c" -w "/path/to/wordlist.txt" -t 10 -m True -r 2 \
	-p '{"http": "http://127.0.0.1:8080", "https": "https://127.0.0.1:8080"}' \
	-H '{"Content-Type": "text/plain"}' \
	--color True --simple_output True

Arguments:
	REQUIRED: -u/--url [URL] = provide a URL
	REQUIRED: -w/--wordlist [WORDLIST] = provide a path to a wordlist (note: when importing as a module, this can also be a Python list)
	-t/--threads [NUM] = number of threads (default 10); each thread uses every URL mutation to check the current word
	-m/--mutate_path = mutate the path to check all subpaths, ex. check "http://example.com/WORD", "http://example.com/somepath/WORD", "http://example.com/somepath/a/WORD", "http://example.com/somepath/a/b/WORD", and "http://example.com/somepath/a/b/c/WORD"
	-r/--retries [NUM] = number of retries to check a domain that can't be reached, before continuing on with other URLs (default 1)
	-H/--headers [HEADERDICT] = dictionary of header information
		- MUST use single-quotes to wrap the dictionary, and double-quotes to wrap the keys and values, ex. '{"Content-Type": "application/json"}'
		- defaults added unless otherwise specified:
			User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:86.0) Gecko/20100101 Firefox/86.0
			Accept: text/html, application/xhtml+xml, application/xml;q=0.9, */*;q=0.8
	-p/--proxy [PROXYDICT] = dictionary of proxy information
		- MUST use single-quotes to wrap the dictionary, and double-quotes to wrap the keys and values, ex. '{"http": "http://127.0.0.1:8080", "https": "https://127.0.0.1:8080"}'
	--color = colorize stdout, forces simple_output format
	--simple_output = only show the response status code and the URL checked
```

### Usage (Importable Module)
```
from requestinjector import RequestInjector

proxy = {'http': 'http://127.0.0.1:8080', 'https': 'https://127.0.0.1:8080'}
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0', 'Accept': 'text/html'}
url = "http://example.com/somepath/a/b/c"

x = RequestInjector(url=url, wordlist="/path/to/wordlist.txt", threads=10, mutate_path=True, headers=headers, proxy=proxy, retries=1, simple_output=True)
x.run()
```

### Example Output
```
# Standard Format
# Provided URL: http://example.com/somepath/exists
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
- query/fragment/body modes, recursive grep, method select/switching
- redirect history handling
- body POST/PUT objects, possibly using a config
- optional encodings
- better output handling to support response body content, headers sent/received, etc