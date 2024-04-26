import paramiko
import time
from typing import List
from .file_transfer import PodFileTransfer


class Orchestrator:
    def __init__(self, hostname: str, username: str, password: str, subject_path: str, trial_interval: int,
                 pod_name_start: str, file_path_in_pod: str, node_save_file_path: str, local_save_file_path: str, namespace='default'):
        self.__subject_path = subject_path
        self.__file_path_in_pod = file_path_in_pod
        self.__local_save_file_path = local_save_file_path
        self.__pod_name_start = pod_name_start
        self.__namespace = namespace
        self.__node_save_file_path = node_save_file_path

        self.__ssh = paramiko.SSHClient()
        self.__ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.__ssh.connect(hostname=hostname,
                               username=username, password=password)
            print("Connected to the remote server.")
        except Exception as e:
            print(f"Failed to connect to the remote server: {e}")

    # run the orchestrator
    def run(self):
        command = "cd " + self.__subject_path + " && skaffold delete && skaffold run"
        self.__execute(command=command)
        self.__pause(float(100))
        self.__pft = PodFileTransfer(
            self.__ssh, self.__pod_name_start, self.__namespace)
        self.__pft.transfer_file_from_pod(
            self.__file_path_in_pod, self.__node_save_file_path)
        self.__close()

    """
    Basic Functions
    """

    # pause for the specified interval
    def __pause(self, interval: float):
        print(f"Pausing for {interval} seconds...")
        time.sleep(interval)

    # execute the specified command
    def __execute(self, command: str):
        stdin, stdout, stderr = self.__ssh.exec_command(command)
        print(command)
        print(stdout.read().decode())

    # close the SSH connection
    def __close(self):
        self.__ssh.close()
