from bson import ObjectId
from mm_std import ConcurrentTasks, Err, Result, synchronized, utc_delta, utc_now

from app.core.blockchains import aptos, evm, starknet
from app.core.constants import Naming
from app.core.services.network_service import NetworkService
from app.core.types_ import AppService, AppServiceParams


class NamingService(AppService):
    def __init__(self, base_params: AppServiceParams, network_service: NetworkService) -> None:
        super().__init__(base_params)
        self.network_service = network_service

    @synchronized
    def check_next(self) -> None:
        if not self.dvalue.check_namings:
            return

        tasks = ConcurrentTasks(max_workers=self.dconfig.max_workers_networks)
        for naming in list(Naming):
            tasks.add_task(f"check_next_naming_{naming}", self.check_next_naming, args=(naming,))
        tasks.execute()

    def check_next_naming(self, naming: Naming) -> None:
        # self.logger.debug("check_next_naming called: %s", naming)
        max_workers = 10

        need_to_check = self.db.account_naming.find(
            {"naming": naming, "$or": [{"checked_at": None}, {"checked_at": {"$lt": utc_delta(minutes=-5)}}]},
            "checked_at",
            max_workers,
        )
        if not need_to_check:
            return

        tasks = ConcurrentTasks(max_workers=max_workers)
        for an in need_to_check:
            tasks.add_task(f"check_account_naming_{an.id}", self.check_account_naming, args=(an.id,))
        tasks.execute()

    def check_account_naming(self, id: ObjectId) -> Result[str | None]:
        account_naming = self.db.account_naming.get(id)
        network = self.network_service.get_network(account_naming.network)

        # self.logger.debug("check_account_naming called: %s / %s", account_naming.naming, account_naming.account)

        match account_naming.naming:
            case Naming.ENS:
                res = evm.get_ens_name(network.rpc_urls, account_naming.account, proxies=self.dvalue.proxies)
            case Naming.ANS:
                res = aptos.get_ans_name(account_naming.account, proxies=self.dvalue.proxies)
            case Naming.STARKNET_ID:
                res = starknet.get_starknet_id(account_naming.account, proxies=self.dvalue.proxies)
            case _:
                return Err("Not implemented")

        if isinstance(res, Err):
            self.logger.debug("check_account_naming: %s", res.err)
            return res

        name = res.ok or ""
        self.db.group_namings.update_one(
            {"group_id": account_naming.group_id, "naming": account_naming.naming},
            {"$set": {f"names.{account_naming.account}": name}},
        )
        self.db.account_naming.set(id, {"name": name, "checked_at": utc_now()})

        return res
