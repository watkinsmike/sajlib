import shlex
from typing import Dict, Optional, Any, Union, List, Set
import subprocess

import logging

logging.getLogger(__name__)


class RunShell:

    @staticmethod
    def run_command(commands: Union[str, List[str]], env_args: Dict[str, str], execution_timeout: Optional[int]) -> int:
        """
        runs shell command as synchronous subprocess
        :param commands: commands to run as string or List[str], e.g. "ls -la" or ["ls", "-la"]
                         If receiving a string, use shlex to split arguments to prevent injections
                         This should not matter because Popen has shell=False as default, just added for extra security
        :param env_args: args to expose to shell script as environment variables
        :param execution_timeout: timeout to wait for completion before automatic failure
        :return: return code of the subprocess
        """
        if isinstance(commands, str):
            commands = shlex.split(commands)
        try:
            rc = subprocess.call(commands,
                                 env=env_args,
                                 timeout=execution_timeout)
        except OSError as os_err:
            raise OSError(os_err)
        except subprocess.TimeoutExpired as proc_err:
            raise proc_err
        return rc
