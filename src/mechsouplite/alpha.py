from mechsouplite import BrowserError
from typing import Any, Dict, List
from urllib.parse import urljoin
import copy


class BrowserForm(object):
    def __init__(
        self,
        form,
        request_url: str,
        base_payload: Dict[str, Any],
        submit_list: List[Any],
    ):
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
            if (
                submit_name is not None
                and s.attrs.get("name", None) != submit_name
            ):
                continue
            if (
                submit_value is not None
                and s.attrs.get("value", None) != submit_value
            ):
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


def get_browser_form(request_url, form):
    submit_list = []
    base_payload = {}
    for e in form.find_all():
        if e.name == "input":
            if e.attrs.get("type", None) == "submit":
                submit_list.append(e)
            elif e.attrs.get("name", None) is not None:
                base_payload[e.attrs["name"]] = e.attrs.get("value", None)
    return BrowserForm(form, request_url, base_payload, submit_list)
