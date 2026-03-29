from uuid import UUID, uuid4

import pytest

from app.application.use_cases.chat_use_cases import SearchChatUsersUseCase
from app.infrastructure.keycloak.admin_client import KeycloakUserSummary, _filter_users


def test_filter_users_matches_names_case_insensitively() -> None:
    users = _filter_users(
        [
            {
                "id": str(uuid4()),
                "email": "alice@example.com",
                "firstName": "Alice",
                "lastName": "Johnson",
                "enabled": True,
            },
            {
                "id": str(uuid4()),
                "email": "bob@example.com",
                "firstName": "Bob",
                "lastName": "Miller",
                "enabled": True,
            },
        ],
        "ALIce",
        20,
    )

    assert len(users) == 1
    assert users[0].first_name == "Alice"


@pytest.mark.asyncio
async def test_search_chat_users_excludes_current_user() -> None:
    current_user = uuid4()
    other_user = uuid4()

    async def fake_search(_query: str, *, max_results: int = 20) -> list[KeycloakUserSummary]:
        assert max_results == 20
        return [
            KeycloakUserSummary(
                id=str(current_user),
                email="me@example.com",
                first_name="Me",
                last_name="User",
            ),
            KeycloakUserSummary(
                id=str(other_user),
                email="friend@example.com",
                first_name="Friend",
                last_name="User",
            ),
        ]

    results = await SearchChatUsersUseCase(fake_search).execute(
        query="user",
        current_user_id=UUID(str(current_user)),
    )

    assert len(results) == 1
    assert results[0].id == other_user
    assert results[0].display_name == "Friend User"
