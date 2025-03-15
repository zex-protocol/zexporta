from unittest.mock import AsyncMock, patch

import pytest

from zexporta.db.token import get_decimals
from zexporta.explorer import explorer, get_accepted_deposits, get_block_batches, get_token_decimals

from .mock import MockTransfer

get_block_batches_parameters = {
    "if_from_block_is_equal_to_block_should_return_list_with_one_item": {
        "input_value": {"from_block": 3000, "to_block": 3000},
        "expected_result": [(3000,)],
    },
    "if_from_block_is_lower_than_block_should_return_batches": {
        "input_value": {"from_block": 2990, "to_block": 3000, "batch_size": 5},
        "expected_result": [
            (2990, 2991, 2992, 2993, 2994),
            (2995, 2996, 2997, 2998, 2999),
            (3000,),
        ],
    },
    "if_from_block_is_bigger_than_block_should_return_empty_list": {
        "input_value": {"from_block": 3001, "to_block": 3000, "batch_size": 5},
        "expected_result": [],
    },
}


@pytest.mark.parametrize(
    argnames=["input_value", "expected_result"],
    argvalues=[(value["input_value"], value["expected_result"]) for value in get_block_batches_parameters.values()],
    ids=[str(test) for test in get_block_batches_parameters.keys()],
)
def test_get_block_batches(input_value: dict[str, int], expected_result: tuple[int, ...]):
    # Action
    result = get_block_batches(**input_value)

    # Assertion
    assert result == expected_result


async def test_get_token_decimals_should_save_decimal_to_db(mock_client):
    # Arrangement
    expected_result = 10
    token_address = "0x0"
    mock_client.get_token_decimals.return_value = expected_result

    # Action
    result = await get_token_decimals(client=mock_client, token_address=token_address)

    # Assertion
    assert (await get_decimals(mock_client.chain.chain_symbol, token_address)) == expected_result
    assert result == expected_result


async def test_get_accepted_deposits_successful(mock_client):
    # Arrangement
    transfer1 = MockTransfer(tx_hash="0x123", value=100, chain_symbol="ETH", token="0xABC", to="0xDEF", block_number=1)
    transfer2 = MockTransfer(tx_hash="0x456", value=200, chain_symbol="ETH", token="0xXYZ", to="0xGHI", block_number=2)
    accepted_addresses = {"0xDEF": 1, "0xGHI": 2}

    mock_client.is_transaction_successful.return_value = True
    mock_client.get_token_decimals.return_value = 18

    # Action
    deposits = await get_accepted_deposits(mock_client, [transfer1, transfer2], accepted_addresses)

    # Assertion
    assert len(deposits) == 2
    assert deposits[0].user_id == 1
    assert deposits[0].decimals == 18
    assert deposits[0].transfer == transfer1
    assert deposits[1].user_id == 2
    assert deposits[1].decimals == 18
    assert deposits[1].transfer == transfer2


async def test_get_accepted_deposits_transaction_failed(mock_client):
    transfer1 = MockTransfer(tx_hash="0x123", value=100, chain_symbol="ETH", token="0xABC", to="0xDEF", block_number=1)
    accepted_addresses = {"0xDEF": 1}

    mock_client.is_transaction_successful.return_value = False
    mock_client.get_token_decimals.return_value = 18

    deposits = await get_accepted_deposits(mock_client, [transfer1], accepted_addresses)

    assert len(deposits) == 0


async def test_get_accepted_deposits_address_not_accepted(mock_client):
    transfer1 = MockTransfer(tx_hash="0x123", value=100, chain_symbol="ETH", token="0xABC", to="0xDEF", block_number=1)
    accepted_addresses = {"0xXYZ": 1}

    deposits = await get_accepted_deposits(mock_client, [transfer1], accepted_addresses)

    assert len(deposits) == 0


async def test_get_accepted_deposits_with_sa_timestamp(mock_client):
    transfer1 = MockTransfer(tx_hash="0x123", value=100, chain_symbol="ETH", token="0xABC", to="0xDEF", block_number=1)
    accepted_addresses = {"0xDEF": 1}
    sa_timestamp = 1678886400

    mock_client.is_transaction_successful.return_value = True
    mock_client.get_token_decimals.return_value = 18

    deposits = await get_accepted_deposits(mock_client, [transfer1], accepted_addresses, sa_timestamp=sa_timestamp)

    assert len(deposits) == 1
    assert deposits[0].sa_timestamp == sa_timestamp
    mock_client.is_transaction_successful.assert_called_once()
    mock_client.get_token_decimals.assert_called_once()


@pytest.fixture
def mock_extract_block_logic():
    return AsyncMock(return_value=[])


async def test_explorer_basic(mock_client, mock_extract_block_logic):
    from_block = 1
    to_block = 3
    accepted_addresses = {"0xDEF": 1}
    mock_extract_block_logic.return_value = [
        MockTransfer(tx_hash="0x123", value=100, chain_symbol="ETH", token="0xABC", to="0xDEF", block_number=1)
    ]
    mock_client.is_transaction_successful.return_value = True
    mock_client.get_token_decimals.return_value = 18

    deposits = await explorer(
        mock_client,
        from_block,
        to_block,
        accepted_addresses,
        mock_extract_block_logic,
    )

    assert len(deposits) == 3
    mock_extract_block_logic.assert_called()


async def test_explorer_no_deposits(mock_client, mock_logger, mock_extract_block_logic):
    from_block = 1
    to_block = 10
    accepted_addresses = {}

    deposits = await explorer(
        mock_client,
        from_block,
        to_block,
        accepted_addresses,
        mock_extract_block_logic,
        logger=mock_logger,
    )

    assert len(deposits) == 0
    mock_extract_block_logic.assert_called()


async def test_explorer_with_transfers(mock_client, mock_logger):
    from_block = 1
    to_block = 5
    accepted_addresses = {"0xDEF": 1}
    transfer1 = MockTransfer(tx_hash="0x123", value=100, chain_symbol="ETH", token="0xABC", to="0xDEF", block_number=1)

    async def mock_extract_block_logic(block_number, **kwargs):
        if 1 == block_number:
            return [transfer1]
        return []

    mock_client.is_transaction_successful.return_value = True
    mock_client.get_token_decimals.return_value = 18

    with patch("clients.get_async_client", return_value=mock_client):
        deposits = await explorer(
            mock_client,
            from_block,
            to_block,
            accepted_addresses,
            mock_extract_block_logic,  # type: ignore
            logger=mock_logger,
        )

        assert len(deposits) == 1
        assert deposits[0].user_id == 1
        assert deposits[0].decimals == 18
        assert deposits[0].transfer == transfer1
