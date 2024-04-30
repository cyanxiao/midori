from typing import Optional


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
