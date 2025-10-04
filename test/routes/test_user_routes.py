from http import HTTPStatus

from test.mocks.user import UserFactory


def test_create_user_by_route(client):
    user = UserFactory.build()

    response = client.post(
        '/users',
        json={
            'name': user['name'],
            'email': user['email'],
            'password': user['password'],
        },
    )
    response_json = response.json()

    assert response.status_code == HTTPStatus.CREATED
    assert response_json['id'] is not None
    assert response_json['name'] == user['name']
    assert response_json['email'] == user['email']
    assert response_json['created_at'] is not None
    assert response_json['updated_at'] is not None
