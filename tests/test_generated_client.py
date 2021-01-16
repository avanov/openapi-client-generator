import pytest
import petstore_full


@pytest.mark.parametrize('service_url', [
    'https://petstore3.swagger.io/api/v3/',
])
def test_client(service_url):
    client = petstore_full.common.http.Client(service_url=service_url)
    endpoint1 = petstore_full.service.pet.post
    action1 = endpoint1.call(
        client,
        request=endpoint1.Request(
            name='pet',
            photo_urls=[],
        )
    )

    endpoint2 = petstore_full.service.pet.find_by_tags.get
    action2 = endpoint2.call(
        client,
        query=endpoint2.Query(
            tags=['term']
        )
    )
