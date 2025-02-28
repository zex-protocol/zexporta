from unittest.mock import AsyncMock, create_autospec

import pytest
from health_check import HealthCheck
from health_check.abstract import Checkable


@pytest.mark.parametrize(
    "database_status, api_status, expected_result",
    [(True, True, True), (False, True, False), (True, False, False), (False, False, False)],
)
async def test_health_check_in_case_of_register(database_status, api_status, expected_result):
    # Arrangement Phase
    mock_checkable_database = create_autospec(Checkable, instance=True)
    mock_checkable_database.is_healthy = AsyncMock(return_value=database_status)
    mock_checkable_api = create_autospec(Checkable, instance=True)
    mock_checkable_api.is_healthy = AsyncMock(return_value=api_status)
    health_check = HealthCheck(mock_checkable_database, mock_checkable_api)
    # Action Phase
    result = await health_check.check_healthiness()
    # Assertion Phase
    assert result == expected_result


async def test_health_check_in_case_of_empty():
    # Arrangement Phase
    health_check = HealthCheck()
    # Action Phase
    result = await health_check.check_healthiness()
    # Assertion Phase
    assert result is True
