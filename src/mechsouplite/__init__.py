from bs4 import BeautifulSoup  # type: ignore
from requests import Response, Session
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin
from bs4.element import Tag  # type: ignore
import copy
import requests

__version__: str = "0.1.0"


class BrowserError(RuntimeError):
    pass


class BrowserForm(object):
    def __init__(self, url: str, form: Tag):
        if not isinstance(form, Tag):
            raise NotImplementedError()
        if form.name != "form":
            raise NotImplementedError()
        self._url = url
        self._form = form

    def _find_by_type(
        self, tag_name: str, type_attr: str, attrs: Dict[str, Any]
    ) -> Any:
        attrs_dict = attrs.copy()
        attrs_dict["type"] = lambda x: x and x.lower() == type_attr
        return self._form.find_all(tag_name, attrs=attrs_dict)

    def set_input(self, name: str, value: str) -> None:
        i = self._form.find("input", {"name": name})
        if not i:
            raise BrowserError("No input field named " + name)
        i["value"] = value

    def set_input_radio(self, name: str, value: str) -> None:
        radios = self._find_by_type("input", "radio", {"name": name})
        if not radios:
            raise BrowserError("No input radio named " + name)

        for radio in radios:
            if "checked" in radio.attrs:
                del radio["checked"]

        for radio in radios:
            if radio.attrs.get("value", None) == value:
                radio["checked"] = "checked"
                break
        else:
            raise BrowserError(
                "No input radio named %s with choice %s" % (name, value)
            )

    def set_input_checkbox(self, name: str, value_list: List[str]) -> None:
        checkboxes = self._find_by_type("input", "checkbox", {"name": name})
        if not checkboxes:
            raise BrowserError("No input checkbox named " + name)

        for value in value_list:
            for checkbox in checkboxes:
                if checkbox.attrs.get("value", None) == value:
                    checkbox["checked"] = "checked"
                    break
            else:
                raise BrowserError(
                    "No input checkbox named %s with choice %s" % (name, value)
                )

    def set_textarea(self, name: str, value: str) -> None:
        t = self._form.find("textarea", {"name": name})
        if not t:
            raise BrowserError("No textarea named " + name)
        t.string = value

    def set_select(self, name: str, value_list: List[str]) -> None:
        select = self._form.find("select", {"name": name})
        if not select:
            raise BrowserError("No select named " + name)

        for option in select.find_all("option"):
            if "selected" in option.attrs:
                del option.attrs["selected"]

        if len(value_list) > 1 and "multiple" not in select.attrs:
            raise BrowserError("Cannot select multiple options!")

        for value in value_list:
            option = select.find("option", {"value": value})
            if not option:
                raise BrowserError(
                    "Option %s not found for select %s" % (value, name)
                )
            option.attrs["selected"] = "selected"

    def choose_submit(self, submit_name: Optional[str] = None) -> None:
        # All buttons NOT of type (button,reset) are valid submits
        inps = self._find_by_type(
            "input", "submit", dict()
        ) + self._form.find_all("button")
        inps = [
            i
            for i in inps
            if i.get("type", "").lower() not in ("button", "reset")
        ]

        if len(inps) == 0:
            raise BrowserError()
        elif len(inps) == 1:
            assert submit_name is None or inps[0]["name"] == submit_name
            submit = inps[0]
        else:
            found = False
            for inp in inps:
                if inp.has_attr("name") and inp["name"] == submit_name:
                    if found:
                        raise BrowserError(
                            "Multiple submit elements match: {0}".format(
                                submit
                            )
                        )
                    found = True
                else:
                    # Delete any non-matching element's name so that it will be
                    # omitted from the submitted form data.
                    del inp["name"]

            if not found and submit is not None:
                raise BrowserError(
                    "Specified submit element not found: {0}".format(submit)
                )
            self._submit_chosen = True

    def get_request_kwargs(self, **kwargs: Any) -> Dict[str, Any]:
        method = str(self._form.get("method", "get"))
        action = self._form.get("action")
        url = urljoin(self._url, action)
        if url is None:  # This happens when both `action` and `url` are None.
            raise ValueError("no URL to submit to")

        # read https://www.w3.org/TR/html52/sec-forms.html
        data = kwargs.pop("data", dict())
        files = kwargs.pop("files", dict())

        # Use a list of 2-tuples to better reflect the behavior of browser QSL.
        # Requests also retains order when encoding form data in 2-tuple lists.
        data = [(k, v) for k, v in data.items()]

        multipart = self._form.get("enctype", "") == "multipart/form-data"

        # Process form tags in the order that they appear on the page,
        # skipping those tags that do not have a name-attribute.
        selector = ",".join(
            "{}[name]".format(i)
            for i in ("input", "button", "textarea", "select")
        )
        for tag in self._form.select(selector):
            name = tag.get("name")  # name-attribute of tag

            # Skip disabled elements, since they should not be submitted.
            if tag.has_attr("disabled"):
                continue

            if tag.name == "input":
                if tag.get("type", "").lower() in ("radio", "checkbox"):
                    if "checked" not in tag.attrs:
                        continue
                    value = tag.get("value", "on")
                else:
                    # browsers use empty string for inputs with missing values
                    value = tag.get("value", "")

                # If the enctype is not multipart, the filename is put in
                # the form as a text input and the file is not sent.
                if tag.get("type", "").lower() == "file" and multipart:
                    filename = value
                    content: Union[str, Any]
                    if filename != "" and isinstance(filename, str):
                        content = open(filename, "rb")
                    else:
                        content = ""
                    # If value is the empty string, we still pass it
                    # for consistency with browsers (see
                    # https://github.com/MechanicalSoup/MechanicalSoup/issues/250).
                    files[name] = (filename, content)
                else:
                    data.append((name, value))

            elif tag.name == "button":
                if tag.get("type", "").lower() in ("button", "reset"):
                    continue
                else:
                    data.append((name, tag.get("value", "")))

            elif tag.name == "textarea":
                data.append((name, tag.text))

            elif tag.name == "select":
                # If the value attribute is not specified, the content will
                # be passed as a value instead.
                options = tag.select("option")
                selected_values = [
                    i.get("value", i.text)
                    for i in options
                    if "selected" in i.attrs
                ]
                if "multiple" in tag.attrs:
                    for value in selected_values:
                        data.append((name, value))
                elif selected_values:
                    # A standard select element only allows one option to be
                    # selected, but browsers pick last if somehow multiple.
                    data.append((name, selected_values[-1]))
                elif options:
                    # Selects the first option if none are selected
                    first_value = options[0].get("value", options[0].text)
                    data.append((name, first_value))

        if method.lower() == "get":
            kwargs["params"] = data
        else:
            kwargs["data"] = data

        # The following part of the function is here to respect the
        # enctype specified by the form, i.e. force sending multipart
        # content. Since Requests doesn't have yet a feature to choose
        # enctype, we have to use tricks to make it behave as we want
        # This code will be updated if Requests implements it.
        if multipart and not files:
            # Requests will switch to "multipart/form-data" only if
            # files pass the `if files:` test, so in this case we use
            # a modified dict that passes the if test even if empty.
            class DictThatReturnsTrue(dict):
                def __bool__(self) -> bool:
                    return True

                __nonzero__ = __bool__

            files = DictThatReturnsTrue()

        return {"method": method, "url": url, "files": files, **kwargs}


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

    def select_form(self, selector: Union[Tag] = None) -> BrowserForm:
        if isinstance(selector, Tag) and selector.name == "form":
            url = self._response.request.url
            if isinstance(url, str):
                return BrowserForm(url, selector)
        raise NotImplementedError()


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
