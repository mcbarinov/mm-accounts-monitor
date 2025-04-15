from mm_sol import rpc_async, token_async
from mm_std import DataResult


async def get_balance(rpc_url: str, account: str, token: str | None = None, proxy: str | None = None) -> DataResult[int]:
    if token:
        return await token_async.get_token_balance(rpc_url, account, token, proxy=proxy, timeout=5)
    return await rpc_async.get_balance(rpc_url, account, proxy=proxy, timeout=5)
