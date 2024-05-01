from typing import Optional
import time


class PodFileTransfer:
    def __init__(self, ssh, pod_name_start, namespace='default'):
        self.ssh = ssh
        self.pod_name_start = pod_name_start
        self.namespace = namespace

    def transfer_file_from_pod(self, file_path_in_pod: str, node_saving_path: str) -> None:
        try:
            target_pod = self.find_pod()
            if target_pod is None:
                print(f"No pod starts with {self.pod_name_start}")
                return

            node_temp_path = self.copy_files_to_node(
                target_pod, file_path_in_pod, node_saving_path)
            if node_temp_path is None:
                return

        except Exception as e:
            print(f"An error occurred: {str(e)}")

    def find_pod(self) -> Optional[str]:
        command = "kubectl get pods --no-headers -o custom-columns=':metadata.name'"
        stdin, stdout, stderr = self.ssh.exec_command(command)
        pod_list = stdout.read().decode('utf-8').split()
        return next((pod for pod in pod_list if pod.startswith(self.pod_name_start)), None)

    def copy_files_to_node(self, pod: str, file_path_in_pod: str, node_saving_path: str) -> Optional[str]:
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

            if status == 'Running':
                print("Pod is in 'Running' state.")
                return True
            time.sleep(1)  # Wait for 5 seconds before checking again.

        print(f"Timed out waiting for the pod to be in 'Running' state after {
              timeout} seconds.")
        return False

    def execute_query_in_pod(self, node_saving_path: str, start_time: Optional[int] = None, end_time: Optional[int] = None) -> None:
        # Default time span: from current time - 60 seconds to current time
        if end_time is None:
            end_time = int(time.time())
        if start_time is None:
            start_time = end_time - 60

        pod = self.find_pod()
        if not pod:
            print("No matching pod found.")
            return

        # Ensure directory and file exist
        mkdir_cmd = f"mkdir -p {node_saving_path.rsplit('/', 1)[0]}"
        touch_cmd = f"touch {node_saving_path}"
        self.ssh.exec_command(mkdir_cmd)
        self.ssh.exec_command(touch_cmd)
        print(f"Directory and file ensured at {node_saving_path}")

        # Format the query to cover the specified time span
        query_cmd = f"kubectl exec {
            pod} -- wget -qO- 'http://localhost:9090/api/v1/query_range?query=scaph_host_power_microwatts%20%2F%201000000&start={start_time}&end={end_time}&step=1'"
        print(f"Executing query from {start_time} to {end_time}")
        stdin, stdout, stderr = self.ssh.exec_command(query_cmd)
        response = stdout.read().decode()

        # Append output to the file on the remote server
        append_cmd = f"echo \"{response}\" >> {node_saving_path}"
        _, _, stderr = self.ssh.exec_command(append_cmd)
        errors = stderr.read().decode().strip()
        if errors:
            print(f"Failed to append the response to file: {errors}")

        print("Query successfully executed and output appended to the file.")
