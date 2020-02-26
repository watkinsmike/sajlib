import sajlib.aws.lambda_

lambda_ = sajlib.aws.lambda_.Lambda(region_name='us-east-1')

def contract_resource_not_found():
    data = lambda_.invoke_lambda(function_name="foo")
    print(data)

if __name__ == '__main__':
    contract_resource_not_found()