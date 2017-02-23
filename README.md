# requests-httpsproxy

```
import requests

import requests_httpsproxy
requests_httpsproxy.inject_into_requests()

https_proxy = 'https://localhost:8443'

print (requests.get('https://httpbin.org/ip', proxies={'http':https_proxy, 'https':https_proxy}).text)
```

## related issues
* https://github.com/kennethreitz/requests/issues/1182
* https://github.com/kennethreitz/requests/issues/1622
* https://github.com/kennethreitz/requests/issues/1903
* https://github.com/kennethreitz/requests/issues/3468
* https://github.com/kennethreitz/requests/issues/3806
* https://github.com/kennethreitz/requests/issues/3882
