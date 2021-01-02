import pytest
import example_client


@pytest.mark.parametrize('service_url', [
    'https://petstore3.swagger.io/api/v3/',
])
def test_client(service_url):
    client = example_client.common.http.Client(service_url=service_url)
    action = example_client.service.pet.post.request(client)

