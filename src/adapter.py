from prompt_templates import PromptTemplates
from helper_functions import HelperFunctions
from experiments import ExperimentRunner

class LLMAdapter(HelperFunctions, PromptTemplates, ExperimentRunner):
    def __init__(self):
        super().__init__()

    def prepare(self, **kwargs):
        pass

    def prepare_prompt(self, **kwargs):
        return "Can you find the vulnerabilities in this code?"

    def chat(self, **kwargs):
        return "It has vulnerabilities."

if __name__ == "__main__":
    adapter = LLMAdapter()
    adapter.prepare()
    adapter.run_all(
        api_key="YOUR_API_KEY",
        model="YOUR_MODEL_NAME"
    )