from mm_aptos import ans, balance
from mm_crypto_utils import Proxies
from mm_std import Result


def get_balance(rpc_urls: list[str], account: str, token: str | None = None, proxies: Proxies = None) -> Result[int]:
    if token is None:
        token = "0x1::aptos_coin::AptosCoin"  # nosec  # noqa: S105
    return balance.get_balance_with_retries(5, rpc_urls, account, coin_type=token, proxies=proxies)


def get_ans_name(account: str, proxies: Proxies = None) -> Result[str | None]:
    return ans.address_to_primary_name(account, timeout=5, proxies=proxies, attempts=5)
