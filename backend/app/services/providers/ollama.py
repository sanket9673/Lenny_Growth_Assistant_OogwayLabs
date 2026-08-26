class OllamaProvider:
    """Mock/wrapper class for local Ollama provider execution matching test assertions."""

    def __init__(self, base_url: str = None):
        self.name = "ollama"
        self.base_url = base_url

    def generate(self, prompt: str) -> str:
        return "Local Ollama response text"
