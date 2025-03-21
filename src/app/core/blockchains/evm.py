from mm_crypto_utils import Proxies
from mm_eth import ens, erc20, rpc
from mm_std import Result


def get_balance(node: str, account: str, token: str | None = None, proxy: str | None = None, timeout: float = 7) -> Result[int]:
    if token:
        return erc20.get_balance(node, token_address=token, user_address=account, proxies=proxy, attempts=1, timeout=int(timeout))
    return rpc.eth_get_balance(node, account, proxies=proxy, attempts=1, timeout=int(timeout))


def get_ens_name(rpc_urls: list[str], account: str, proxies: Proxies = None) -> Result[str | None]:
    return ens.get_name_with_retries(rpc_urls, account, retries=5, proxies=proxies)
