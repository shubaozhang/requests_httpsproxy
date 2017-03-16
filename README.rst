==============
requests-httpsproxy
==============
allow http/https requests through `HTTPS Proxy
<https://www.chromium.org/developers/design-documents/secure-web-proxy>`_.

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

  https_proxy = 'https://username:password@phus.lu'
  sess = requests.Session()
  print (sess.get('https://httpbin.org/ip', proxies={'http':https_proxy, 'https':https_proxy}).text)


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
