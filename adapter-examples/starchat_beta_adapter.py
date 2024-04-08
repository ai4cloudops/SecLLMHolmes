from adapter import LLMAdapter
import torch
from transformers import pipeline, AutoTokenizer
import os

class StarChatBetaAdapter(LLMAdapter): 
    def __init__(self):
        super().__init__()
    
    def prepare_prompt(self, **kwargs):
        if kwargs['prompt'] == 'Question':
            prompt = kwargs['code'] + '\n' + kwargs['question']
        if kwargs['prompt'] == 'Analysis':
            prompt = kwargs['code']
        if kwargs['prompt'] == 'Q/A':
            prompt = kwargs['code'] + "\n" + kwargs['question'] + "\n" + kwargs['answer']
        if kwargs['prompt'] == 'Def':
            prompt = kwargs['defin'] + "\n\n" + kwargs['code'] + "\n" + kwargs['question']
        if kwargs['prompt'] == "None":
            prompt = kwargs['code']
        return prompt
        
    def prepare(self, **kwargs):
        if 'temp' in kwargs:
            self.temp = kwargs['temp']
        self.pipe = pipeline("text-generation", model="HuggingFaceH4/starchat-beta", torch_dtype=torch.bfloat16, device_map="cuda")
        self.prompt_template = "<|system|>\n{system}<|end|>\n{examples}<|user|>\n{query}<|end|>\n<|assistant|>"
        self.tokenizer = AutoTokenizer.from_pretrained("HuggingFaceH4/starchat-beta")
     
    # Step-by-Step Prompt 3 (ZS)
    def promptSS3(self, **kwargs):
        cwe = kwargs['cwe']
        cwe_name = self.cwes[cwe]
        code = kwargs['code']

        # system
        sys = ""

        # example
        exp = []

        # overview
        prompt = "Code:\n" + code + "\n\nProvide a brief overview of the code.\nOverview: "
        overview_response = self.chat(system=sys, examples=exp, text=prompt)
        overview = overview_response.replace(prompt, "")

        # sub-components
        prompt += overview_response + "\n\nBased on the overview identify the sub-components in code that could lead to a security vulnerability knows as {}.\nSub-components: ".format(cwe_name)
        sub_response = self.chat(system=sys, examples=exp, text=prompt)
        sub = sub_response.replace(prompt, "")

        # detailed analysis
        prompt += sub_response + "\n\nPerform a detailed analysis of the identified sub-components for the existence of the {}.\nDetailed Analysis: ".format(cwe_name + " vulnerability")
        analysis_response = self.chat(system=sys, examples=exp, text=prompt)
        analysis = analysis_response.replace(prompt, "")

        # answer
        prompt += analysis_response + "\n\nBased on the detailed analysis decide and answer whether the {} is present in the given code or not.\nAnswer: ".format(cwe_name + " vulnerability")
        ans_response = self.chat(system=sys, examples=exp, text=prompt)
        ans = ans_response.replace(prompt, "")

        # response
        response = "Overview:\n" + overview + "\n\nSub-cmponents:\n" + sub + "\n\nDetailed Analysis:\n" + analysis + "\n\nAnswer:\n" + ans
        return response
        
    def chat(self, **kwargs):
        sys, exp = '', ''
        if 'system' in kwargs and kwargs['system'] != "":
            sys = kwargs['system']
        
        if 'examples' in kwargs and len(kwargs['examples']) > 0: 
            for ex in kwargs['examples']:
                exp += "<|user|>\n" + ex[0] + "<|end|>\n" 
                exp += "<|assistant|>\n" + ex[1] + "<|end|>\n"
        
        prompt = self.prompt_template.format(system=sys, examples=exp, query=kwargs['text'])

        # We use a special <|end|> token with ID 49155 to denote ends of a turn
        if self.temp == 0.0:
            outputs = self.pipe(prompt, max_new_tokens=8192, do_sample=False, temperature=self.temp, top_k=50, top_p=0.95, eos_token_id=49155)
        else:
            outputs = self.pipe(prompt, max_new_tokens=8192, do_sample=True, temperature=self.temp, top_k=50, top_p=0.95, eos_token_id=49155)
        response = outputs[0]['generated_text'].replace(prompt, "")
        return response
 