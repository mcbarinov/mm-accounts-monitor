import mm_starknet.balance
from mm_crypto_utils import Proxies
from mm_starknet import domain
from mm_std import Result


def get_balance(rpc_urls: list[str], account: str, token: str, proxies: Proxies = None) -> Result[int]:
    return mm_starknet.balance.get_balance_with_retries(5, rpc_urls, account, token, proxies=proxies)


def get_starknet_id(account: str, proxies: Proxies = None) -> Result[str | None]:
    return domain.address_to_domain_with_retries(5, account, proxies=proxies)
