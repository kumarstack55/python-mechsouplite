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
```

## License

MIT
