# link-example

This package was auto-generated by [openapi-client-generator](https://github.com/avanov/openapi-client-generator).

```bash

pip install link-example

```


## Client instantiation example

```python
import link_example

client = link_example.common.http.Client(service_url="https://openapi-service-url/")
response = link_example.service.<path.to.endpoint>.<method>.call(
    client,
    <params, headers, payloads>
)
```