import re


class Replacer:

    def __init__(self):

        self.rules = {}

    def set_rules(

        self,

        rules

    ):

        self.rules = rules

    def process(

        self,

        text

    ):

        for search, replace in self.rules.items():

            pattern = re.compile(

                re.escape(search),

                flags=re.IGNORECASE

            )

            text = pattern.sub(

                replace,

                text

            )

        return text