WORDS_PER_MINUTE = 155


def estimate_duration(

    text

):

    words = len(

        text.split()

    )

    minutes = words / WORDS_PER_MINUTE

    hours = int(minutes // 60)

    mins = int(minutes % 60)

    return hours, mins


def estimate_size(

    duration_minutes,

    bitrate=192

):

    mb = (

        duration_minutes *

        bitrate *

        60

    ) / 8192

    return round(

        mb,

        2

    )