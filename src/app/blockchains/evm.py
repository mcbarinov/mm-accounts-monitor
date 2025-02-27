from mm_crypto_utils import Proxies
from mm_eth import erc20, rpc
from mm_std import Result


def get_balance(rpc_urls: list[str], account: str, token: str | None = None, proxies: Proxies = None) -> Result[int]:
    if token:
        return erc20.get_balance(rpc_urls, token_address=token, user_address=account, proxies=proxies, attempts=5)
    return rpc.eth_get_balance(rpc_urls, account, proxies=proxies, attempts=5)
