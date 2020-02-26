import logging
from typing import Optional, Dict, List, Mapping, Union, Any
from .service import AWSService
from . import exceptions

import botocore.paginate
from boto3 import client
import botocore.exceptions

# Removed default logger from caller module
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# root = logging.getLogger()
# if root.handlers:
#     for handler in root.handlers:
#         root.removeHandler(handler)

# logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.DEBUG)


class ParameterStore(AWSService):

    def __init__(self, region_name: str = "us-east-1"):
        super().__init__()
        self._ssm = client('ssm', region_name=region_name)

    def retrieve_params(self, params: List[str], with_decryption: bool = False) -> Dict[str, Any]:

        query = {
            "Names": params,
            "WithDecryption": with_decryption
        }

        try:
            response: Dict[str, Any] = self._ssm.get_parameters(**query)

            # Even if no parameters are found, AWS will return a 200. Have to explicitly look for failures
            # get_parameters() does not throw an exception on parameter not found or invalid unlike get_parameter()
            invalid_params = response.get("InvalidParameters")
            if invalid_params:
                raise exceptions.ClientError(error_message=f"There were '{len(invalid_params)}' invalid parameter(s) : "
                                                           f"{invalid_params} are either malformed or do not exist.")

        except botocore.exceptions.ClientError as boto_err:
            # Saved for future usage
            error_code: str = boto_err.response.get('Error', {}).get('Code')
            error_message: str = boto_err.response.get('Error', {}).get('Message')
            error_http_response_code: int = boto_err.response.get('Error', {}).get('HTTPStatusCode')
            ex_message = error_message
            raise exceptions.ClientError(error_message=error_message)
        except botocore.exceptions.NoCredentialsError as boto_err:
            # Custom no credentials found error if desired
            raise exceptions.ClientError(exception=boto_err)

        return self._get_mapping_from_response(response=response)

    def retrieve_params_by_path(self,
                                param_path: str,
                                recursive: bool,
                                with_decryption: bool) -> Dict[str, str]:
        """
        Retrieve all the params that exists in the passed path
        Example: With passed path as /foo/bar/
                 Non-recursive mode will find /foo/bar/secret1, /foo/bar/secret2,
                 Recursive mode will find /foo/bar/secret1, /foo/bar/secret2/, /foo/bar/service/secret
        :param with_decryption:
        :param recursive:
        :param param_path:
        :return: Paginator for returned parameters
        """

        query = {
            "Path": param_path,
            "Recursive": recursive,
            "WithDecryption": with_decryption
        }

        try:
            paginator = self._ssm.get_paginator('get_parameters_by_path')
            pager = paginator.paginate(**query)

        except botocore.exceptions.ClientError as boto_err:
            raise exceptions.ClientError(exception=boto_err)

        # Getting the paginator could succeed, but pagination can still fail
        # try:
        structured_params = self._get_mapping_from_response(response=pager)
        # except exceptions.ClientError as err:
        #     raise exceptions.ClientError(exception=err)

        return structured_params

    def _get_mapping_from_response(self, response: Dict[str, Any]) -> Dict[str, str]:
        """
        Receives an AWS get_parameters(), get_parameters_by_path() or paginator('get_parameters_by_path') response,
        pull the name of the key and it's associate value and returns all of them as a mapping object.
        e.g. {key1: value1, key2: value2, ...}
        """
        params: Dict[str, str] = dict()

        if isinstance(response, botocore.paginate.PageIterator):
            try:
                for page in response:
                    for config in page['Parameters']:
                        params = {**params,
                                  **self._get_key_and_value_from_response(retrieve_parameter_response=config)}
            except (botocore.exceptions.ClientError,
                    botocore.exceptions.NoCredentialsError) as boto_err:
                raise exceptions.ClientError(error_message=f"Error when paginating response:",
                                             exception=boto_err)

        else:
            for resp in response['Parameters']:
                params = {**params,
                          **self._get_key_and_value_from_response(retrieve_parameter_response=resp)}

        return params

    @staticmethod
    def trim_param_keys(param_dict: Dict[str, str]) -> Dict[str, str]:
        """
        Trims the parameter paths of kv pairs to just the final key name and returns the resulting dictionary
        This will be used to map dictionary keys to variable names used for rendering Jinja templates
        e.g. devops/server/foo is trimmed to foo, foo="bar" which is used to template out {{ foo }} to "bar"
        This is useful if passing the dictionary as 1-1 mappings for environment variables
        :param param_dict: Dictionary of {"parameter_path" : "param_value"} kv pairs
        :return: Dictionary with trimmed paths replacing original keys
                 e.g. {"/foo/bar/bind": "value"} becomes {"bind": "value"}
        """
        new_param_dict: Dict[str, Any] = dict()

        for k, v in param_dict.items():
            new_param_dict[k.split("/")[-1]] = v

        return new_param_dict

    def _get_value_from_response(self, retrieve_parameter_response: Dict[str, Any]) -> str:
        """
        Retrieves only the value from a single parameter response
        """
        try:
            param: str = retrieve_parameter_response['Value']
        except KeyError as err:
            raise exceptions.ClientError(f"Error retrieving parameter value from response object {err}")

        return param

    def _get_key_from_response(self, retrieve_parameter_response: Dict[str, Any]) -> str:

        try:
            param: str = retrieve_parameter_response['Name']
        except KeyError as err:
            raise exceptions.ClientError(f"Error retrieving parameter value from response object {err}")

        return param

    def _get_key_and_value_from_response(self, retrieve_parameter_response: Dict[str, Any]) -> Dict[str, str]:
        try:
            key: str = retrieve_parameter_response['Name']
            value: str = retrieve_parameter_response['Value']
        except KeyError as err:
            raise exceptions.ClientError(f"Error retrieving parameter value from response object {err}")
        return {key: value}
