# -*- coding: utf-8 -*-
"""
This module add HTTPS proxies support to requests.

The HTTPS implementation supports the full range of requests features.
"""
from __future__ import absolute_import

from socket import error as SocketError, timeout as SocketTimeout
from socket import create_connection as create_socket_connection

from requests.packages.urllib3.connection import (
    HTTPConnection, HTTPSConnection
)
from requests.packages.urllib3.connectionpool import (
    HTTPConnectionPool, HTTPSConnectionPool
)
from requests.packages.urllib3.exceptions import ConnectTimeoutError, NewConnectionError
from requests.packages.urllib3.poolmanager import PoolManager
from requests.packages.urllib3.util.url import parse_url
from requests.packages.urllib3.contrib.pyopenssl import WrappedSocket

import re
import functools
import tlslite
import OpenSSL.crypto

class HTTPSProxyConnection(HTTPConnection):
    """
    A plain-text HTTP connection that connects via a HTTPSProxy proxy.
    """
    def __init__(self, *args, **kwargs):
        self._ssl_options = kwargs.pop('_ssl_options')
        super(HTTPSProxyConnection, self).__init__(*args, **kwargs)

    def _new_conn(self):
        """
        Establish a new connection via the HTTPSProxy proxy.
        """
        extra_kw = {}
        if self.source_address:
            extra_kw['source_address'] = self.source_address

        try:
            proxy_host = self._ssl_options['proxy_host']
            proxy_port = self._ssl_options['proxy_port']
            proxy_sock = create_socket_connection(
                (proxy_host, proxy_port),
                timeout=self.timeout,
                **extra_kw
            )
            proxy_conn = tlslite.TLSConnection(proxy_sock)
            proxy_conn.handshakeClientCert(serverName=proxy_host)
            proxy_conn.sendall(('CONNECT %s:%d HTTP/1.1\r\nHost: %s:%d\r\n\r\n' % (self.host, self.port, self.host, self.port)).encode())

            data = b''
            code = 0
            pos = -1
            while True:
                s = proxy_conn.recv(4096)
                if not s:
                    if code == 0:
                        raise SocketError("Tunnel connection failed: %r" % data)
                    break
                data += s
                if code == 0 and b'\r\n' in data:
                    version, code, message = data.split(b' ', 2)
                    if code != b'200':
                        proxy_conn.close()
                        raise SocketError("Tunnel connection failed: %s %s" % (code, message.strip()))
                pos = data.find(b'\r\n\r\n')
                if pos > 0:
                    break
            proxy_conn.unread(data[pos+4:])
            conn = proxy_conn
        except SocketTimeout as e:
            raise ConnectTimeoutError(
                self, "Connection to %s timed out. (connect timeout=%s)" %
                (self.host, self.timeout))

        except SocketError as e:
            raise NewConnectionError(
                self, "Failed to establish a new connection: %s" % e)

        return conn


# We don't need to duplicate the Verified/Unverified distinction from
# urllib3/connection.py here because the HTTPSConnection will already have been
# correctly set to either the Verified or Unverified form by that module. This
# means the HTTPSProxyHTTPSConnection will automatically be the correct type.
class HTTPSProxyHTTPSConnection(HTTPSProxyConnection, HTTPSConnection):
    pass


class HTTPSProxyHTTPConnectionPool(HTTPConnectionPool):
    ConnectionCls = HTTPSProxyConnection


class HTTPSProxyHTTPSConnectionPool(HTTPSConnectionPool):
    ConnectionCls = HTTPSProxyHTTPSConnection


class HTTPSProxyProxyManager(PoolManager):
    """
    A version of the urllib3 ProxyManager that routes connections via the
    defined HTTPSProxy proxy.
    """
    pool_classes_by_scheme = {
        'http': HTTPSProxyHTTPConnectionPool,
        'https': HTTPSProxyHTTPSConnectionPool,
    }

    def __init__(self, proxy_url, username=None, password=None,
                 num_pools=10, headers=None, **connection_pool_kw):
        parsed = parse_url(proxy_url)

        self.proxy_url = proxy_url

        ssl_options = {
            # 'ssl_version': ssl_version,
            'proxy_host': parsed.host,
            'proxy_port': parsed.port or 443,
            'username': username,
            'password': password,
        }
        connection_pool_kw['_ssl_options'] = ssl_options

        super(HTTPSProxyProxyManager, self).__init__(
            num_pools, headers, **connection_pool_kw
        )

        self.pool_classes_by_scheme = HTTPSProxyProxyManager.pool_classes_by_scheme


def tlslite_getpeercert(conn):
    if not hasattr(conn, '_peercert'):
        x509_bytes = conn.session.serverCertChain.x509List[0].bytes
        x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, bytes(x509_bytes))
        subject = x509.get_subject()
        abbvs = {'CN': 'commonName',
                 'L': 'localityName',
                 'ST': 'stateOrProvinceName',
                 'O': 'organizationName',
                 'OU': 'organizationalUnitName',
                 'C': 'countryName',
                 'STREET': 'streetAddress',
                 'DC': 'domainComponent',
                 'UID': 'userid',}
        cert = {}
        cert['subject'] = [[(abbvs.get(k.decode()) or k.decode(), v.decode()) for k, v in subject.get_components()]]
        for i in range(x509.get_extension_count()):
            extension = x509.get_extension(8)
            if extension.get_short_name() == b'subjectAltName':
                cert['subjectAltName'] = []
                for c, name in re.findall(br'\x82(.)([a-z0-9\\.\\-_]+)', extension.get_data()):
                    if ord(c) == len(name):
                        cert['subjectAltName'].append(('DNS', name.decode()))
        conn._peercert = cert
    return conn._peercert
    

def inject_into_requests():
    'Monkey-patch requests with HTTPS-Proxy Support.'
    import requests
    from requests.utils import get_auth_from_url
    __real_proxy_manager_for = requests.adapters.HTTPAdapter.proxy_manager_for
    def proxy_manager_for(self, proxy, **proxy_kwargs):
        if proxy.lower().startswith('https'):
            username, password = get_auth_from_url(proxy)
            if proxy not in self.proxy_manager:
                self.proxy_manager[proxy] = HTTPSProxyProxyManager(
                    proxy,
                    username=username,
                    password=password,
                    num_pools=self._pool_connections,
                    maxsize=self._pool_maxsize,
                    block=self._pool_block,
                    **proxy_kwargs
                )
            return self.proxy_manager[proxy]
        else:
            return __real_proxy_manager_for(self, proxy, **proxy_kwargs)
    requests.adapters.HTTPAdapter.proxy_manager_for = proxy_manager_for
    __real_is_connection_dropped = requests.packages.urllib3.util.connection.is_connection_dropped
    def is_connection_dropped(conn):
        sock = conn.sock
        while isinstance(sock, tlslite.tlsconnection.TLSConnection):
            sock = sock.sock.socket
        fake_conn = type('fake_conn_type', (object, ), {})()
        fake_conn.sock = sock
        return __real_is_connection_dropped(fake_conn)
    requests.packages.urllib3.connectionpool.is_connection_dropped = is_connection_dropped
    def ssl_wrap_socket(sock, **kwargs):
        conn = tlslite.TLSConnection(sock)
        conn.handshakeClientCert()
        conn.getpeercert = functools.partial(tlslite_getpeercert, conn)
        return conn
    requests.packages.urllib3.util.ssl_.ssl_wrap_socket = ssl_wrap_socket
    requests.packages.urllib3.connection.ssl_wrap_socket = ssl_wrap_socket
