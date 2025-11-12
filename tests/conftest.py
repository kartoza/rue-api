import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, create_engine, Session, select

from app.mock.main import app as fastapi_app          # ✅ the FastAPI() instance
from app.api.deps import get_db                  # adjust path if different
import app.models  # noqa: F401                  # ensure models are registered

from app.crud import create_user
from app.models import User, UserCreate
from app.core.config import settings
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

@pytest.fixture(scope="session", autouse=True)
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)

@pytest.fixture()
def db() -> Session:
    with Session(engine) as session:
        yield session
        session.rollback()

@pytest.fixture()
def client(db: Session) -> TestClient:
    def override_get_db():
        yield db
    # ✅ override on the FastAPI instance
    fastapi_app.dependency_overrides[get_db] = override_get_db
    # ✅ use the FastAPI instance here
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def seed_superuser(db: Session):
    su = db.exec(select(User).where(User.email == settings.FIRST_SUPERUSER)).first()
    if not su:
        create_user(
            session=db,
            user_create=UserCreate(
                email=settings.FIRST_SUPERUSER,
                password=settings.FIRST_SUPERUSER_PASSWORD,
                is_superuser=True,
                is_active=True,
                full_name="Admin",
            ),
        )

@pytest.fixture()
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture()
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )
