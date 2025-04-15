from mm_crypto_utils import Proxies, random_proxy
from mm_starknet import balance_async, domain_async
from mm_std import DataResult


async def get_balance(rpc_url: str, account: str, token: str, proxy: str | None = None) -> DataResult[int]:
    return await balance_async.get_balance(rpc_url, account, token, proxy=proxy, timeout=7.0)


async def get_starknet_id(account: str, proxies: Proxies = None) -> DataResult[str | None]:
    res: DataResult[str | None] = DataResult.err("not_started")
    for _ in range(5):
        res = await domain_async.address_to_domain(account, proxy=random_proxy(proxies), timeout=5.0)
        if res.is_ok():
            return res
    return res
