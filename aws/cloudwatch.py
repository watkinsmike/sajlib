import decimal
import datetime
import botocore.exceptions
from typing import List, Any, Union, Dict

from .service import AWSService
from . import exceptions

from boto3 import client


class CloudWatch(AWSService):

    def __init__(self, region_name: str = "us-east-1"):
        super().__init__()
        self._cw = client('cloudwatch', region_name=region_name)

    def put_metric(self, name_space: str, metric_data: List[Any]):
        """
        Push custom metric to CloudWatch
        https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/cloudwatch.html#CloudWatch.Client.put_metric_data
        :param name_space: The custom namespace to push the metric
        :param metric_data: Custom metric data. Can be passed normally or by using construct_metric_data() helper func
        ex: combined_metric_data.append(construct_metric_data(metric_name="metric",
                                                          dimensions=[{"Name": "foo", "Value": "bar"}],
                                                          unit="Count",
                                                          timestamp=datetime.datetime.now(),
                                                          value=1))
        :return:
        """

        query = {
            "Namespace": name_space,
            "MetricData": metric_data
        }

        try:
            response = self._cw.put_metric_data(**query)

        except botocore.exceptions.ClientError as boto_err:
            # Saved for future usage
            error_code: str = boto_err.response.get('Error', {}).get('Code')
            error_message: str = boto_err.response.get('Error', {}).get('Message')
            error_http_response_code: int = boto_err.response.get('Error', {}).get('HTTPStatusCode')
            raise exceptions.ClientError(exception=boto_err)
        except botocore.exceptions.NoCredentialsError as boto_err:
            raise exceptions.ClientError(exception=boto_err)

        return response

    @staticmethod
    def construct_metric_data(metric_name: str,
                              value: Union[float, decimal.Decimal, int],
                              dimensions: List[Dict[str, str]],
                              unit: str,
                              timestamp: datetime.datetime = datetime.datetime.now()) -> Dict[str, Any]:
        """
        Constructs metric data to be used to push custom metrics to CloudWatch
        :param metric_name:
        :param value:
        :param dimensions:
        :param timestamp:
        :param unit:
        :return: Mapping of metric data to be used with put_metric()
        """

        metric_data = {
            "MetricName": metric_name,
            "Dimensions": dimensions,
            "Timestamp": timestamp,
            "Unit": unit,
            "Value": value
        }

        return metric_data
