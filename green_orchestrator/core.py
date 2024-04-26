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

    # close the SSH connection
    def close(self):
        self.ssh.close()
