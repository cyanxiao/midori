import paramiko
from typing import List, Dict
from .plugins.helpers import PodHelper
from .treatments_helper import get_treatments
from .plugins.base import (
    checkout_branch_based_on_treatment,
    is_a_branch_exist,
    pause,
    execute,
    close,
)


class Orchestrator:
    def __init__(
        self,
        hostname: str,
        username: str,
        password: str,
        trial_interval: int,
        trial_timespan: int,
        pod_name_start: str,
        file_path_in_pod: str,
        node_save_file_path: str,
        variables: Dict[str, List[str]],
        namespace: str = "default",
        subject_path: str = ".",
        prometheus_pod_name_start: str = "prometheus-server",
    ) -> None:
        self.__subject_path: str = subject_path
        self.__file_path_in_pod: str = file_path_in_pod
        self.__trial_interval: int = trial_interval
        self.__trial_timespan: int = trial_timespan
        self.__pod_name_start: str = pod_name_start
        self.__namespace: str = namespace
        self.__base_node_save_file_path: str = node_save_file_path
        self.__prometheus_pod_name_start: str = prometheus_pod_name_start
        self.__ssh: paramiko.SSHClient = paramiko.SSHClient()
        self.__ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        self.treatments: List[str] = get_treatments(variables=variables)

        try:
            self.__ssh.connect(hostname=hostname, username=username, password=password)
            print("Connected to the remote server.")
        except Exception as e:
            print(f"Failed to connect to the remote server: {e}")

    def run(self) -> None:
        print("Starting the experiment...")
        print(f"Treatments: {self.treatments}")
        for treatment in self.treatments:
            if not is_a_branch_exist(
                branch=treatment, subject_path=self.__subject_path, ssh=self.__ssh
            ):
                print(f"Branch {treatment} does not exist.")
                continue
            checkout_branch_based_on_treatment(
                treatment=treatment, ssh=self.__ssh, subject_path=self.__subject_path
            )

            # Cooling time
            pause(interval=self.__trial_interval)

            # Start the trial
            command: str = (
                "cd " + self.__subject_path + " && skaffold delete && skaffold run"
            )
            execute(command=command, ssh=self.__ssh)

            # Each trial runs for a specific timespan
            pause(interval=self.__trial_timespan)

            # Collect energy data
            self.__energy_collector: PodHelper = PodHelper(
                self.__ssh, self.__prometheus_pod_name_start, self.__namespace
            )
            energy_node_save_path = f"{
                self.__base_node_save_file_path}/{treatment}/energy.json"
            self.__energy_collector.execute_query_in_pod(
                node_saving_path=energy_node_save_path,
                query_cmd=self.__energy_collector.construct_query_cmd(),
            )

            # Append the treatment name to the base node save path
            treatment_node_save_path = f"{
                self.__base_node_save_file_path}/{treatment}"
            self.__pft: PodHelper = PodHelper(
                self.__ssh, self.__pod_name_start, self.__namespace
            )
            self.__pft.transfer_file_from_pod(
                self.__file_path_in_pod, treatment_node_save_path
            )

        close(ssh=self.__ssh)
