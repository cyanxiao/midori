import paramiko
import time
from typing import List, Any, Dict
from .file_transfer import PodFileTransfer
from .treatments_helper import get_treatments


class Orchestrator:
    def __init__(self, hostname: str, username: str, password: str, trial_interval: int, trial_timespan: int,
                 pod_name_start: str, file_path_in_pod: str, node_save_file_path: str, local_save_file_path: str, variables:  Dict[str, List[str]],
                 namespace: str = 'default', subject_path: str = '.', prometheus_pod_name_start: str = 'prometheus-server') -> None:
        self.__subject_path: str = subject_path
        self.__file_path_in_pod: str = file_path_in_pod
        self.__local_save_file_path: str = local_save_file_path
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
            self.__ssh.connect(hostname=hostname,
                               username=username, password=password)
            print("Connected to the remote server.")
        except Exception as e:
            print(f"Failed to connect to the remote server: {e}")

    def run(self) -> None:
        for treatment in self.treatments:
            if not self.__is_a_branch_exist(treatment):
                print(f"Branch {treatment} does not exist.")
                continue
            self.checkout_branch_based_on_treatment(treatment)
            self.__pause(interval=self.__trial_interval)
            command: str = "cd " + self.__subject_path + \
                " && skaffold delete && skaffold run"
            self.__execute(command=command)

            self.__pause(interval=self.__trial_timespan)

            # # Collect energy data
            self.__energy_collector: PodFileTransfer = PodFileTransfer(
                self.__ssh, self.__prometheus_pod_name_start, self.__namespace)
            energy_node_save_path = f"{
                self.__base_node_save_file_path}/{treatment}/energy.txt"
            self.__energy_collector.execute_query_in_pod(
                node_saving_path=energy_node_save_path)

            # Append the treatment name to the base node save path
            treatment_node_save_path = f"{
                self.__base_node_save_file_path}/{treatment}"
            self.__pft: PodFileTransfer = PodFileTransfer(
                self.__ssh, self.__pod_name_start, self.__namespace)
            self.__pft.transfer_file_from_pod(
                self.__file_path_in_pod, treatment_node_save_path)
        # skaffold_delete_command: str = "cd " + \
        #     self.__subject_path + " && skaffold delete"
        # self.__execute(command=skaffold_delete_command)
        self.__close()

    def checkout_branch_based_on_treatment(self, treatment: str) -> None:
        command: str = f"cd {self.__subject_path} && git checkout {treatment}"
        self.__execute(command=command)

    def __is_a_branch_exist(self, branch: str) -> bool:
        command: str = f"cd {
            self.__subject_path} && git branch --list {branch}"
        stdin, stdout, stderr = self.__ssh.exec_command(command)
        return bool(stdout.read().decode())

    def __pause(self, interval: float) -> None:
        print(f"Pausing for {interval} seconds...")
        time.sleep(interval)

    def __execute(self, command: str) -> None:
        stdin, stdout, stderr = self.__ssh.exec_command(command)
        print(command)
        print(stdout.read().decode())

    def __close(self) -> None:
        self.__ssh.close()
