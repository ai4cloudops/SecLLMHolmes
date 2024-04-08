from adapter import LLMAdapter

class YourLLMAdapter(LLMAdapter):
    def __init__(self, temp=0.0):
        super().__init__()
        self.temp = temp

    def prepare_prompt(self, **kwargs):
        pass

    def prepare(self, **kwargs):
        pass

    def chat(self, **kwargs):
        pass

if __name__ == '__main__':
    model = YourLLMAdapter(temp=0.0)
    model.prepare()
    model.run_all(
        api_key="<OPENAI-API-KEY>",
        model="<YOUR-MODEL-NAME>"
    )