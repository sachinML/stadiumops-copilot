import os
import unittest

from copilot.config import get_settings


class TestConfig(unittest.TestCase):
    def test_settings_reads_current_env_vars_each_call(self):
        original = os.environ.get("LLM_PROVIDER")
        try:
            os.environ["LLM_PROVIDER"] = "openai"
            self.assertEqual(get_settings().llm_provider, "openai")

            os.environ["LLM_PROVIDER"] = "ollama"
            self.assertEqual(get_settings().llm_provider, "ollama")
        finally:
            if original is None:
                os.environ.pop("LLM_PROVIDER", None)
            else:
                os.environ["LLM_PROVIDER"] = original

    def test_settings_defaults_without_env_vars(self):
        original = os.environ.pop("LLM_PROVIDER", None)
        try:
            self.assertEqual(get_settings().llm_provider, "ollama")
        finally:
            if original is not None:
                os.environ["LLM_PROVIDER"] = original


if __name__ == "__main__":
    unittest.main()
