import paramiko
import random
from typing import List, Dict, Type
from .plugins.helpers import PluginHelper
from .treatments_helper import get_treatments
from .plugins.base import (
    checkout_branch_based_on_treatment,
    is_a_branch_exist,
    pause,
    close,
)


class Orchestrator:
    def __init__(
        self,
        hostname: str,
        username: str,
        password: str,
        repetitions: int,
        before_trial_cooling_time: int,
        trial_timespan: int,
        after_trial_cooling_time: int,
        variables: Dict[str, List[str]],
        subject_path: str,
        before_experiment_plugins: List[Type[PluginHelper]] = [],
        setup_plugins: List[Type[PluginHelper]] = [],
        end_trial_plugins: List[Type[PluginHelper]] = [],
        end_experiment_plugins: List[Type[PluginHelper]] = [],
    ) -> None:
        self.__repetitions: int = repetitions
        self.__before_experiment_plugins: List[Type[PluginHelper]] = (
            before_experiment_plugins
        )
        self.__subject_path: str = subject_path
        self.__before_trial_cooling_time: int = before_trial_cooling_time
        self.__trial_timespan: int = trial_timespan
        self.__setup_plugins: List[Type[PluginHelper]] = setup_plugins
        self.__after_trial_cooling_time: int = after_trial_cooling_time
        self.__end_trial_plugins: List[Type[PluginHelper]] = end_trial_plugins
        self.__end_experiment_plugins: List[Type[PluginHelper]] = end_experiment_plugins
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

        # Before Experiment plugins
        output = None
        for Plugin in self.__before_experiment_plugins:
            plugin = Plugin(
                ssh=self.__ssh,
                subject_path=self.__subject_path,
                treatment="",
                previous_output=output,
            )
            output = plugin.execute()

        print(f"Treatments: {self.treatments}")

        for i in range(self.__repetitions):
            print(f"Repetition {i+1}")

            randomized_treatments = random.sample(self.treatments, len(self.treatments))
            for treatment in randomized_treatments:
                if not is_a_branch_exist(
                    branch=treatment, subject_path=self.__subject_path, ssh=self.__ssh
                ):
                    print(f"Branch {treatment} does not exist.")
                    continue
                checkout_branch_based_on_treatment(
                    treatment=treatment,
                    ssh=self.__ssh,
                    subject_path=self.__subject_path,
                )

                # Before Trial Cooling time
                pause(interval=self.__before_trial_cooling_time)

                # Setup plugins
                output = None
                for Plugin in self.__setup_plugins:
                    plugin = Plugin(
                        ssh=self.__ssh,
                        subject_path=self.__subject_path,
                        treatment=treatment,
                        previous_output=output,
                    )
                    output = plugin.execute()

                # Each trial runs for a specific timespan
                pause(interval=self.__trial_timespan)

                # End Trial plugins
                output = None
                for Plugin in self.__end_trial_plugins:
                    plugin = Plugin(
                        ssh=self.__ssh,
                        subject_path=self.__subject_path,
                        treatment=treatment,
                        previous_output=output,
                    )
                    output = plugin.execute()

                # After Trial Cooling time
                pause(interval=self.__after_trial_cooling_time)

        # End Experiment plugins
        output = None
        for Plugin in self.__end_experiment_plugins:
            plugin = Plugin(
                ssh=self.__ssh,
                subject_path=self.__subject_path,
                treatment=treatment,
                previous_output=output,
            )
            output = plugin.execute()

        close(ssh=self.__ssh)
