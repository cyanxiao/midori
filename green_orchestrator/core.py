import paramiko
import time
from typing import List


class Orchestrator:
    def __init__(self, hostname: str, username: str, password: str, subject_path: str, trial_interval: int,
                 trial_derivatives: List[str], trial_end_waiting_time: int):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.subject_path = subject_path
        self.trial_interval = trial_interval
        self.trial_derivatives = trial_derivatives
        self.trial_end_waiting_time = trial_end_waiting_time
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.connect()

    # launch an SSH connection to the remote server
    def connect(self):
        try:
            self.ssh.connect(hostname=self.hostname,
                             username=self.username, password=self.password)
        except Exception as e:
            print(f"Failed to connect to the remote server: {e}")

    # navigate to the specified directory
    def navigate(self):
        stdin, stdout, stderr = self.ssh.exec_command(
            f"cd {self.subject_path}")
        print(stdout.read().decode())

    # pause for the specified interval
    def pause(self):
        time.sleep(self.trial_interval)

    # execute the specified command
    def execute(self, command: str):
        stdin, stdout, stderr = self.ssh.exec_command(command)
        print(stdout.read().decode())
        time.sleep(self.trial_end_waiting_time)

    # collect data from the remote server
    def transfer_file_from_pod(self, pod_name_start: str, file_path_in_pod: str, local_file_path: str):
        try:
            # Finding the pod
            stdin, stdout, stderr = self.ssh.exec_command(
                f"kubectl get pods --no-headers -o custom-columns=':metadata.name'")
            pod_list = stdout.read().decode('utf-8').split()
            target_pod = next(
                (pod for pod in pod_list if pod.startswith(pod_name_start)), None)

            if not target_pod:
                print(f"No pod starts with {pod_name_start}")
                return

            print(f"Target pod found: {target_pod}")

            # Copy from the pod to the node
            node_temp_path = "/tmp/" + target_pod + "_file"
            copy_cmd = f"kubectl cp default/{target_pod}:{
                file_path_in_pod} {node_temp_path}"
            stdin, stdout, stderr = self.ssh.exec_command(copy_cmd)
            errors = stderr.read().decode()
            if errors:
                print(f"Error copying file from pod: {errors}")
                return
            print("File copied to node successfully.")

            # Transfer file from node to local machine using SFTP
            sftp = self.ssh.open_sftp()
            sftp.get(node_temp_path, local_file_path)
            print("File transferred to local machine successfully.")

            # Cleanup node
            self.execute(f"rm {node_temp_path}")
            print("Temporary files on node removed.")

        except Exception as e:
            print(f"An error occurred: {str(e)}")

    # close the SSH connection
    def close(self):
        self.ssh.close()
