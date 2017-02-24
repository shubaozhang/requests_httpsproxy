==============
requests-httpsproxy
==============
allow http/https requests through https proxy

Requirements
------------
* requests >= 2.13.0
* PyOpenSSL >= 0.11
* tlslite-ng

Usage
-----

.. code:: python

  import requests

  import requests_httpsproxy
  requests_httpsproxy.inject_into_requests()

  https_proxy = 'https://localhost:8443'
  print (requests.get('https://httpbin.org/ip', proxies={'http':https_proxy, 'https':https_proxy}).text)


License
-------
MIT

Related issues
-------
- https://github.com/kennethreitz/requests/issues/1182
- https://github.com/kennethreitz/requests/issues/1622
- https://github.com/kennethreitz/requests/issues/1903
- https://github.com/kennethreitz/requests/issues/3468
- https://github.com/kennethreitz/requests/issues/3806
- https://github.com/kennethreitz/requests/issues/3882
