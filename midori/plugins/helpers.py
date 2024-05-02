from typing import Optional, final
from .base import execute
import time
import paramiko


class PluginHelper:
    def __init__(
        self,
        ssh: paramiko.SSHClient,
        subject_path: str,
        treatment: str,
        previous_output: Optional[str] = None,
    ):
        self._ssh = ssh
        self.subject_path = subject_path
        self.previous_output = previous_output
        self.treatment = treatment

    @final
    def execute(self) -> Optional[str]:
        command = self.action()
        if command:
            return execute(command, self._ssh)
        return None

    def action(self) -> Optional[str]:
        raise NotImplementedError("Subclasses must implement this method")


class PodHelper:
    def __init__(self, ssh, pod_name_start, namespace="default"):
        self.ssh = ssh
        self.pod_name_start = pod_name_start
        self.namespace = namespace
        self.pod = self.find_pod()

    def transfer_file_from_pod(
        self, file_path_in_pod: str, node_saving_path: str
    ) -> None:
        try:
            target_pod = self.find_pod()
            if target_pod is None:
                print(f"No pod starts with {self.pod_name_start}")
                return

            node_temp_path = self.copy_files_to_node(
                target_pod, file_path_in_pod, node_saving_path
            )
            if node_temp_path is None:
                return

        except Exception as e:
            print(f"An error occurred: {str(e)}")

    def find_pod(self) -> Optional[str]:
        command = "kubectl get pods --no-headers -o custom-columns=':metadata.name'"
        stdin, stdout, stderr = self.ssh.exec_command(command)
        pod_list = stdout.read().decode("utf-8").split()
        return next(
            (pod for pod in pod_list if pod.startswith(self.pod_name_start)), None
        )

    def copy_files_to_node(
        self, pod: str, file_path_in_pod: str, node_saving_path: str
    ) -> Optional[str]:
        # Ensure the destination directory exists
        mkdir_cmd = f"mkdir -p {node_saving_path}"
        stdin, stdout, stderr = self.ssh.exec_command(mkdir_cmd)
        errors = stderr.read().decode()
        if errors:
            print(f"Error creating directory on node: {errors}")
            return None
        print(f"Directory {node_saving_path} created or already exists.")

        # Proceed with copying files
        copy_cmd = f"kubectl cp {
            self.namespace}/{pod}:{file_path_in_pod}/. {node_saving_path}/"
        print(copy_cmd)
        stdin, stdout, stderr = self.ssh.exec_command(copy_cmd)
        errors = stderr.read().decode()
        if errors:
            print(f"Error copying files from pod: {errors}")
            return None
        print("Files copied to node successfully.")
        return node_saving_path

    def wait_for_pod_to_start(self, timeout: int):
        start_time = time.time()
        print("Waiting for the pod to be in 'Running' state...")
        while time.time() - start_time < timeout:
            command = f"kubectl get pod $(kubectl get pods --no-headers -o custom-columns=':metadata.name' | grep '{
                self.pod_name_start}') -o jsonpath='{{.status.phase}}'"
            stdin, stdout, stderr = self.ssh.exec_command(command)
            status = stdout.read().decode().strip()

            if status == "Running":
                print("Pod is in 'Running' state.")
                return True
            time.sleep(1)  # Wait for 5 seconds before checking again.

        print(f"Timed out waiting for the pod to be in 'Running' state after {
              timeout} seconds.")
        return False

    def prepare_node_environment(self, node_saving_path: str) -> bool:
        """Prepares the node directory and file for storing outputs."""
        mkdir_cmd = f"mkdir -p {node_saving_path.rsplit('/', 1)[0]}"
        touch_cmd = f"touch {node_saving_path}"
        self.ssh.exec_command(mkdir_cmd)
        self.ssh.exec_command(touch_cmd)
        print(f"Directory and file prepared at {node_saving_path}")
        return True

    def construct_query_cmd(
        self, start_time: Optional[int] = None, end_time: Optional[int] = None
    ) -> str:
        """Constructs the query command to be executed inside the pod."""
        if end_time is None:
            end_time = int(time.time())
        if start_time is None:
            start_time = end_time - 60
        return f"kubectl exec {self.pod} -- wget -qO- 'http://localhost:9090/api/v1/query_range?query=scaph_host_power_microwatts%20%2F%201000000&start={start_time}&end={end_time}&step=1'"

    def execute_query_in_pod(self, query_cmd: str, node_saving_path: str) -> None:
        """Executes the provided query command in the pod and appends output to the specified path."""
        if not self.pod:
            print("No matching pod found.")
            return

        self.prepare_node_environment(node_saving_path)

        stdin, stdout, stderr = self.ssh.exec_command(query_cmd)
        response = stdout.read().decode()

        # Append output to the file on the remote server
        append_cmd = f'echo "{response}" >> {node_saving_path}'
        _, _, stderr = self.ssh.exec_command(append_cmd)
        errors = stderr.read().decode().strip()
        if errors:
            print(f"Failed to append the response to file: {errors}")
        else:
            print("Query successfully executed and output appended to the file.")
