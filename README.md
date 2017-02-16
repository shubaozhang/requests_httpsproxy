# requests-httpsproxy

```
import requests

import requests_httpsproxy
requests_httpsproxy.inject_into_requests()

https_proxy = 'https://localhost:8443'

print (requests.get('https://httpbin.org/ip', proxies={'http':https_proxy, 'https':https_proxy}).text)
```
