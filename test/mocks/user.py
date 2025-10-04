import factory

from test.utils.mock_functions import generate_user_email, generate_user_name


class UserFactory(factory.DictFactory):
    name = factory.Sequence(generate_user_name)
    email = factory.Sequence(generate_user_email)
    password = '12345'
