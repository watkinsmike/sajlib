import os
from datetime import datetime
from shutil import copyfile
import logging

LOG = logging.getLogger(__name__)


def whoami(location: str) -> str:
    """
    Returns the server role
    :param location: file that contains server role metadata
    :return: string designating server role
    """
    try:
        with open(location) as f:
            machine_role = f.read()
    except FileNotFoundError as err:
        raise OSError(f"{location} not found or inaccessible. {err}")
    except OSError as err:
        raise OSError(f"Problem accessing {location}. {err}")
    return machine_role


def backup_file(src: str,
                backup_suffix: str = "." + datetime.now().strftime("%Y-%m-%d-%H%M%S")) -> None:
    """
    Makes a copy of the src file by appending suffix on end.
    :param src: File to make copy of
    :param backup_suffix: Suffix to append to destination file. This should make file unique always
    :return: None
    """
    try:
        if os.path.isfile(src):
            LOG.debug(f"Backing up {src} to {src}{backup_suffix}")
            copyfile(src, src + backup_suffix)
        else:
            raise FileNotFoundError(f"Source file not found or inaccessible: {src}")
    except OSError as os_err:
        raise os_err
