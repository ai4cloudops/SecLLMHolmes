from adapter import LLMAdapter
from llama import Llama

class LLaMaAdapter(LLMAdapter):
     
    def __init__(self):
        super().__init__()
    
    def prepare_prompt(self, **kwargs):
        if kwargs['prompt'] == 'Question':
            prompt = kwargs['question'] + "\n\n" + kwargs['code']
        if kwargs['prompt'] == 'Analysis':
            prompt = kwargs['code']
        if kwargs['prompt'] == 'Q/A':
            prompt = kwargs['question'] + "\n\n" + kwargs['code'] + "\n\n" + kwargs['answer']
        if kwargs['prompt'] == 'Def':
            prompt = kwargs['defin'] + "\n\n" + kwargs['question'] + "\n\n" + kwargs['code']
        if kwargs['prompt'] == 'None':
            prompt = kwargs['code']
        return prompt
    
    def prepare(self, **kwargs):
        self.temp = kwargs['temp']
        self.generator = Llama.build(
            ckpt_dir=kwargs['ckpt_dir'],
            tokenizer_path=kwargs['tokenizer_path'],
            max_seq_len=11000,
            max_batch_size=1
        )

    def chat(self, **kwargs):
        instructions = []
        if 'system' in kwargs:
            if kwargs['system'] != "":
                instructions.append({"role": "system", "content": kwargs['system']})
        if 'examples' in kwargs:
            if kwargs['examples'] != []:
                for ex in kwargs['examples']:
                    instructions.append({"role": "user", "content": ex[0]})
                    instructions.append({"role": "assistant", "content": ex[1]})
        instructions.append({"role": "user", "content": kwargs['text']})
        results = self.generator.chat_completion(
            [instructions], 
            max_gen_len=None,
            temperature= self.temp,
            top_p=0.95,
        )
        return results[0]['generation']['content']
