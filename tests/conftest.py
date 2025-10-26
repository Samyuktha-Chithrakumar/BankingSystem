import pytest
from app import app, mongo

@pytest.fixture(scope="session")
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(autouse=True)
def cleanup_db():
    mongo.db.customers.delete_many({})
    yield
    mongo.db.customers.delete_many({})
