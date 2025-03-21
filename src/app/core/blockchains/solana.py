from mm_sol import balance
from mm_std import Result


async def get_balance(rpc_url: str, account: str, token: str | None = None, proxy: str | None = None) -> Result[int]:
    if token:
        return await balance.get_token_balance_async(rpc_url, account, token, proxy=proxy, timeout=5)
    return await balance.get_sol_balance_async(rpc_url, account, proxy=proxy, timeout=5)
