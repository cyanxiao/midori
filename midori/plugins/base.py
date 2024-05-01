import time
from paramiko import SSHClient


def checkout_branch_based_on_treatment(treatment: str, subject_path: str, ssh: SSHClient) -> None:
    command: str = f"cd {subject_path} && git checkout {treatment}"
    execute(command=command, ssh=ssh)


def is_a_branch_exist(branch: str, subject_path: str, ssh: SSHClient) -> bool:
    command: str = f"cd {
        subject_path} && git branch --list {branch}"
    stdin, stdout, stderr = ssh.exec_command(command)
    return bool(stdout.read().decode())


def pause(interval: float) -> None:
    print(f"Pausing for {interval} seconds...")
    time.sleep(interval)


def execute(command: str, ssh: SSHClient) -> None:
    stdin, stdout, stderr = ssh.exec_command(command)
    print(command)
    print(stdout.read().decode())


def close(ssh: SSHClient) -> None:
    ssh.close()
