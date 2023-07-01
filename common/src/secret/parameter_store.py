import boto3


class ParameterStore:
    """Class manipulate and access secrets from AWS Parameter Store"""
    def __init__(self):
        self._ssm_client = boto3.client("ssm")

    def get_parameter(self, parameter_name: str, with_decryption: bool = True) -> str:
        return self._ssm_client.get_parameter(
            Name=parameter_name,
            WithDecryption=with_decryption
        )["Parameter"]["Value"]
