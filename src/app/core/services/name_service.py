import logging
from datetime import datetime

from bson import ObjectId
from mm_std import AsyncTaskRunner, Err, Result, async_synchronized_parameter, utc_delta, utc_now

from app.core.blockchains import aptos, evm, starknet
from app.core.constants import Naming
from app.core.db import NamingProblem
from app.core.services.network_service import NetworkService
from app.core.types_ import AppService, AppServiceParams

logger = logging.getLogger(__name__)


class NameService(AppService):
    def __init__(self, base_params: AppServiceParams, network_service: NetworkService) -> None:
        super().__init__(base_params)
        self.network_service = network_service

    @async_synchronized_parameter(arg_index=1)
    async def check_next_naming(self, naming: Naming) -> None:
        # self.logger.debug("check_next_naming called: %s", naming)

        # first check accounts that were never checked
        need_to_check = await self.db.account_name.find(
            {"naming": naming, "checked_at": None}, limit=self.dconfig.limit_naming_workers
        )
        if len(need_to_check) < self.dconfig.limit_naming_workers:
            need_to_check += await self.db.account_name.find(
                {"naming": naming, "checked_at": {"$lt": utc_delta(minutes=-1 * self.dconfig.check_name_interval)}},
                limit=self.dconfig.limit_naming_workers - len(need_to_check),
            )
        if not need_to_check:
            return

        runner = AsyncTaskRunner(self.dconfig.limit_naming_workers, name="check_names")
        for an in need_to_check:
            runner.add_task(str(an.id), self.check_account_name(an.id))
        await runner.run()

    async def check_account_name(self, id: ObjectId) -> Result[str | None]:
        account_name = await self.db.account_name.get(id)
        network = await self.network_service.get_network(account_name.network)

        # self.logger.debug("check_account_name called: %s / %s", account_naming.naming, account_naming.account)

        match account_name.naming:
            case Naming.ENS:
                res = await evm.get_ens_name(network.rpc_urls, account_name.account, proxies=self.dvalue.proxies)
            case Naming.ANS:
                res = await aptos.get_ans_name(account_name.account, proxies=self.dvalue.proxies)
            case Naming.STARKNET_ID:
                res = await starknet.get_starknet_id(account_name.account, proxies=self.dvalue.proxies)
            case _:
                return Err("Not implemented")

        if isinstance(res, Err):
            logger.debug("check_account_name: %s", res.err)
            await self.db.naming_problem.insert_one(
                NamingProblem(
                    id=ObjectId(),
                    network=network.id,
                    naming=account_name.naming,
                    account=account_name.account,
                    message=res.err,
                )
            )
            return res

        name = res.ok or ""
        await self.db.group_name.update_one(
            {"group_id": account_name.group_id, "naming": account_name.naming},
            {"$set": {f"names.{account_name.account}": name, f"checked_at.{account_name.account}": utc_now()}},
        )
        await self.db.account_name.set(id, {"name": name, "checked_at": utc_now()})

        return res

    async def calc_oldest_checked_time(self) -> dict[Naming, datetime | None]:
        res: dict[Naming, datetime | None] = {}
        for naming in list(Naming):
            res[naming] = None
            if not await self.db.account_name.exists({"naming": naming, "checked_at": None}):
                name = await self.db.account_name.find_one({"naming": naming}, "checked_at")
                if name:
                    res[naming] = name.checked_at
        return res
