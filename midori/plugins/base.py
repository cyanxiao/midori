import time
import logging
from paramiko import SSHClient
from typing import Optional

logging.basicConfig(level=logging.INFO)


def checkout_branch_based_on_treatment(
    treatment: str, subject_path: str, ssh: SSHClient
) -> None:
    """Checkout to a specific git branch."""
    try:
        command = f"cd {subject_path} && git checkout {treatment}"
        execute(command, ssh)
    except Exception as e:
        logging.error(f"Failed to checkout branch {treatment}: {e}")


def is_a_branch_exist(branch: str, subject_path: str, ssh: SSHClient) -> bool:
    """Check if a specific git branch exists in the repository."""
    command = f"cd {subject_path} && git branch --list {branch}"
    try:
        stdin, stdout, stderr = ssh.exec_command(command)
        return bool(stdout.read().decode().strip())
    except Exception as e:
        logging.error(f"Error checking if branch exists {branch}: {e}")
        return False


def pause(interval: float) -> None:
    """Pause the execution for a specified number of seconds."""
    logging.info(f"Pausing for {interval} seconds...")
    time.sleep(interval)


def execute(command: str, ssh: SSHClient) -> Optional[str]:
    """Execute a command over SSH and log the output or error."""
    try:
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode()
        if output:
            logging.info(f"Command output: {output}")
            return output
        else:
            logging.info(f"Executed command with no output: {command}")
    except Exception as e:
        logging.error(f"Error executing command {command}: {e}")


def close(ssh: SSHClient) -> None:
    """Close the SSH client connection."""
    try:
        ssh.close()
        logging.info("SSH connection closed successfully.")
    except Exception as e:
        logging.error(f"Failed to close SSH connection: {e}")
