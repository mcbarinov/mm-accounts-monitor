from mm_sol import balance
from mm_std import Result


def get_balance(rpc_url: str, account: str, token: str | None = None, proxy: str | None = None) -> Result[int]:
    if token:
        return balance.get_token_balance(rpc_url, account, token, proxy=proxy)
    return balance.get_sol_balance(rpc_url, account, proxy=proxy)
