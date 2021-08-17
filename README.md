# RequestInjector
scan a URL using a given wordlist with optional URL transformations

### Installation [GitHub](https://github.com/bonifield/RequestInjector) [PyPi](https://pypi.org/project/requestinjector/)
```
pip install requestinjector
```

### Usage (Command Line Tool)
```
requestinjector.py -u "http://example.com/somepath/a/b/c" -w "/path/to/wordlist.txt" -m True -r 2 -p '{"http": "http://127.0.0.1:8080", "https": "https://127.0.0.1:8080"}' -H '{"Content-Type": "text/plain"}' --color True --simple_output True
	-u [URL] = provide a URL
	-w [WORDLIST] = provide a path to a wordlist (note: when importing as a module, this can also be a Python list)
	-m True = mutate the path to check all subpaths, ex. check ""http://example.com/WORD", "http://example.com/somepath/WORD", "http://example.com/somepath/a/WORD", "http://example.com/somepath/a/b/WORD", and "http://example.com/somepath/a/b/c/WORD"
	-r [NUM] = number of retries to check a domain that can't be reached, before continuing on with other URLs
	-H [HEADERDICT] = dictionary of header information, with single-quotes wrapping the dictionary and double-quotes wrapping the keys and values, ex. '{"Content-Type": "application/json"}'
	-p [PROXYDICT] = dictionary of proxy information, with single-quotes wrapping the dictionary and double-quotes wrapping the keys and values, ex. '{"Content-Type": "application/json"}'
	--color True = colorize stdout, forces simple_output format
	--simple_output True = only show the response status code, and the URL checked
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
status_code:404 bytes:12 word:x ip:127.0.0.1 port:8080 url:http://example.com/x
status_code:404 bytes:12 word:z ip:127.0.0.1 port:8080 url:http://example.com/z
status_code:404 bytes:12 word:test ip:127.0.0.1 port:8080 url:http://example.com/test
status_code:200 bytes:411 word:somepath ip:127.0.0.1 port:8080 url:http://example.com/somepath
status_code:404 bytes:12 word:doesnotexist ip:127.0.0.1 port:8080 url:http://example.com/doesnotexist
status_code:200 bytes:556 word:u ip:127.0.0.1 port:8080 url:http://example.com/somepath/u

# Simplified Format (simple_output)
404 http://example.com/somepath/v
200 http://example.com/somepath
200 http://example.com/somepath/u

```

### Future Improvements
- Add "Modes" to try various requests
	- query mode
	- fragment mode
	- body mode
	- multiple request methods

### TODO
- better injection handlers
- map get history length against head history length to check body redirects
- body POST/PUT JSON objects, using a config possible
- encodings
- query/fragment/body modes
- better output handling to support response body content, headers sent/received, etc
