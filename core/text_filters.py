import re


class TextFilters:

    @staticmethod
    def normalize_quotes(text):

        text = text.replace("“", '"')

        text = text.replace("”", '"')

        text = text.replace("‘", "'")

        text = text.replace("’", "'")

        return text

    @staticmethod
    def remove_multiple_spaces(text):

        return re.sub(

            r"\s+",

            " ",

            text

        )

    @staticmethod
    def remove_empty_lines(text):

        return re.sub(

            r"\n{3,}",

            "\n\n",

            text

        )

    @staticmethod
    def clean(text):

        text = TextFilters.normalize_quotes(text)

        text = TextFilters.remove_multiple_spaces(text)

        text = TextFilters.remove_empty_lines(text)

        return text