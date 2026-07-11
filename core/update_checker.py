import requests


class UpdateChecker:

    def __init__(

        self,

        github_repo

    ):

        self.repo = github_repo

    def latest(self):

        url = f"https://api.github.com/repos/{self.repo}/releases/latest"

        try:

            r = requests.get(

                url,

                timeout=10

            )

            if r.status_code != 200:

                return None

            return r.json()

        except Exception:

            return None