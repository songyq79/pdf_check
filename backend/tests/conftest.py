"""
Pytest configuration and fixtures for testing
"""
import os
import tempfile
from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Setup paths
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.models.user import Base, User, get_db
from app.models import billing
from app.api.v1.auth import _hash


@pytest.fixture(scope="session")
def db_file():
    """Create a temporary database file for testing"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture(scope="session")
def engine(db_file):
    """Create a test database engine"""
    database_url = f"sqlite:///{db_file}"
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db(engine):
    """Create a new database session for each test"""
    connection = engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    """Create a test client with dependency override"""
    def override_get_db():
        return db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db: Session):
    """Create a test user"""
    user = User(
        username="testuser",
        hashed_password=_hash("password123"),
        is_active=True,
        is_approved=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user1(db: Session):
    """Create test user 1"""
    user = User(
        username="user1",
        hashed_password=_hash("password123"),
        is_active=True,
        is_approved=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user2(db: Session):
    """Create test user 2"""
    user = User(
        username="user2",
        hashed_password=_hash("password123"),
        is_active=True,
        is_approved=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_user(db: Session):
    """Create an admin user"""
    user = User(
        username="admin",
        hashed_password=_hash("admin123"),
        is_active=True,
        is_approved=True,
        is_admin=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def token(client, db, admin_user):
    """Get JWT token for admin user"""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def test_user_token(test_user):
    """Get JWT token for test user"""
    from app.api.v1.auth import _create_token
    return _create_token({"sub": test_user.username}, 60)
