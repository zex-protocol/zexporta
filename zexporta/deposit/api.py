from typing import Annotated

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter
from health_check import HealthCheck, HealthController

from zexporta.config import CHAINS_CONFIG
from zexporta.custom_types import ChainSymbol, DepositStatus
from zexporta.db.deposit import find_deposit_by_status

app = FastAPI(name="ZexDeposit", version="1")

route = APIRouter(tags=["Deposits"], prefix="/deposits")

# In future we should organize this instance creation
health_check_router = APIRouter(tags=["HealthCheck"])

health_check_svc = HealthCheck()

health_check_ctrl = HealthController(health_check_svc, health_check_router)

health_check_router = health_check_ctrl.register_handlers()


@route.get("/finalized/<chain_symbol:str>")
async def get_finalized_tx(
    chain_symbol: ChainSymbol,
    from_block: Annotated[int, Query(default=0)],
    status: Annotated[DepositStatus, Query(default=DepositStatus.FINALIZED)],
) -> JSONResponse:
    chain = CHAINS_CONFIG[chain_symbol.value]
    deposits = await find_deposit_by_status(chain, status, from_block=from_block)
    return JSONResponse(content=[deposit.model_dump(mode="json") for deposit in deposits])


app.include_router(route)
app.include_router(health_check_router)
