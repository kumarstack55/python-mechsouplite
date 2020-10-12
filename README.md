[![codecov](https://codecov.io/gh/kumarstack55/python-mechsouplite/branch/main/graph/badge.svg?token=QwzgFauQKa)](https://app.codecov.io/gh/kumarstack55/python-mechsouplite)

# python-mechsouplite

## Installation

```bash
pip install mechsouplite
```

## Demo

```python
from mechsouplite import Browser


browser = Browser()

resp = browser.get("https://www.example.com/")
resp.response.status_code
  # --> 200
resp.soup.find("title").text
  # --> 'Example Domain'

resp2 = browser.get("https://httpbin.org/forms/post")
form = BrowserForm(resp2.response.request.url, resp2.soup.form)
form.set_input("custname", "john smith")
form.set_input_radio("size", "large")
form.set_input_checkbox("topping", ["bacon", "cheese"])
form.set_textarea("comments", "The best one, please")
kwargs = form.get_request_kwargs()

resp3 = browser.request(**kwargs)
```

## License

MIT
