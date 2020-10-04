from mechsouplite import Browser, BrowserResponse  # type: ignore
from requests import HTTPError
import bs4  # type: ignore
import mechsouplite
import requests


def test_version() -> None:
    assert mechsouplite.__version__ == "0.1.0"


def test_browser() -> None:
    browser = mechsouplite.Browser()
    assert isinstance(browser, Browser)


def test_browser_init_session() -> None:
    session = requests.Session()
    browser = mechsouplite.Browser(session=session)
    assert isinstance(browser, Browser)
    assert session == browser._session


def test_browser_get() -> None:
    browser = mechsouplite.Browser()
    resp = browser.get("http://httpbin.org/html")
    assert isinstance(resp, BrowserResponse)


def test_browser_get_not_2xx() -> None:
    browser = mechsouplite.Browser()
    try:
        browser.get("http://httpbin.org/status/404")
        assert False
    except HTTPError:
        pass


def test_browser_response_response() -> None:
    browser = mechsouplite.Browser()
    resp = browser.get("http://httpbin.org/html")
    assert isinstance(resp.response, requests.Response)


def test_browser_response_soup() -> None:
    browser = mechsouplite.Browser()
    resp = browser.get("http://httpbin.org/html")
    assert isinstance(resp.soup, bs4.BeautifulSoup)


def test_browser_response_get_absolute_url() -> None:
    browser = mechsouplite.Browser()
    resp = browser.get("http://httpbin.org/html")
    relative_url = "path/a.html"
    assert (
        resp.get_absolute_url(relative_url) == "http://httpbin.org/path/a.html"
    )
