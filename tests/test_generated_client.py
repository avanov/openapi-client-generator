import pytest
import example_client


@pytest.mark.parametrize('service_url', [
    'https://petstore3.swagger.io/api/v3/',
])
def test_client(service_url):
    client = example_client.common.http.Client(service_url=service_url)
    endpoint1 = example_client.service.pet.post
    action1 = endpoint1.call(
        client,
        request=endpoint1.Request(
            name='pet',
            photo_urls=[],
        )
    )

    endpoint2 = example_client.service.pet.find_by_tags.get
    action2 = endpoint2.call(
        client,
        query=endpoint2.Query(
            tags=['term']
        )
    )
