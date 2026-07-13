import unittest

from copilot.llm import ChatMessage, OllamaLLM, OpenAICompatibleLLM


UNREACHABLE_URL = "http://127.0.0.1:1"  # port 1 is reserved; nothing listens here


class TestLlmResilience(unittest.TestCase):
    """
    A live LLM provider being unreachable (network blip, rate limit, bad key)
    must never raise/crash the app — it should degrade gracefully instead.
    """

    def test_ollama_chat_degrades_gracefully_when_unreachable(self):
        llm = OllamaLLM(base_url=UNREACHABLE_URL, model="llama3.1", timeout_s=2.0)
        reply = llm.chat([ChatMessage(role="user", content="hello")])
        self.assertIsInstance(reply, str)
        self.assertIn("couldn't reach the GenAI provider", reply)
        self.assertIn("ollama:llama3.1", reply)

    def test_openai_compatible_chat_degrades_gracefully_when_unreachable(self):
        llm = OpenAICompatibleLLM(
            base_url=UNREACHABLE_URL, api_key="fake-key", model="test-model", timeout_s=2.0
        )
        reply = llm.chat([ChatMessage(role="user", content="hello")])
        self.assertIsInstance(reply, str)
        self.assertIn("couldn't reach the GenAI provider", reply)
        self.assertIn("openai-compatible:test-model", reply)


if __name__ == "__main__":
    unittest.main()
