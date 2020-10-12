from bs4 import BeautifulSoup  # type: ignore
from requests import Response, Session
from typing import Any, Dict, Optional
from urllib.parse import urljoin
import copy
import requests

__version__: str = "0.1.0"


class BrowserError(RuntimeError):
    pass


class BrowserResponse(object):
    def __init__(self, response: Response):
        self._response = response

    def _get_response(self) -> Response:
        if self._response is None:
            raise BrowserError()
        return copy.deepcopy(self._response)

    def _get_soup(self) -> BeautifulSoup:
        if self._response is None:
            raise BrowserError()
        return BeautifulSoup(self._response.content, "html.parser")

    @property
    def response(self) -> Response:
        return self._get_response()

    @property
    def soup(self) -> BeautifulSoup:
        return self._get_soup()

    def get_absolute_url(self, relative_url: str) -> str:
        if self._response is None:
            raise BrowserError()
        if self._response.request.url is None:
            raise BrowserError()
        return urljoin(self._response.request.url, relative_url)

    def _join_url(self, url: str) -> str:
        """Deprecated"""
        return self.get_absolute_url(url)


class Browser(object):
    def __init__(self, session: Optional[Session] = None):
        if session is None:
            session = requests.Session()
        self._session = session

    def get(self, url: str, **kwargs: Any) -> BrowserResponse:
        return self.request("GET", url, **kwargs)

    def post(
        self, url: str, data: Optional[Dict[str, str]] = None, **kwargs: Any
    ) -> BrowserResponse:
        return self.request("POST", url, data=data, **kwargs)

    def request(self, method: str, url: str, **kwargs: Any) -> BrowserResponse:
        r = self._session.request(method, url, **kwargs)
        r.raise_for_status()
        return BrowserResponse(r)
