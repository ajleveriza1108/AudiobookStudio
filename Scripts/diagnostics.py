from pathlib import Path
import torch

from core.system_info import SystemInfo
from engines.kokoro import KokoroEngine


def main():

    print("="*60)

    print("Audiobook Studio Diagnostics")

    print("="*60)

    info=SystemInfo.summary()

    print()

    for key,value in info.items():

        print(key)

        print(value)

        print()

    print("="*60)

    engine=KokoroEngine()

    print(engine.info())

    print()

    print("Voices")

    print("-"*60)

    for voice in engine.available_voices():

        print(voice)

    print()

    print("CUDA")

    print(torch.cuda.is_available())

    if torch.cuda.is_available():

        print(torch.cuda.get_device_name(0))

        print(torch.cuda.memory_allocated(0))

        print(torch.cuda.memory_reserved(0))

    print("="*60)


if __name__=="__main__":

    main()