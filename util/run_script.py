import botocore.paginate
from typing import Dict, Optional, Any, Union, List, Set
import sys
import subprocess

import logging

logging.getLogger(__name__)


class RunScript:

    @staticmethod
    def run_shell_script(script_path: str, env_args: Dict[str, str], execution_timeout: Optional[int]) -> int:
        """
        runs shell script as synchronous subprocess
        :param script_path: path to script
        :param env_args: args to expose to shell script as environment variables
        :param execution_timeout: timeout to wait for completion before automatic failure
        :return: return code of the subprocess
        """
        try:
            rc = subprocess.call([script_path],
                                 env=env_args,
                                 timeout=execution_timeout)
        except OSError as os_err:
            raise OSError(os_err)
        except subprocess.TimeoutExpired as proc_err:
            raise proc_err
        return rc
