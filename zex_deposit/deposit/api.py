from typing import Annotated

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter

from zex_deposit.custom_types import ChainId, TransferStatus
from zex_deposit.db.transfer import find_transactions_by_status

app = FastAPI(name="ZexDeposit", version="1")

route = APIRouter(tags=["Transfers"], prefix="/transfers")


@route.get("/finalized/<chain_id:int>")
async def get_finalized_tx(
    chain_id: int,
    from_block: Annotated[int, Query(default=0)],
    status: Annotated[TransferStatus, Query(default=TransferStatus.FINALIZED)],
) -> JSONResponse:
    transfers = await find_transactions_by_status(
        status, chain_id=ChainId(chain_id), from_block=from_block
    )
    return JSONResponse(
        content=[transfer.model_dump(mode="json") for transfer in transfers]
    )


app.include_router(route)
