from engines.kokoro_engine import KokoroEngine

engine = KokoroEngine()

engine.speak(

    text="""
Hello.

This is Audiobook Studio.

The Kokoro engine has been integrated successfully.
""",

    output_file="Output/engine_test.wav"

)

print("Finished.")