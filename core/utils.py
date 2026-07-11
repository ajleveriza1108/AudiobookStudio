from pathlib import Path
import os
import re
import shutil
import platform
import hashlib


def sanitize_filename(name):

    name = re.sub(

        r'[<>:"/\\\\|?*]',

        "",

        name

    )

    name = re.sub(

        r"\s+",

        " ",

        name

    )

    return name.strip()


def ensure_folder(folder):

    folder = Path(folder)

    folder.mkdir(

        parents=True,

        exist_ok=True

    )

    return folder


def human_size(size):

    units = [

        "B",

        "KB",

        "MB",

        "GB",

        "TB"

    ]

    size = float(size)

    for unit in units:

        if size < 1024:

            return f"{size:.2f} {unit}"

        size /= 1024

    return f"{size:.2f} PB"


def folder_size(folder):

    folder = Path(folder)

    total = 0

    for file in folder.rglob("*"):

        if file.is_file():

            total += file.stat().st_size

    return human_size(total)


def free_disk(folder):

    usage = shutil.disk_usage(folder)

    return human_size(

        usage.free

    )


def operating_system():

    return platform.system()


def is_windows():

    return platform.system() == "Windows"


def sha256(file):

    file = Path(file)

    h = hashlib.sha256()

    with open(

        file,

        "rb"

    ) as f:

        while True:

            data = f.read(

                1024 * 1024

            )

            if not data:

                break

            h.update(data)

    return h.hexdigest()


def next_available_file(path):

    path = Path(path)

    if not path.exists():

        return path

    counter = 2

    while True:

        candidate = path.with_stem(

            f"{path.stem}_{counter}"

        )

        if not candidate.exists():

            return candidate

        counter += 1