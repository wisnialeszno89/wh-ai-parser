import requests


class CompanionClient:

    def send(

        self,

        command

    ):

        response = requests.post(

            "http://localhost:8080/command",

            json=command

        )

        return response.json()