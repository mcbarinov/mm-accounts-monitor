from mm_crypto_utils import Proxies, retry_node_call
from mm_eth import rpc_async
from mm_std import DataResult


async def get_balance(
    node: str, account: str, token: str | None = None, proxy: str | None = None, timeout: float = 7
) -> DataResult[int]:
    if token:
        return await rpc_async.erc20_balance(node, token_address=token, user_address=account, proxy=proxy, timeout=timeout)
    return await rpc_async.eth_get_balance(node, account, timeout=timeout, proxy=proxy)


async def get_ens_name(rpc_urls: list[str], account: str, proxies: Proxies = None) -> DataResult[str | None]:
    return await retry_node_call(5, rpc_urls, proxies, rpc_async.ens_name, address=account)
