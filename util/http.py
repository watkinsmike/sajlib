import logging

LOG = logging.getLogger(__name__)

try:
    import requests
    from requests.exceptions import HTTPError, Timeout

except ImportError as import_err:
    logging.error("Python [requests] module is required.")
    raise import_err

try:
    from . import exceptions
except ImportError as import_err:
    raise import_err


def get_http_response(url: str, timeout: float = 2.5) -> str:
    """
    Incomplete. Very limited functionality.
    :param url:
    :param timeout:
    :return:
    """
    try:
        response: requests.Response = requests.get(url=url, timeout=timeout)
        response.raise_for_status()
    except HTTPError as err:
        raise err
    except Timeout as timeout_err:
        raise exceptions.HTTPError(timeout_err)

    return response.text


def construct_payload():
    # placeholder
    pass
