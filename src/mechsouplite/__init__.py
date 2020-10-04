from bs4 import BeautifulSoup  # type: ignore
from requests import Response, Session
from typing import Any, Dict, List
from urllib.parse import urljoin
import copy
import requests
__version__ = '0.1.0'


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

    def join_url(self, url: str) -> str:
        if self._response is None:
            raise BrowserError()
        request_url = self._response.request.url
        if request_url is None:
            raise BrowserError()
        return urljoin(request_url, url)


class Browser(object):
    def __init__(self, session: Session = None):
        if session is None:
            session = requests.Session()
        self._session = session

    def get(self, url: str, **kwargs) -> BrowserResponse:
        r = self._session.get(url, **kwargs)
        r.raise_for_status()
        return BrowserResponse(r)

    def post(self, url: str, data: Dict[str, str] = None, **kwargs) -> BrowserResponse:
        r = self._session.post(url, data, **kwargs)
        r.raise_for_status()
        return BrowserResponse(r)

    def request(self, method: str, url: str, **kwargs) -> BrowserResponse:
        r = self._session.request(method, url, **kwargs)
        r.raise_for_status()
        return BrowserResponse(r)


class _BrowserForm(object):
    def __init__(
            self, form, request_url: str, base_payload: Dict[str, Any],
            submit_list: List[Any]):
        self._form = form
        self._request_url = request_url
        self._base_payload = base_payload
        self._submit_list = submit_list

    def get_submits(self):
        return self._submit_list

    def click(self, submit_name: str = None, submit_value: str = None):
        payload = copy.deepcopy(self._base_payload)
        submit_list = []
        for s in self._submit_list:
            if submit_name is not None and \
               s.attrs.get("name", None) != submit_name:
                continue
            if submit_value is not None and \
               s.attrs.get("value", None) != submit_value:
                continue
            submit_list.append(s)
        if len(submit_list) != 1:
            raise BrowserError()
        submit = submit_list[0]

        method = self._form.attrs.get("method", "get")
        url = urljoin(self._request_url, self._form.attrs["action"])
        if submit.attrs.get("name", None) is not None:
            payload[submit.attrs["name"]] = submit.attrs["value"]

        return {"method": method, "url": url, "data": payload}


def _get_browser_form(request_url, form):
    submit_list = []
    base_payload = {}
    for e in form.find_all():
        if e.name == "input":
            if e.attrs.get("type", None) == "submit":
                submit_list.append(e)
            elif e.attrs.get("name", None) is not None:
                base_payload[e.attrs["name"]] = e.attrs.get("value", None)
    return BrowserForm(form, request_url, base_payload, submit_list)
