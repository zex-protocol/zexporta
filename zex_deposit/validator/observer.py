from utils.web3 import async_web3_factory, filter_blocks
from db.address import insert_new_adderss_to_db
from custom_types import ChainConfig


async def main(chain: ChainConfig):
    w3 = async_web3_factory(chain)
    await insert_new_adderss_to_db()
