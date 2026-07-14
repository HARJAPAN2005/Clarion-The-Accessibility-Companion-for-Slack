import os
from dotenv import load_dotenv

load_dotenv()

print("OPENROUTER_API_KEY:", "SET" if os.getenv("OPENROUTER_API_KEY") else "NOT SET")

from agent import run_clarion, ClarionDeps

class MockClient:
    def chat_postMessage(self, *args, **kwargs):
        pass
    def reactions_add(self, *args, **kwargs):
        pass

deps = ClarionDeps(client=MockClient(), user_id="U123", channel_id="C123", prefs={})

def on_chunk(text):
    print(f"CHUNK: {repr(text)}")

print("Running clarion...")
result = run_clarion("Simplify this: Leverage our synergies to boil the ocean ASAP.", deps, on_chunk=on_chunk)
print("FINAL RESULT:")
print(result)
