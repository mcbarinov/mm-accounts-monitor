import mm_starknet.balance
from mm_crypto_utils import Proxies
from mm_starknet import domain
from mm_std import Result


async def get_balance(rpc_url: str, account: str, token: str, proxy: str | None = None) -> Result[int]:
    return await mm_starknet.balance.get_balance_async(rpc_url, account, token, proxy=proxy)


async def get_starknet_id(account: str, proxies: Proxies = None) -> Result[str | None]:
    return await domain.address_to_domain_with_retries_async(5, account, proxies=proxies)
