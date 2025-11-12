# Project Testing Guidelines: Python Jogja Member API
---
## 1. Testing Framework
* **Primary Framework**: [unittest](https://docs.python.org/3/library/unittest.html) (Python standard library)
* **Database Testing**: In-memory SQLite with fresh instances per test
* **Note**: We use `unittest` instead of `pytest` for simplicity and to avoid dependency injection complexities
---
## 2. Test Types & Scope

### Unit Tests (Primary Focus)

* **Focus**: Individual CRUD functions, models, and business logic in isolation.
* **Database**: Each test creates a fresh in-memory SQLite database for complete isolation.
* **Location**: `tests/test_members.py`
* **Approach**: Test business logic directly by calling CRUD functions with test database sessions.

### Integration Tests (Optional/Advanced)

* **Focus**: HTTP endpoints with FastAPI TestClient (more complex, requires careful dependency management).
* **Note**: For this project, we focus on unit testing the business logic as it's more reliable and easier to maintain.

---
## 3. Test Structure

* **Given-When-Then**: Structure tests clearly:
    * **Given**: Set up test data and database state.
    * **When**: Perform the action being tested (call CRUD function).
    * **Then**: Assert the expected outcome.
* **Fresh Database Per Test**: Each test gets its own in-memory SQLite database via `setUp()` method.
* **Descriptive Naming**: Test function names should clearly indicate what they are testing (e.g., `test_create_member_successfully`, `test_get_member_by_email`).

---
## 4. Test Database Setup

### Recommended Pattern (unittest):

```python
import unittest
from sqlmodel import create_engine, Session, SQLModel
from app import models, crud

class TestMemberAPI(unittest.TestCase):
    def setUp(self):
        """Set up each individual test with a fresh in-memory database."""
        self.engine = create_engine("sqlite:///:memory:")
        SQLModel.metadata.create_all(self.engine)
        self.session = Session(self.engine)

    def tearDown(self):
        """Clean up after each test."""
        self.session.close()

    def test_create_member_successfully(self):
        # Given
        member_data = models.MemberCreate(name="John", email="john@example.com")
        
        # When
        created_member = crud.create_member(self.session, member_data)
        
        # Then
        self.assertEqual(created_member.name, member_data.name)
        self.assertIsNotNone(created_member.id)
```

---
## 5. Test Data

* **Isolated Data**: Each test operates on its own, isolated data set via fresh database instances.
* **Test Models**: Use the actual Pydantic models (`MemberCreate`, etc.) to ensure type safety.
* **Realistic Data**: Use realistic but simple test data (e.g., "john@example.com", "1234567890").

---
## 6. Test Coverage

* **Target**: Focus on business logic coverage rather than HTTP endpoint coverage.
* **Priority**: Test all CRUD operations, validation logic, and edge cases.
* **Tool**: Use `coverage` for coverage reporting if needed: `coverage run -m unittest && coverage report`

---
## 7. Running Tests

* `python -m unittest discover tests` (from project root)
* `python -m unittest tests.test_members` (specific test module)
* Tests should complete in under 1 second due to in-memory database usage

---
## 8. Why This Approach Works

* **Simplicity**: Direct testing of business logic without HTTP layer complexity
* **Reliability**: No dependency injection issues or threading problems
* **Speed**: In-memory databases are extremely fast
* **Isolation**: Each test gets a completely fresh database state
* **Debugging**: Easier to debug business logic without HTTP/ASGI layer

---
## 9. When to Add HTTP Tests

Consider adding FastAPI TestClient tests only when:
* You need to test request/response serialization
* You need to test HTTP status codes and headers
* You need to test middleware or authentication
* The business logic tests are insufficient for your confidence level

For basic CRUD operations, testing the business logic directly is more reliable and maintainable.



