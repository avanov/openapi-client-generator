# petstore-expanded

This package was auto-generated by [openapi-client-generator](https://github.com/avanov/openapi-client-generator).

```bash

pip install petstore-expanded

```


## Client instantiation example

```python
import petstore_expanded

client = petstore_expanded.common.http.Client(service_url="https://openapi-service-url/")
response = petstore_expanded.service.<path.to.endpoint>.<method>.call(
    client,
    <params, headers, payloads>
)
```