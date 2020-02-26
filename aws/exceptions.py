class ClientError(Exception):
    def __init__(self, error_message: str = "", exception: Exception = None):
        self.error_message = error_message
        if exception:
            self.error_message = self.error_message + str(exception)

    def __str__(self):
        return self.error_message


def return_http_response(error_message):
    message = error_message.get('Error', {}).get('Message')
    response_code = error_message.get('ResponseMetadata', {}).get('HTTPStatusCode')
    if response_code is None:
        response_code = 500
    error = {
        "statusCode": response_code,
        "body": {
            "message": message
        }
    }
    return error
