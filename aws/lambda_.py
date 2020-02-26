from typing import Mapping, Optional, Union, Any, Dict, List, TypedDict
import json
import os
import base64

import boto3
import botocore.exceptions

import sajlib.aws.exceptions
from service import AWSService

invocation_type_synchronous = 'RequestResponse'
invocation_type_asynchronous = "Event"
invocation_type_dry_run = "DryRun"


class LambdaQuery(TypedDict, total=False):
    """
    Class-based syntax type hinting: https://mypy.readthedocs.io/en/latest/more_types.html#class-based-syntax
    Represents the type mapping contract for boto3 invoke lambda
    """
    FunctionName: str
    InvocationType: str
    LogType: str
    ClientContext: str
    Payload: bytes
    Qualifier: str


class Lambda(AWSService):

    def __init__(self, region_name="us-east-1") -> None:
        super().__init__()
        self._region_name: str = region_name
        self._lambda: boto3.client = boto3.client("lambda", region_name=region_name)
        self.invocation_type_synchronous: str = "RequestResponse"
        self.invocation_type_asynchronous: str = "Event"
        self.invocation_type_dry_run: str = "DryRun"

    @property
    def region_name(self):
        return self._region_name

    @region_name.setter
    def region_name(self, region_name):
        # TODO: Add validation for proper region names
        self._region_name: str = region_name

    def invoke_lambda(self,
                      function_name: str,
                      invocation_type: Optional[str] = None,
                      payload: Optional[Union[Dict[str, Any], str, bytes]] = None,
                      get_log_tail: bool = False,
                      client_context: Optional[str] = None,
                      qualifier: Optional[str] = None) -> Dict[str, Any]:
        """

        :param function_name: Name of the lambda function. e.g. foo, foo:v1, arn:::::
        :param invocation_type:
        :param payload: Payload to pass to Lambda function.
            Can be JSON object, JSON like str, str that begins with file:// to parse JSON file, bytes
        :param get_log_tail:
        :param client_context:
        :param qualifier:
        :return:
        """

        lambda_query: LambdaQuery = self._construct_lambda_query(function_name=function_name,
                                                                 invocation_type=invocation_type,
                                                                 payload=payload,
                                                                 get_log_tail=get_log_tail,
                                                                 client_context=client_context,
                                                                 qualifier=qualifier)

        lambda_response = self._call_lambda_api(lambda_query)

        return lambda_response

    def _construct_lambda_query(self,
                                function_name: str,
                                invocation_type: Optional[str],
                                payload: Optional[Union[Dict[str, Any], str, bytes]],
                                get_log_tail: bool,
                                client_context: Optional[str],
                                qualifier: Optional[str]) -> LambdaQuery:

        query: LambdaQuery = {
            "FunctionName": function_name,
        }

        if invocation_type is not None:
            query: LambdaQuery = {**query, "InvocationType": invocation_type}

        if get_log_tail is True:
            query: LambdaQuery = {**query, "LogType": "Tail"}

        if payload is not None:
            if isinstance(payload, Mapping):
                try:
                    query: LambdaQuery = {**query, "Payload": bytes(json.dumps(payload), encoding='utf-8')}
                except json.JSONDecodeError as json_err:
                    raise sajlib.aws.exceptions.ClientError(json_err)

            elif isinstance(payload, str):
                if payload.startswith("file://"):
                    file_path = payload.split("file://")[1]
                    query: LambdaQuery = {
                        **query,
                        "Payload": bytes(json.dumps(load_json_from_file(file_path=file_path)), encoding='utf-8')
                    }
                else:
                    query: LambdaQuery = {**query, "Payload": bytes(payload, encoding='utf-8')}

            elif isinstance(payload, bytes):
                query: LambdaQuery = {**query, "Payload": payload}
            else:
                raise sajlib.aws.exceptions.ClientError(f"Improper payload type. Must be JSON like string, file, bytes")

        if client_context is not None:
            query: LambdaQuery = {**query, "ClientContext": base64.b64encode(bytes(client_context, encoding='utf-8'))}

        if qualifier is not None:
            query: LambdaQuery = {**query, "Qualifier": qualifier}

        return query

    def _call_lambda_api(self, query: LambdaQuery) -> Dict[str, Any]:

        try:
            response = self._lambda.invoke(**query)

        except botocore.exceptions.ClientError as boto_err:
            response_status_code = boto_err.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            response_error_code = boto_err.response.get("Error", {}).get("Code")
            if response_error_code == "ResourceNotFoundException":
                print(f"Resource not found: {boto_err}")
                raise sajlib.aws.exceptions.ClientError(sajlib.aws.exceptions.return_http_response(boto_err.response))
            elif response_error_code == "ValidationException":
                raise sajlib.aws.exceptions.ClientError(f"Validation error: {boto_err}")
            else:
                raise sajlib.aws.exceptions.ClientError(boto_err)
        except botocore.exceptions.ParamValidationError as boto_err:
            raise sajlib.aws.exceptions.ClientError(boto_err)

        return response


def load_json_from_file(file_path: str) -> Dict[str, Any]:
    file_path = (os.path.realpath(os.path.join(os.getcwd(), file_path)))

    try:
        with open(file=file_path) as f:
            payload = json.loads(f.read())
    except OSError as os_err:
        raise sajlib.aws.exceptions.ClientError(os_err)
    except json.decoder.JSONDecodeError as json_err:
        raise sajlib.aws.exceptions.ClientError(f"Error decoding json from file '{file_path}': {json_err}")
    return payload
