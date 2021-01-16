import pytest
import petstore_full


@pytest.mark.parametrize('service_url', [
    'https://petstore3.swagger.io/api/v3/',
])
def test_client(service_url):
    client = petstore_full.common.http.Client(service_url=service_url)
    endpoint = petstore_full.service.pet.find_by_tags.get
    action = endpoint.call(
        client,
        query=endpoint.Query(
            tags=['dog']
        ),
        headers=endpoint.Headers()
    )
    assert isinstance(action, list)
    assert isinstance(action[0], endpoint.Pet)
