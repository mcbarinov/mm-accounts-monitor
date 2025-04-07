from mm_crypto_utils import Proxies
from mm_eth import async_rpc, ens, erc20
from mm_std import Result


async def get_balance(
    node: str, account: str, token: str | None = None, proxy: str | None = None, timeout: float = 7
) -> Result[int]:
    if token:
        return await erc20.async_get_balance(
            node, token_address=token, user_address=account, proxies=proxy, attempts=1, timeout=int(timeout)
        )
    return await async_rpc.eth_get_balance(node, account, proxies=proxy, attempts=1, timeout=int(timeout))


async def get_ens_name(rpc_urls: list[str], account: str, proxies: Proxies = None) -> Result[str | None]:
    return await ens.get_name_with_retries_async(rpc_urls, account, retries=5, proxies=proxies)
