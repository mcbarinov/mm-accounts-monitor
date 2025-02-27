from mm_crypto_utils import Proxies
from mm_sol import balance
from mm_std import Result


def get_balance(rpc_urls: list[str], account: str, token: str | None = None, proxies: Proxies = None) -> Result[int]:
    if token:
        return balance.get_token_balance_with_retries(rpc_urls, account, token, proxies=proxies, retries=5)
    return balance.get_sol_balance_with_retries(rpc_urls, account, proxies=proxies, retries=5)
