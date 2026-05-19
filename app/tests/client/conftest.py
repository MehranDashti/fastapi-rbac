import pytest

from app.tests.factories import user_payload

__all__ = ["user_payload"]


@pytest.fixture
def new_user_payload():
    return user_payload()
