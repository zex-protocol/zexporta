from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi import status as status_code
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter

from zexporta.custom_types import ChainSymbol, DepositStatus
from zexporta.db.deposit import find_deposit_by_status

from .config import CHAINS_CONFIG

app = FastAPI(name="ZexDeposit", version="1")

route = APIRouter(tags=["Deposits"], prefix="/deposits")


@route.get("/finalized/<chain_symbol:str>")
async def get_finalized_tx(
    chain_symbol: ChainSymbol,
    from_block: Annotated[int, Query(default=0)],
    status: Annotated[DepositStatus, Query(default=DepositStatus.FINALIZED)],
) -> JSONResponse:
    try:
        deposits = await find_deposit_by_status(
            chain=CHAINS_CONFIG[chain_symbol], status=status, from_block=from_block
        )
    except KeyError:
        raise HTTPException(
            status_code=status_code.HTTP_404_NOT_FOUND,
            detail=f"Chain with symbol {chain_symbol.value} not found",
        )
    return JSONResponse(
        content=[deposit.model_dump(mode="json") for deposit in deposits]
    )


app.include_router(route)
