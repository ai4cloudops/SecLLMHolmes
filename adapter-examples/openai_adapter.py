import openai, time
from openai import OpenAI
from adapter import LLMAdapter

class GPTAdapter(LLMAdapter):
    def __init__(self, temp=0.0):
        super().__init__()
        self.temp = temp

    def prepare_prompt(self, **kwargs):
        if kwargs['prompt'] == "Question":
            prompt = "Code: \"\"\"\n" + kwargs['code'] + "\n\"\"\"\n" + kwargs['question']
        if kwargs['prompt'] == "Analysis":
            prompt = kwargs['code']
        if kwargs['prompt'] == "Q/A":
            prompt = "Code: \"\"\"\n" + kwargs['code'] + "\n\"\"\"\n" + kwargs['question'] + "\n" + kwargs['answer']
        if kwargs['prompt'] == "Def":
            prompt = kwargs['defin'] + "\n\nCode: \"\"\"\n" + kwargs['code'] + "\n\"\"\"\n" + kwargs['question']
        if kwargs['prompt'] == "None":
            prompt = "Code: \"\"\"\n" + kwargs['code'] + "\n\"\"\""
        return prompt

    def prepare(self, **kwargs):
        self.model_client = OpenAI(api_key=kwargs['api_key'])
        self.model = kwargs['model'] # e.g. "gpt-3.5-turbo", "gpt-4" (API name of the model)

    def chat(self, **kwargs):
        # prepare messages
        msgs = []
        if 'system' in kwargs:
            if kwargs['system'] != "":
                msgs.append({"role": "system", "content": kwargs['system']})
        if 'examples' in kwargs:
            if kwargs['examples'] != []:
                for ex in kwargs['examples']:
                    msgs.append({"role": "user", "content": ex[0]})
                    msgs.append({"role": "assistant", "content": ex[1]})
        msgs.append({"role": "user", "content": kwargs['text']})

        # send request
        itr = 5
        while itr:
            try:
                response = self.model_client.chat.completions.create(
                    model = self.model,
                    temperature = self.temp,
                    messages = msgs
                )
                return response.choices[0].message.content
            except openai.RateLimitError as e:
                print("Rate limit reached. Waiting for 60 seconds...")
                time.sleep(60)
            except openai.APIError as e:
                itr -= 1
                print("Retrying...")
        return None
