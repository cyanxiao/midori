from .helpers import PluginHelper, PodHelper


class SkaffoldSetup(PluginHelper):
    def action(self) -> str:
        return f"cd {self.subject_path} && skaffold delete && skaffold run"


class EnergyDataCollection(PluginHelper):
    def action(self) -> None:
        energy_collector: PodHelper = PodHelper(
            self._ssh, "prometheus-server", "default"
        )
        energy_node_save_path = f"~/research/results/{self.treatment}/energy.json"
        energy_collector.execute_query_in_pod(
            node_saving_path=energy_node_save_path,
            query_cmd=energy_collector.construct_query_cmd(),
        )


class LoadTestingDataCollection(PluginHelper):
    def action(self) -> None:
        treatment_node_save_path = f"~/research/results/{self.treatment}"
        pft: PodHelper = PodHelper(self._ssh, "loadgenerator", "default")
        pft.transfer_file_from_pod("/loadgen", treatment_node_save_path)
