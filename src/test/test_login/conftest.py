from fastapi.testclient import TestClient
import pytest
from jose import JWTError, jwt

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.main import app
from app.auth.config import settings
from app.auth.database import get_db
from app.auth.database import Base
from app.auth.oauth2 import create_access_token, create_refresh_token

"""
Define pytest fixture in this file.
All pytest modules can reach below functions without having to import them.

You can create different confest.py files in different places in your project.
like:
src/tests/blog/conftest.py
src/tests/api/conftest.py

Scope also important. You can define scope for each fixture. Default scope is function.
Function scope means that fixture will be called for each test function. So if you have 10 test function, fixture will be called 10 times.
For different module, it is better to define different confest.py file. Because if you define all fixtures in one file, it will be hard to 
understand which fixture is used for which module.
"""
# at the end of the URL we define our test database
SQL_DATABASE_URL = f"postgresql://{settings.DATABASE_USERNAME}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOSTNAME}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}_test"
# postgresql://hello_fastapi:hello_fastapi@db:5432/hello_fastapi_dev_test
engine = create_engine(SQL_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def session():
    # before running test session, we drop all  tables and create new tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(session):
    # define client for testing. we return client with yield because before testing we prepare new env for testing
    # and after testing we clean env
    def overrite_get_db():
        db = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = overrite_get_db
    yield TestClient(app)


@pytest.fixture()
def test_user(client):
    user_data = {"email": "user1_test@user.com", "password": "user1"}
    response = client.post("/auth/register/", json=user_data)
    assert response.status_code == 201
    new_data = response.json()
    new_data["password"] = user_data["password"]
    return new_data


@pytest.fixture()
def test_user2(client):
    user_data = {"email": "user2_test@user.com", "password": "user2"}
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201
    new_data = response.json()
    new_data["password"] = user_data["password"]
    return new_data


# we create this token for testing purposes
@pytest.fixture()
def tokens(test_user):
    user_id = test_user["id"]
    access_token = create_access_token({"user_id": user_id})
    refresh_token = create_refresh_token(data={"user_id": f"{user_id}_30"})
    # payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    # print("payload",payload)
    return access_token, refresh_token


@pytest.fixture()
def authorized_client(client, tokens):
    access_token, _ = tokens
    client.headers["Authorization"] = f"Bearer {access_token}"
    return client


@pytest.fixture()
def refresh_token(tokens):
    _, refresh_token = tokens
    return refresh_token
