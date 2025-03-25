from datetime import datetime

from bson import ObjectId
from mm_std import AsyncTaskRunner, Err, Result, async_synchronized, utc_delta, utc_now

from app.core.blockchains import aptos, evm, starknet
from app.core.constants import Naming
from app.core.db import NamingProblem
from app.core.services.network_service import NetworkService
from app.core.types_ import AppService, AppServiceParams


class NamingService(AppService):
    def __init__(self, base_params: AppServiceParams, network_service: NetworkService) -> None:
        super().__init__(base_params)
        self.network_service = network_service

    @async_synchronized
    async def check_next(self) -> None:
        if not self.dvalue.check_namings:
            return

        runner = AsyncTaskRunner(self.dconfig.max_workers_networks)
        for naming in list(Naming):
            runner.add_task(f"check_next_naming_{naming}", self.check_next_naming, naming)
        await runner.run()

        # tasks = ConcurrentTasks(max_workers=self.dconfig.max_workers_networks, thread_name_prefix="check_next_namings")
        # for naming in list(Naming):
        #     tasks.add_task(f"check_next_naming_{naming}", self.check_next_naming, args=(naming,))
        # tasks.execute()

    async def check_next_naming(self, naming: Naming) -> None:
        # self.logger.debug("check_next_naming called: %s", naming)

        # first check accounts that were never checked
        need_to_check = await self.db.account_naming.find(
            {"naming": naming, "checked_at": None}, limit=self.dconfig.max_workers_namings
        )
        if len(need_to_check) < self.dconfig.max_workers_namings:
            need_to_check += await self.db.account_naming.find(
                {"naming": naming, "checked_at": {"$lt": utc_delta(minutes=-1 * self.dconfig.check_naming_interval)}},
                limit=self.dconfig.max_workers_namings - len(need_to_check),
            )
        if not need_to_check:
            return

        runner = AsyncTaskRunner(self.dconfig.max_workers_namings)
        for an in need_to_check:
            runner.add_task(f"check_account_naming_{an.id}", self.check_account_naming, an.id)
        await runner.run()

        # tasks = ConcurrentTasks(max_workers=self.dconfig.max_workers_namings, thread_name_prefix="check_namings__" + naming)
        # for an in need_to_check:
        #     tasks.add_task(f"check_account_naming_{an.id}", self.check_account_naming, args=(an.id,))
        # tasks.execute()

    async def check_account_naming(self, id: ObjectId) -> Result[str | None]:
        account_naming = await self.db.account_naming.get(id)
        network = await self.network_service.get_network(account_naming.network)

        # self.logger.debug("check_account_naming called: %s / %s", account_naming.naming, account_naming.account)

        match account_naming.naming:
            case Naming.ENS:
                res = await evm.get_ens_name(network.rpc_urls, account_naming.account, proxies=self.dvalue.proxies)
            case Naming.ANS:
                res = aptos.get_ans_name(account_naming.account, proxies=self.dvalue.proxies)
            case Naming.STARKNET_ID:
                res = starknet.get_starknet_id(account_naming.account, proxies=self.dvalue.proxies)
            case _:
                return Err("Not implemented")

        if isinstance(res, Err):
            self.logger.debug("check_account_naming: %s", res.err)
            await self.db.naming_problem.insert_one(
                NamingProblem(
                    id=ObjectId(),
                    network=network.id,
                    naming=account_naming.naming,
                    account=account_naming.account,
                    message=res.err,
                )
            )
            return res

        name = res.ok or ""
        await self.db.group_naming.update_one(
            {"group_id": account_naming.group_id, "naming": account_naming.naming},
            {"$set": {f"names.{account_naming.account}": name}},
        )
        await self.db.account_naming.set(id, {"name": name, "checked_at": utc_now()})

        return res

    async def calc_oldest_checked_time(self) -> dict[Naming, datetime | None]:
        res: dict[Naming, datetime | None] = {}
        for naming in list(Naming):
            res[naming] = None
            if not await self.db.account_naming.exists({"naming": naming, "checked_at": None}):
                name = await self.db.account_naming.find_one({"naming": naming}, "checked_at")
                if name:
                    res[naming] = name.checked_at
        return res
