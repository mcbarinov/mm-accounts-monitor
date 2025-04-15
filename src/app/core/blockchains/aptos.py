from mm_aptos import ans_async, balance_async
from mm_crypto_utils import Proxies, random_proxy
from mm_std import DataResult


async def get_balance(rpc_url: str, account: str, token: str | None = None, proxy: str | None = None) -> DataResult[int]:
    if token is None:
        token = "0x1::aptos_coin::AptosCoin"  # nosec  # noqa: S105
    return await balance_async.get_balance(rpc_url, account, coin_type=token, proxy=proxy, timeout=7.0)


async def get_ans_name(account: str, proxies: Proxies = None) -> DataResult[str | None]:
    res: DataResult[str | None] = DataResult.err("not_started")
    for _ in range(5):
        res = await ans_async.address_to_primary_name(account, proxy=random_proxy(proxies), timeout=5.0)
        if res.is_ok():
            return res
    return res
