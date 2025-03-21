from mm_aptos import ans, balance
from mm_crypto_utils import Proxies
from mm_std import Result


def get_balance(rpc_url: str, account: str, token: str | None = None, proxy: str | None = None) -> Result[int]:
    if token is None:
        token = "0x1::aptos_coin::AptosCoin"  # nosec  # noqa: S105
    return balance.get_balance(rpc_url, account, coin_type=token, proxy=proxy)


def get_ans_name(account: str, proxies: Proxies = None) -> Result[str | None]:
    return ans.address_to_primary_name(account, timeout=5, proxies=proxies, attempts=5)
