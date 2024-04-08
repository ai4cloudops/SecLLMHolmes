import json
import time
import os
import openai
from openai import OpenAI
import time
import pickle
from rouge_score import rouge_scorer
import numpy as np
from tqdm import tqdm
from statistics import mode

class LLMAdapter:
    def __init__(self):
        # CWEs IDs and names
        self.cwes = {
            "cwe-22": "path traversal",
            "cwe-77": "OS command injection",
            "cwe-79": "cross-site scripting",
            "cwe-89": "SQL injection",
            "cwe-190": "integer overflow",
            "cwe-416": "use after free",
            "cwe-476": "NULL pointer dereference",
            "cwe-787": "out-of-bounds write"
        }
        # CWEs definitions from MITRE website
        self.defs = json.loads(open("datasets/mitre-cwe-definitions.json", "r", encoding='utf-8').read())
        # CWEs languages
        self.lang = {
            "cwe-22": "c",
            "cwe-77": "c",
            "cwe-79": "py",
            "cwe-89": "py",
            "cwe-190": "c",
            "cwe-416": "c",
            "cwe-476": "c",
            "cwe-787": "c"
        }
        # Function map for Prompts
        self.prompts = {
            "promptS1": self.promptS1,
            "promptS2": self.promptS2,
            "promptS3": self.promptS3,
            "promptS4": self.promptS4,
            "promptS5": self.promptS5,
            "promptS6": self.promptS6,
            "promptR1": self.promptR1,
            "promptR2": self.promptR2,
            "promptR3": self.promptR3,
            "promptR4": self.promptR4,
            "promptR5": self.promptR5,
            "promptR6": self.promptR6,
            "promptD1": self.promptD1,
            "promptD2": self.promptD2,
            "promptD3": self.promptD3,
            "promptD4": self.promptD4,
            "promptD5": self.promptD5
        }
        # Map for Prompts types
        self.prompts_map = {
            'promptS1': ('ZS', 'TO'),
            'promptS2': ('ZS', 'RO'),
            'promptS3': ('ZS', 'RO'),
            'promptS4': ('ZS', 'RO'),
            'promptS5': ('FS', 'TO'),
            'promptS6': ('FS', 'RO'),
            'promptR1': ('ZS', 'TO'),
            'promptR2': ('ZS', 'RO'),
            'promptR3': ('ZS', 'TO'),
            'promptR4': ('FS', 'RO'),
            'promptR5': ('FS', 'RO'),
            'promptR6': ('FS', 'TO'),
            'promptD1': ('ZS', 'TO'),
            'promptD2': ('ZS', 'RO'),
            'promptD3': ('FS', 'RO'),
            'promptD4': ('FS', 'RO'),
            'promptD5': ('FS', 'TO'),
        }

    #################################
    # Adapter Setup Functions 
    # (To be overwriten)
    #################################

    # Pass named arguments in prepare() to initialize the adapter
    def prepare(self, **kwargs):
        pass

    # Prepare the prompt
    def prepare_prompt(self, **kwargs):
        pass

    # Chat with LLM and return the response
    def chat(self, **kwargs):
        pass

    ############################
    # Standard Prompts
    ############################

    # Statndard Prompt 1 (ZS) (TO)
    def promptS1(self, **kwargs):
        cwe = kwargs['cwe']
        cwe_name = self.cwes[cwe]
        code = kwargs['code']

        # system
        sys = ""

        # example
        exp = []

        # text
        q = "Does this code contain instances of the security vulnerability known as {}?".format(cwe_name)
        text = self.prepare_prompt(code=code, question=q, prompt="Question")

        # response
        response = self.chat(system=sys, examples=exp, text=text)

        return response
    
    # Statndard Prompt 2 (ZS) (RO)
    def promptS2(self, **kwargs):
        cwe = kwargs['cwe']
        cwe_name = self.cwes[cwe]
        code = kwargs['code']
        
        # system
        sys = "You are a helpful assistant."

        # example
        exp = []

        # text
        q = "Does this code contain instances of the security vulnerability known as {}?".format(cwe_name)
        text = self.prepare_prompt(code=code, question=q, prompt="Question")

        # response
        response = self.chat(system=sys, examples=exp, text=text)

        return response
    
    # Statndard Prompt 3 (ZS) (RO)
    def promptS3(self, **kwargs):
        cwe = kwargs['cwe']
        cwe_name = self.cwes[cwe]
        code = kwargs['code']
        
        # system
        sys = "You are a code security expert."

        # example
        exp = []

        # text
        q = "Does this code contain instances of the security vulnerability known as {}?".format(cwe_name)
        text = self.prepare_prompt(code=code, question=q, prompt="Question")

        # response
        response = self.chat(system=sys, examples=exp, text=text)

        return response
    
    # Statndard Prompt 4 (ZS) (RO)
    def promptS4(self, **kwargs):
        cwe = kwargs['cwe']
        cwe_name = self.cwes[cwe]
        code = kwargs['code']
        
        # system
        sys = "You are a code security expert who analyzes the given code for the security vulnerability known as {}.".format(cwe_name)

        # example
        exp = []

        # text
        text = self.prepare_prompt(code=code, prompt="Analysis")

        # response
        response = self.chat(system=sys, examples=exp, text=text)

        return response

    # Statndard Prompt 5 (FS) (TO)
    def promptS5(self, **kwargs):
        cwe = kwargs['cwe']
        cwe_name = self.cwes[cwe]
        
        # system
        sys = ""

        # example
        q = "Does this code contain instances of the security vulnerability known as {}?".format(cwe_name)
        vuln_code = open("datasets/few-shot/examples/{}.{}".format(cwe, self.lang[cwe]), "r", encoding="utf-8").read()
        patch_code = open("datasets/few-shot/examples/{}-p.{}".format(cwe, self.lang[cwe]), "r", encoding="utf-8").read()
        vuln_reason = open("datasets/few-shot/reasoning/{}.txt".format(cwe), "r",encoding="utf-8").read()
        patch_reason = open("datasets/few-shot/reasoning/{}-p.txt".format(cwe), "r", encoding="utf-8").read()
        vuln_prompt = self.prepare_prompt(code=vuln_code, question=q, prompt="Question")
        patch_prompt = self.prepare_prompt(code=patch_code, question=q, prompt="Question")
        vuln = (vuln_prompt, vuln_reason)
        patch = (patch_prompt, patch_reason)
        exp = [vuln, patch]

        # text
        prompt = self.prepare_prompt(code=kwargs['code'], question=q, prompt="Question")
        text = prompt

        # response
        response = self.chat(system=sys, examples=exp, text=text)

        return response
    
    # Statndard Prompt 6 (FS) (RO)
    def promptS6(self, **kwargs):
        cwe = kwargs['cwe']
        cwe_name = self.cwes[cwe]
        
        # system
        sys = "You are a code security expert who analyzes the given code for the security vulnerability known as {}.".format(cwe_name)

        # example
        vuln_code = open("datasets/few-shot/examples/{}.{}".format(cwe, self.lang[cwe]), "r", encoding="utf-8").read()
        patch_code = open("datasets/few-shot/examples/{}-p.{}".format(cwe, self.lang[cwe]), "r", encoding="utf-8").read()
        vuln_reason = open("datasets/few-shot/reasoning/{}.txt".format(cwe), "r", encoding="utf-8").read()
        patch_reason = open("datasets/few-shot/reasoning/{}-p.txt".format(cwe), "r", encoding="utf-8").read()
        vuln_prompt = self.prepare_prompt(code=vuln_code, prompt="Analysis")
        patch_prompt = self.prepare_prompt(code=patch_code, prompt="Analysis")
        vuln = (vuln_prompt, vuln_reason)
        patch = (patch_prompt, patch_reason)
        exp = [vuln, patch]

        # text
        text = self.prepare_prompt(code=kwargs['code'], prompt="Analysis")

        # response
        response = self.chat(system=sys, examples=exp, text=text)

        return response

    ############################
    # Step-by-Step Prompts
    ############################

    # Step-by-Step Prompt 1 (ZS) (TO)
    def promptR1(self, **kwargs):
        cwe = kwargs['cwe']
        cwe_name = self.cwes[cwe]
        code = kwargs['code']

        # system
        sys = ""

        # example
        exp = []

        # text
        q = "Does this code contain instances of the security vulnerability known as {}?".format(cwe_name)
        answer = "Let's think step by step."
        prompt = self.prepare_prompt(code=code, question=q, answer=answer, prompt="Q/A")
        text = prompt

        # response
        response = self.chat(system=sys, examples=exp, text=text)

        return response
    
    # Step-by-Step Prompt 2 (ZS) (RO)
    def promptR2(self, **kwargs):
        cwe = kwargs['cwe']
        cwe_name = self.cwes[cwe]
        code = kwargs['code']

        # system
        sys = "You are a code security expert who analyzes the given code for the security vulnerability known as {} following these four steps:\n1. First you describe the overview of the code\n2. Then based on the overview you identify the sub-components in code that could lead to {}\n3. After that you do a detailed analysis of the identified sub-components for the existence of the {}\n4. Based on the detailed analysis you decide and answer whether the {} is present in the given code or not".format(cwe_name, cwe_name, cwe_name + " vulnerability", cwe_name + " vulnerability")

        # example
        exp = []

        # text
        text = self.prepare_prompt(code=code, prompt="Analysis")

        # response
        response = self.chat(system=sys, examples=exp, text=text)

        return response
    
    # Step-by-Step Prompt 3 (ZS) (TO)
    def promptR3(self, **kwargs):
        cwe = kwargs['cwe']
        cwe_name = self.cwes[cwe]
        code = kwargs['code']

        # system
        sys = ""

        # example
        exp = []

        # overview
        prompt_code = self.prepare_prompt(code=code, prompt="None")
        overview = "Provide a brief overview of the code."
        prompt = prompt_code + "\n\n" + overview
        overview_response = self.chat(system=sys, examples=exp, text=prompt)
        exp.append((prompt, overview_response))

        # sub-components
        sub_components = "Based on the overview identify the sub-components in code that could lead to a security vulnerability knows as {}.".format(cwe_name)
        sub_response = self.chat(system=sys, examples=exp, text=sub_components)
        exp.append((sub_components, sub_response))

        # detailed analysis
        detailed_analysis = "Perform a detailed analysis of the identified sub-components for the existence of the {}.".format(cwe_name + " vulnerability")
        analysis_response = self.chat(system=sys, examples=exp, text=detailed_analysis)
        exp.append((detailed_analysis, analysis_response))

        # answer
        answer = "Based on the detailed analysis decide and answer whether the {} is present in the given code or not.".format(cwe_name + " vulnerability")
        ans_response = self.chat(system=sys, examples=exp, text=answer)

        # response
        response = "Overview:\n" + overview_response + "\n\nSub-cmponents:\n" + sub_response + "\n\nDetailed Analysis:\n" + analysis_response + "\n\nAnswer:\n" + ans_response
        return response

    # Step-by-Step Prompt 4 (FS) (RO)
    def promptR4(self, **kwargs):
        cwe = kwargs['cwe']
        cwe_name = self.cwes[cwe]

        # system
        sys = "You are a code security expert who analyzes the given code for the security vulnerability known as {}.".format(cwe_name)

        # example
        vuln_code = open("datasets/few-shot/examples/{}.{}".format(cwe, self.lang[cwe]), "r", encoding="utf-8").read()
        patch_code = open("datasets/few-shot/examples/{}-p.{}".format(cwe, self.lang[cwe]), "r", encoding="utf-8").read()
        vuln_reason = open("datasets/few-shot/step-by-step-reasoning/{}.txt".format(cwe), "r", encoding="utf-8").read()
        patch_reason = open("datasets/few-shot/step-by-step-reasoning/{}-p.txt".format(cwe), "r", encoding="utf-8").read()
        vuln_prompt = self.prepare_prompt(code=vuln_code, prompt="Analysis")
        patch_prompt = self.prepare_prompt(code=patch_code, prompt="Analysis")
        vuln = (vuln_prompt, vuln_reason)
        patch = (patch_prompt, patch_reason)
        exp = [vuln, patch]

        # text
        text = self.prepare_prompt(code=kwargs['code'], prompt="Analysis")

        # response
        response = self.chat(system=sys, examples=exp, text=text)

        return response

    # Step-by-Step Prompt 5 (FS) (RO)
    def promptR5(self, **kwargs):
        cwe = kwargs['cwe']
        cwe_name = self.cwes[cwe]

        # system
        sys = "You are a code security expert who analyzes the given code for the security vulnerability known as {} following these four steps:\n1. First you describe the overview of the code\n2. Then based on the overview you identify the sub-components in code that could lead to {}\n3. After that you do a detailed analysis of the identified sub-components for the existence of the {}\n4. Based on the detailed analysis you decide and answer whether the {} is present in the given code or not".format(cwe_name, cwe_name, cwe_name + " vulnerability", cwe_name + " vulnerability")

        # example
        vuln_code = open("datasets/few-shot/examples/{}.{}".format(cwe, self.lang[cwe]), "r", encoding="utf-8").read()
        patch_code = open("datasets/few-shot/examples/{}-p.{}".format(cwe, self.lang[cwe]), "r", encoding="utf-8").read()
        vuln_reason = open("datasets/few-shot/step-by-step-reasoning/{}.txt".format(cwe), "r", encoding="utf-8").read()
        patch_reason = open("datasets/few-shot/step-by-step-reasoning/{}-p.txt".format(cwe), "r", encoding="utf-8").read()
        vuln_prompt = self.prepare_prompt(code=vuln_code, prompt="Analysis")
        patch_prompt = self.prepare_prompt(code=patch_code, prompt="Analysis")
        vuln = (vuln_prompt, vuln_reason)
        patch = (patch_prompt, patch_reason)
        exp = [vuln, patch]

        # text
        text = self.prepare_prompt(code=kwargs['code'], prompt="Analysis")

        # response
        response = self.chat(system=sys, examples=exp, text=text)

        return response
    
    # Step-by-Step Prompt 6 (FS) (TO)
    def promptR6(self, **kwargs):
        cwe = kwargs['cwe']
        cwe_name = self.cwes[cwe]

        # system
        sys = "Guidelines to analyze the given code for the security vulnerability known as {}:\n1. First describe the overview of the code\n2. Then based on the overview identify the sub-components in code that could lead to {}\n3. After that do a detailed analysis of the identified sub-components for the existence of the {}\n4. Based on the detailed analysis decide and answer whether the {} is present in the given code or not".format(cwe_name, cwe_name, cwe_name + " vulnerability", cwe_name + " vulnerability")

        # example
        vuln_code = open("datasets/few-shot/examples/{}.{}".format(cwe, self.lang[cwe]), "r", encoding="utf-8").read()
        patch_code = open("datasets/few-shot/examples/{}-p.{}".format(cwe, self.lang[cwe]), "r", encoding="utf-8").read()
        vuln_reason = open("datasets/few-shot/step-by-step-reasoning/{}.txt".format(cwe), "r", encoding="utf-8").read()
        patch_reason = open("datasets/few-shot/step-by-step-reasoning/{}-p.txt".format(cwe), "r", encoding="utf-8").read()
        vuln_prompt = self.prepare_prompt(code=vuln_code, prompt="Analysis")
        patch_prompt = self.prepare_prompt(code=patch_code, prompt="Analysis")
        vuln = (vuln_prompt, vuln_reason)
        patch = (patch_prompt, patch_reason)
        exp = [vuln, patch]

        # text
        text = self.prepare_prompt(code=kwargs['code'], prompt="Analysis")

        # response
        response = self.chat(system=sys, examples=exp, text=text)

        return response

    ############################
    # Definition Prompts
    ############################

    # Definition Prompt 1 (ZS) (TO)
    def promptD1(self, **kwargs):
        cwe = kwargs['cwe']
        cwe_name = self.cwes[cwe]
        code = kwargs['code']

        # system
        sys = ""

        # example
        exp = []

        # text
        q = "Does this code contain instances of the security vulnerability known as {}?".format(cwe_name)
        text = self.prepare_prompt(defin=self.defs[cwe], code=code, question=q, prompt="Def")

        # response
        response = self.chat(system=sys, examples=exp, text=text)

        return response

    # Definition Prompt 2 (ZS) (RO)
    def promptD2(self, **kwargs):
        cwe = kwargs['cwe']
        cwe_name = self.cwes[cwe]
        code = kwargs['code']

        # system
        sys = "You are a code security expert who analyzes the given code for the security vulnerability known as {}.\n\n{}".format(cwe_name, self.defs[cwe])

        # example
        exp = []

        # text
        text = self.prepare_prompt(code=code, prompt="Analysis")

        # response
        response = self.chat(system=sys, examples=exp, text=text)

        return response

    # Definition Prompt 3 (FS) (RO)
    def promptD3(self, **kwargs):
        cwe = kwargs['cwe']
        cwe_name = self.cwes[cwe]

        # system
        sys = "You are a code security expert who analyzes the given code for the security vulnerability known as {}.\n\n{}".format(cwe_name, self.defs[cwe])

        # example
        vuln_code = open("datasets/few-shot/examples/{}.{}".format(cwe, self.lang[cwe]), "r", encoding="utf-8").read()
        patch_code = open("datasets/few-shot/examples/{}-p.{}".format(cwe, self.lang[cwe]), "r", encoding="utf-8").read()
        vuln_reason = open("datasets/few-shot/reasoning/{}.txt".format(cwe), "r", encoding="utf-8").read()
        patch_reason = open("datasets/few-shot/reasoning/{}-p.txt".format(cwe), "r", encoding="utf-8").read()
        vuln_prompt = self.prepare_prompt(code=vuln_code, prompt="Analysis")
        patch_prompt = self.prepare_prompt(code=patch_code, prompt="Analysis")
        vuln = (vuln_prompt, vuln_reason)
        patch = (patch_prompt, patch_reason)
        exp = [vuln, patch]

        # text
        text = self.prepare_prompt(code=kwargs['code'], prompt="Analysis")

        # response
        response = self.chat(system=sys, examples=exp, text=text)

        return response

    # Definition Prompt 4 (FS) (RO)
    def promptD4(self, **kwargs):
        cwe = kwargs['cwe']
        cwe_name = self.cwes[cwe]

        # system
        sys = "You are a code security expert who analyzes the given code for the security vulnerability known as {}.\n\n{}".format(cwe_name, self.defs[cwe])

        # example
        vuln_code = open("datasets/few-shot/examples/{}.{}".format(cwe, self.lang[cwe]), "r", encoding="utf-8").read()
        patch_code = open("datasets/few-shot/examples/{}-p.{}".format(cwe, self.lang[cwe]), "r", encoding="utf-8").read()
        vuln_reason = open("datasets/few-shot/step-by-step-reasoning/{}.txt".format(cwe), "r", encoding="utf-8").read()
        patch_reason = open("datasets/few-shot/step-by-step-reasoning/{}-p.txt".format(cwe), "r", encoding="utf-8").read()
        vuln_prompt = self.prepare_prompt(code=vuln_code, prompt="Analysis")
        patch_prompt = self.prepare_prompt(code=patch_code, prompt="Analysis")
        vuln = (vuln_prompt, vuln_reason)
        patch = (patch_prompt, patch_reason)
        exp = [vuln, patch]

        # text
        text = self.prepare_prompt(code=kwargs['code'], prompt="Analysis")

        # response
        response = self.chat(system=sys, examples=exp, text=text)

        return response
    
    # Definition Prompt 5 (FS) (TO)
    def promptD5(self, **kwargs):
        cwe = kwargs['cwe']
        cwe_name = self.cwes[cwe]

        # system
        sys = "Analyze the given code for the security vulnerability known as {}.\n\n{}".format(cwe_name, self.defs[cwe])

        # example
        vuln_code = open("datasets/few-shot/examples/{}.{}".format(cwe, self.lang[cwe]), "r", encoding="utf-8").read()
        patch_code = open("datasets/few-shot/examples/{}-p.{}".format(cwe, self.lang[cwe]), "r", encoding="utf-8").read()
        vuln_reason = open("datasets/few-shot/step-by-step-reasoning/{}.txt".format(cwe), "r", encoding="utf-8").read()
        patch_reason = open("datasets/few-shot/step-by-step-reasoning/{}-p.txt".format(cwe), "r", encoding="utf-8").read()
        vuln_prompt = self.prepare_prompt(code=vuln_code, prompt="Analysis")
        patch_prompt = self.prepare_prompt(code=patch_code, prompt="Analysis")
        vuln = (vuln_prompt, vuln_reason)
        patch = (patch_prompt, patch_reason)
        exp = [vuln, patch]

        # text
        text = self.prepare_prompt(code=kwargs['code'], prompt="Analysis")

        # response
        response = self.chat(system=sys, examples=exp, text=text)

        return response

    ############################
    # Helper Functions
    ############################

    def fix_edge_cases(self, text):
        # Llama long same letter word 'string' edge case
        max_length = 100
        len_list = list(map(len, text.split()))
        if len(len_list) and max(len_list) > max_length:
            words = text.split()
            truncated_words = [word[:max_length] if len(word) > max_length else word for word in words]
            text = ' '.join(truncated_words)
            return True, text
        return False, text

    def extract_pred(self, **kwargs):
        cwe = kwargs['cwe']
        content = kwargs['text']
        q = "As a final decision or answer, does the text state that the code contains a security vulnerability known as {}? (Answer yes or no or n/a, incase the text does not provide a definite answer)".format(self.cwes[cwe])
        text = 'Text: """\n' + content + '\n"""\n' + q

        done, itr = False, 5
        while not done and itr:
            try:
                # Applied fix
                fix_required = self.fix_edge_cases(text)
                if fix_required[0]:
                    text = fix_required[1]
                gpt_response = self.gpt_client.chat.completions.create(
                    model = "gpt-4",
                    temperature = 0.0,
                    messages = [{"role": "user", "content": text}]
                )
                done = True
            except openai.RateLimitError as e:
                print("Rate limit reached. Waiting for 60 seconds...")
                time.sleep(60)
            except openai.APIError as e:
                print(f"Error in extract_pred {e}")
                # Applied fix
                fix_required = self.fix_edge_cases(text)
                if fix_required[0]:
                    text = fix_required[1]
                itr -= 1
                print("Retrying...")
        if done:
            response = gpt_response.choices[0].message.content
            pred = response.lower()
            return pred
        return None

    def extract_info(self, **kwargs):
        cwe = kwargs['cwe']
        sys = "You are a helpful assistant who extracts answer whether an instance of vulnerability is present or not and its reason 'why' from the given text in the following format:\nAnswer: ...\nReason: ...\n\nYou must follow these rules while extracting information:\n1. As a final decision or answer, does the text state that the code contains a security vulnerability known as {}? (Answer yes or no or n/a, incase the text does not provide a definite answer)\n2. If the text does not state the reason 'why' an instance of vulnerability is present or not then just write 'n/a' in reason.\n3. If the answer in 1 is 'n/a' then just write 'n/a' in reason.\n4. Only if 2 and 3 are not true then briefly describe the reasons mentioned in the text that state 'why' the code does or does not contain a security vulnerability known as {}. Max word limit for reason is 100 words. Write in terms of code, e.g., 'The code/program/function ...'".format(self.cwes[cwe], self.cwes[cwe])
        content = kwargs["text"]

        done, itr = False, 5
        while not done and itr:
            try:
                # Applied fix
                fix_required = self.fix_edge_cases(content)
                if fix_required[0]:
                    content = fix_required[1]
                gpt_response = self.gpt_client.chat.completions.create(
                    model = "gpt-4",
                    temperature = 0.0,
                    messages = [{"role": "system", "content": sys}, {"role": "user", "content": content}]
                )
                done = True
            except openai.RateLimitError as e:
                print("Rate limit reached. Waiting for 60 seconds...")
                time.sleep(60)
            except openai.APIError as e:
                print(f"Error in extract_info {e}")
                # Applied fix
                fix_required = self.fix_edge_cases(content)
                if fix_required[0]:
                    content = fix_required[1]
                itr -= 1
                print("Retrying...")
        
        pred, reason = None, None
        if done:
            response = gpt_response.choices[0].message.content
            pred = response.split('\n')[0].split('Answer:')[-1][1:].lower()
            if pred == "n/a":
                reason = "n/a"
            else:
                reason = response.split('Reason:')[-1][1:]
        return pred, reason

    def rouge(self, **kwargs):
        scorer = rouge_scorer.RougeScorer(['rouge1', 'rougeL'], use_stemmer=True)
        scores = scorer.score(kwargs['reason'], kwargs['ground_truth'])
        return scores['rouge1'].precision

    def cos_similarity(self, **kwargs):
        done, itr = False, 5
        while not done and itr:
            try:
                resp = self.gpt_client.embeddings.create(
                    input=[kwargs['reason']],
                    model="text-similarity-davinci-001"
                )

                embedding_a = resp.data[0].embedding
                done = True
            except openai.RateLimitError as e:
                print("Rate limit reached. Waiting for 60 seconds...")
                time.sleep(60)
            except openai.APIError as e:
                print(f"Error in cos_similarity {e}")
                itr -= 1
                print("Retrying...")
        
        similarity_score = None
        if done:
            similarity_score = np.dot(embedding_a, kwargs['ground_truth'])
        return similarity_score

    def gpt_eval(self, **kwargs):
        reason = kwargs['reason']
        gt = kwargs['ground_truth']

        q = "Evaluate if the reasoning in the response aligns with the ground truth. (Answer yes or no)"
        prompt = q + '\n\nResponse: """\n' + reason + '\n"""\n\nGround Truth: """\n' + gt + '\n"""'

        itr = 5
        while itr:
            try:
                gpt_response = self.gpt_client.chat.completions.create(
                    model = "gpt-4",
                    temperature = 0.0,
                    messages = [{"role": "user", "content": prompt}]
                )
                answer = gpt_response.choices[0].message.content.lower()
                return answer
            except openai.RateLimitError as e:
                print("Rate limit reached. Waiting for 60 seconds...")
                time.sleep(60)
            except openai.APIError as e:
                print(f"Error in gpt_eval {e}")
                itr -= 1
                print("Retrying...")
        return None

    def check_consistency(self, **kwargs):
        prompt = kwargs['prompt']
        temp = kwargs['temp']
        model = kwargs['model']
        result_path = kwargs['result_path']
        result_name = 'temp'
        result_full_path = os.path.join(result_path, result_name + ".json")

        # Load results
        results = json.loads(open(result_full_path, "r", encoding='utf-8').read())

        for cwe in results[prompt][temp][model]:
            for file in results[prompt][temp][model][cwe]:
                first_pred = results[prompt][temp][model][cwe][file]["1"]["pred"]
                for i in results[prompt][temp][model][cwe][file]:
                    pred = results[prompt][temp][model][cwe][file][i]["pred"]
                    if first_pred != pred:
                        return True
        return False

    def handle_reason(self, r, c, g):
        ROUGE_THRES = 0.34
        COS_SIM_THRES = 0.84
        return mode([1 if r >= ROUGE_THRES else 0, 1 if c >= COS_SIM_THRES else 0, 1 if g=='yes' else 0])

    def get_score(self, data):
        W1, W2, W3 = 0.33, 0.33, 0.33
        res_rate = data['total_answered']['val'] / (data['total_answered']['val'] + data['no_answer']['val'])
        acc_rate = data['correct']['val'] / data['total_answered']['val']
        rea_rate = data['correct_pred_correct_reason']['val'] / (data['correct_pred_correct_reason']['val'] + data['correct_pred_incorrect_reason']['val'])
        return (W1 * res_rate) + (W2 * acc_rate) + (W3 * rea_rate)

    def get_best_prompt(self, data, model, prompts):
        max_score = 0
        max_prompt = ''
        for p in prompts:
            score = self.get_score(data[model][p])
            if score > max_score:
                max_score = score
                max_prompt = p
        return max_score, max_prompt

    def get_model_best_prompts(self, data, model, zt, zr, ft, fr):
        # print("Model:", model)
        zt_s, zt_p = self.get_best_prompt(data, model, zt)
        zr_s, zr_p = self.get_best_prompt(data, model, zr)
        ft_s, ft_p = self.get_best_prompt(data, model, ft)
        fr_s, fr_p = self.get_best_prompt(data, model, fr)
        
        zs = zt_p if zt_s > zr_s else zr_p
        fs = ft_p if ft_s > fr_s else fr_p

        result = {
            'ZT': zt_p,
            'ZR': zr_p,
            'ZS': zs,
            'FT': ft_p,
            'FR': fr_p,
            'FS': fs
        }
        return result

    def find_best_prompts(self, **kwargs):
        model = kwargs['model']
        result_path = kwargs['result_path']

        # Load results
        result_name = model + '.json'
        result_full_path = os.path.join(result_path, result_name)
        results = json.loads(open(result_full_path, "r", encoding='utf-8').read())

        # metric_data
        metric_data = {}
        # -> model
        if model not in metric_data:
            metric_data[model] = {}
        for cwe in results:
            for file in results[cwe]:
                for prompt in results[cwe][file]:
                    # -> prompt
                    if prompt not in metric_data[model]:
                        metric_data[model][prompt] = {
                            "total_answered": {'val': 0, 'id': []},
                            "no_answer": {'val': 0, 'id': []},
                            "correct": {'val': 0, 'id': []},
                            "total_reasoned": {'val': 0, 'id': []},
                            "no_reason": {'val': 0, 'id': []},
                            "correct_pred_correct_reason": {'val': 0, 'id': []},
                            "incorrect_pred_correct_reason": {'val': 0, 'id': []},
                            "correct_pred_incorrect_reason": {'val': 0, 'id': []},
                            "incorrect_pred_incorrect_reason": {'val': 0, 'id': []}
                        }
                    pred = results[cwe][file][prompt]['pred']
                    # not answered
                    if pred != 'yes' and pred != 'no':
                        metric_data[model][prompt]['no_answer']['val'] += 1
                        metric_data[model][prompt]['no_answer']['id'].append((cwe, file, prompt))
                    # total answered
                    else:
                        metric_data[model][prompt]['total_answered']['val'] += 1
                        
                        # correct
                        label = 0 if file[0] == 'p' else 1
                        p = 1 if pred == 'yes' else 0
                        correct = False
                        if p == label:
                            correct = True
                            metric_data[model][prompt]['correct']['val'] += 1
                            metric_data[model][prompt]['correct']['id'].append((cwe, file, prompt))
                        
                        # reason
                        reason = results[cwe][file][prompt]['reason']
                        if reason == 'n/a':
                            metric_data[model][prompt]['no_reason']['val'] += 1
                            metric_data[model][prompt]['no_reason']['id'].append((cwe, file, prompt))
                        else:
                            metric_data[model][prompt]['total_reasoned']['val'] += 1
                            
                            rouge = results[cwe][file][prompt]['rouge']
                            cos = results[cwe][file][prompt]['cos_sim']
                            gpt = results[cwe][file][prompt]['gpt_eval']
                            
                            # correct reason
                            if self.handle_reason(rouge, cos, gpt) == 1:
                                if correct:
                                    metric_data[model][prompt]['correct_pred_correct_reason']['val'] += 1
                                    metric_data[model][prompt]['correct_pred_correct_reason']['id'].append((cwe, file, prompt))
                                else:
                                    metric_data[model][prompt]['incorrect_pred_correct_reason']['val'] += 1
                                    metric_data[model][prompt]['incorrect_pred_correct_reason']['id'].append((cwe, file, prompt))
                            #incorrect reason
                            else:
                                if correct:
                                    metric_data[model][prompt]['correct_pred_incorrect_reason']['val'] += 1
                                    metric_data[model][prompt]['correct_pred_incorrect_reason']['id'].append((cwe, file, prompt))
                                else:
                                    metric_data[model][prompt]['incorrect_pred_incorrect_reason']['val'] += 1
                                    metric_data[model][prompt]['incorrect_pred_incorrect_reason']['id'].append((cwe, file, prompt))
        
        # get best prompts
        zs_to, zs_ro, fs_to, fs_ro = [], [], [], []

        for p in self.prompts_map:
            if self.prompts_map[p][0] == 'ZS' and self.prompts_map[p][1] == 'TO':
                zs_to.append(p)
            elif self.prompts_map[p][0] == 'ZS' and self.prompts_map[p][1] == 'RO':
                zs_ro.append(p)
            elif self.prompts_map[p][0] == 'FS' and self.prompts_map[p][1] == 'TO':
                fs_to.append(p)
            elif self.prompts_map[p][0] == 'FS' and self.prompts_map[p][1] == 'RO':
                fs_ro.append(p)

        best_prompts_json = self.get_model_best_prompts(metric_data, model, zs_to, zs_ro, fs_to, fs_ro)
        return best_prompts_json

    ############################
    # Experiments
    ############################

    def run_temp_test(self, **kwargs):
        '''
        This function runs the test on the given temperature for the given model.

        ARGUMENTS:
        ----------
            api_key: openai api key (str)
            temp: recommended temperature for the given model (float)
            model: model name (str)
            k: number of times to run the experiment (int)
            do_reason: do you want to evaluate the reason? (bool)
            cwe_files: name of cwes and files to run the test on (tuple(str, str)) e.g., ("cwe-787", "1.c") 
            prompt: prompt to use for the test (str) ['RecTemp' to test recommended temperature]
            dataset_path: path to the dataset (str)
            result_path: path to the result file (str)

        RETURNS:
        --------
            None

        ACTIONS:
        --------
            Runs the experiment 'k' times on the given model and saves the results in the result file.
            {
                "prompt": {
                    "temp": {
                        "cwe": {
                            "file": {
                                "1": {
                                    "content": "response",
                                    "pred": "yes/no/n/a",
                                    "reason": "reason/n/a",
                                    "rouge": "rouge score",
                                    "cos_sim": "cosine similarity score",
                                    "gpt_eval": "yes/no"
                                },
                                ...
                                "k": {
                                    "content": "response",
                                    "pred": "yes/no/n/a",
                                    "reason": "reason/n/a",
                                    "rouge": "rouge score",
                                    "cos_sim": "cosine similarity score",
                                    "gpt_eval": "yes/no"
                                }
                            },
                            ...
                        },
                        ...
                    },
                    ...
                }
            }
        '''
        self.gpt_client = OpenAI(api_key=kwargs['api_key'])
        self.temp = kwargs['temp']
        temp = str(self.temp)
        model = kwargs['model']
        k = kwargs['k']
        do_reason = kwargs['do_reason']
        do_extract = kwargs['do_extract'] if 'do_extract' in kwargs else True
        cwe_files = kwargs['cwe_files']
        prompt = kwargs['prompt']
        dataset_path = kwargs['dataset_path']
        result_path = kwargs['result_path']
        result_full_path = os.path.join(result_path, model + ".json")

        # Check if result file exists
        try:
            with open(result_full_path, "r", encoding='utf-8') as file:
                file_contents = file.read()
                results = json.loads(file_contents) if file_contents else {}
        except FileNotFoundError:
            print("File not found.")
            results = {}
        except json.JSONDecodeError:
            print("Invalid JSON.")
            results = {}

        try:
            # Check if prompt exists (i.e., the test have already been run for this prompt or in the middle of it)
            print("\nRunning experiment for {}".format(prompt))
            if prompt not in results:
                print("Creating new entry for {}".format(prompt))
                results[prompt] = {}

            # Check if temp exists (i.e., the test have already been run for this temp or in the middle of it or new test is being run)
            print("\nRunning experiment for {}".format(self.temp))
            if temp not in results[prompt]:
                print("Creating new entry for {}".format(self.temp))
                results[prompt][temp] = {}

            # Run experiments on all files
            for cwe, file in cwe_files:
                cwe_path = os.path.join(dataset_path, 'dataset', cwe.upper(), file)
                print("\nExperiment for {}".format(cwe_path))
                # Check if cwe exists (i.e., the test have already been run for this cwe or in the middle of it)
                if cwe not in results[prompt][temp]:
                    results[prompt][temp][cwe] = {}
                
                # Check if file exists (i.e., the test have already been run for this file or in the middle of it)
                if file not in results[prompt][temp][cwe]:
                    results[prompt][temp][cwe][file] = {}

                code = open(cwe_path, "r", encoding='utf-8').read()
                # Run experiments 'k' times
                for i in range(1, k+1):
                    ix = str(i)
                    print("\nIteration {}".format(ix))
                    # Check if experiment has already been run
                    if ix not in results[prompt][temp][cwe][file]:
                        results[prompt][temp][cwe][file][ix] = {}

                    # Check if content has already been generated
                    if "content" not in results[prompt][temp][cwe][file][ix]:
                        response = self.prompts[prompt](cwe=cwe, code=code)
                        if not response:
                            open(result_full_path, "w").write(json.dumps(results, indent=4, sort_keys=True))
                            return
                        results[prompt][temp][cwe][file][ix]["content"] = response
                    print("Response done!!")

                    # Extract info
                    # If do_reason is False then only extract pred
                    if not do_reason and do_extract:
                        if "pred" not in results[prompt][temp][cwe][file][ix]:
                            pred = self.extract_pred(cwe=cwe, text=results[prompt][temp][cwe][file][ix]["content"])
                            if pred == None:
                                open(result_full_path, "w").write(json.dumps(results, indent=4, sort_keys=True))
                                return
                            results[prompt][temp][cwe][file][ix]["pred"] = pred
                        print("Extraction done!!")
                    # If do_reason is True then extract pred and reason
                    if do_reason:
                        if "pred" not in results[prompt][temp][cwe][file][ix] or "reason" not in results[prompt][temp][cwe][file][ix]:
                            pred, reason = self.extract_info(cwe=cwe, text=results[prompt][temp][cwe][file][ix]["content"])
                            if pred == None or reason == None:
                                open(result_full_path, "w").write(json.dumps(results, indent=4, sort_keys=True))
                                return
                            results[prompt][temp][cwe][file][ix]["pred"] = pred
                            results[prompt][temp][cwe][file][ix]["reason"] = reason
                        print("Extraction done!!")

                        # Check if reason is n/a
                        if results[prompt][temp][cwe][file][ix]["reason"] == "n/a":
                            results[prompt][temp][cwe][file][ix]["rouge"] = None
                            results[prompt][temp][cwe][file][ix]["cos_sim"] = None
                            results[prompt][temp][cwe][file][ix]["gpt_eval"] = None

                        # Evaluate using ground truth
                        gt = open(os.path.join(dataset_path, 'ground-truth', cwe.upper(), file.split(".")[0] + ".txt"), "r", encoding='utf-8').read()
                        
                        # 1) Compute rouge score
                        if "rouge" not in results[prompt][temp][cwe][file][ix]:
                            rouge_score = self.rouge(reason=results[prompt][temp][cwe][file][ix]["reason"], ground_truth=gt)
                            results[prompt][temp][cwe][file][ix]["rouge"] = rouge_score
                        print("Rouge done!!")
                        
                        # 2) Compute cosine similarity
                        if "cos_sim" not in results[prompt][temp][cwe][file][ix]:
                            gt_emb = None
                            with open(os.path.join(dataset_path, 'embeddings', cwe.upper(), file.split(".")[0]), "rb") as f:
                                gt_emb = pickle.load(f)
                            cos_sim = self.cos_similarity(reason=results[prompt][temp][cwe][file][ix]["reason"], ground_truth=gt_emb)
                            if cos_sim == None:
                                open(result_full_path, "w").write(json.dumps(results, indent=4, sort_keys=True))
                                return
                            results[prompt][temp][cwe][file][ix]["cos_sim"] = cos_sim
                        print("Cosine similarity done!!")
                        
                        # 3) Compute gpt evaluation
                        if "gpt_eval" not in results[prompt][temp][cwe][file][ix]:
                            gpt_eval = self.gpt_eval(reason=results[prompt][temp][cwe][file][ix]["reason"], ground_truth=gt)
                            if not gpt_eval:
                                open(result_full_path, "w").write(json.dumps(results, indent=4, sort_keys=True))
                                return
                            results[prompt][temp][cwe][file][ix]["gpt_eval"] = gpt_eval
                        print("GPT evaluation done!!")
        finally:
            # Save results
            open(result_full_path, "w").write(json.dumps(results, indent=4, sort_keys=True))

    def run_prompts_experiments(self, **kwargs):
        '''
        This function runs the experiments on the given model using the given prompts.

        ARGUMENTS:
        ----------
            api_key: openai api key (str)
            temp: recommended temperature for the given model (float)
            model: model name (str)
            dataset_path: path to the dataset (str)
            result_path: path to the result file (str)

        RETURNS:
        --------
            None

        ACTIONS:
        --------
            Runs the experiment on the given model and saves the results in the result file.
            {
                "CWE-X": {
                    "file": {
                        "prompt": {
                            "content": "response",
                            "label": "0/1",
                            "pred": "yes/no/n/a",
                            "reason": "reason/n/a",
                            "rouge": "rouge score",
                            "cos_sim": "cosine similarity score",
                            "gpt_eval": "yes/no"
                        },
                        ...
                    },
                    ...
                },
        '''
        self.gpt_client = OpenAI(api_key=kwargs['api_key'])
        self.temp = kwargs['temp']
        model = kwargs['model']
        dataset_path = kwargs['dataset_path']
        result_path = kwargs['result_path']
        result_full_path = os.path.join(result_path, model + ".json")
        results = {} if os.path.isfile(result_full_path) == False else json.loads(open(result_full_path, "r", encoding='utf-8').read())

        try:
            print("\nRunning experiment for {}".format(model))
            # Run all dirs (cwes)
            for dir in tqdm(os.listdir(os.path.join(dataset_path, 'dataset'))):
                # Check for dir name
                cwe = dir.lower()
                if cwe not in self.cwes:
                    continue
                
                print("\nRunning experiment for {}".format(cwe))
                if cwe not in results:
                    results[cwe] = {}

                # Run all files
                for file in os.listdir(os.path.join(dataset_path, 'dataset', dir)):
                    print("\nExperiment for {}".format(file))
                    if file.endswith(".c") or file.endswith(".py"):
                        label = 0 if file[0] == 'p' else 1

                        # Check if file exists
                        if file not in results[cwe]:
                            results[cwe][file] = {}
                        
                        # Get code
                        code = open(os.path.join(dataset_path, 'dataset', dir, file), "r", encoding='utf-8').read()

                        # Run all prompts
                        for prompt in self.prompts:
                            print("\n-> {}".format(prompt))
                            if prompt not in results[cwe][file]:
                                results[cwe][file][prompt] = {}
                            if "content" not in results[cwe][file][prompt]:
                                response = self.prompts[prompt](cwe=cwe, code=code)
                                if not response:
                                    open(result_full_path, "w").write(json.dumps(results, indent=4, sort_keys=True))
                                    return
                                results[cwe][file][prompt]["content"] = response
                                results[cwe][file][prompt]["label"] = label
                            print("Response done!!")

                            # Extract info
                            if "pred" not in results[cwe][file][prompt] or "reason" not in results[cwe][file][prompt]:
                                pred, reason = self.extract_info(cwe=cwe, text=results[cwe][file][prompt]["content"])
                                if pred == None or reason == None:
                                    open(result_full_path, "w").write(json.dumps(results, indent=4, sort_keys=True))
                                    return
                                results[cwe][file][prompt]["pred"] = pred
                                results[cwe][file][prompt]["reason"] = reason
                            print("Extraction done!!")

                            # Check if reason is n/a
                            if results[cwe][file][prompt]["reason"] == "n/a":
                                results[cwe][file][prompt]["rouge"] = None
                                results[cwe][file][prompt]["cos_sim"] = None
                                results[cwe][file][prompt]["gpt_eval"] = None

                            # Evaluate using ground truth
                            gt = open(os.path.join(dataset_path, 'ground-truth', cwe.upper(), file.split(".")[0] + ".txt"), "r", encoding='utf-8').read()

                            # 1) Compute rouge score
                            if "rouge" not in results[cwe][file][prompt]:
                                rouge_score = self.rouge(reason=results[cwe][file][prompt]["reason"], ground_truth=gt)
                                results[cwe][file][prompt]["rouge"] = rouge_score
                            print("Rouge done!!")

                            # 2) Compute cosine similarity
                            if "cos_sim" not in results[cwe][file][prompt]:
                                gt_emb = None
                                with open(os.path.join(dataset_path, 'embeddings', cwe.upper(), file.split(".")[0]), "rb") as f:
                                    gt_emb = pickle.load(f)
                                cos_sim = self.cos_similarity(reason=results[cwe][file][prompt]["reason"], ground_truth=gt_emb)
                                if cos_sim == None:
                                    open(result_full_path, "w").write(json.dumps(results, indent=4, sort_keys=True))
                                    return
                                results[cwe][file][prompt]["cos_sim"] = cos_sim
                            print("Cosine similarity done!!")

                            # 3) Compute gpt evaluation
                            if "gpt_eval" not in results[cwe][file][prompt]:
                                gpt_eval = self.gpt_eval(reason=results[cwe][file][prompt]["reason"], ground_truth=gt)
                                if not gpt_eval:
                                    open(result_full_path, "w").write(json.dumps(results, indent=4, sort_keys=True))
                                    return
                                results[cwe][file][prompt]["gpt_eval"] = gpt_eval
                            print("GPT evaluation done!!")
        finally:
            # Save results
            open(result_full_path, "w").write(json.dumps(results, indent=4, sort_keys=True))

    def run_trivial_robustness_experiments(self, **kwargs):
        '''
        This function runs the experiments to test robustness on the given model.

        ARGUMENTS:
        ----------
            api_key: openai api key (str)
            temp: recommended temperature for the given model (float)
            model: model name (str)
            prompt: prompt to use for the test (str)
            scenario: scenario to use for the test (str)
            dataset_path: path to the dataset (str)
            result_path: path to the result file (str)

        RETURNS:
        --------
            None

        ACTIONS:
        --------
            Runs the experiment on the given model and saves the results in the result file.
            {
                "scenario": {
                    "A1": {
                        "CWE-X": {
                            "file": {
                                "content": "response",
                                "pred": "yes/no/n/a",
                                "reason": "reason/n/a",
                                "rouge": "rouge score",
                                "cos_sim": "cosine similarity score",
                                "gpt_eval": "yes/no"
                            },
                            ...
                        },
                        ...
                    },
                    ...
                },
                ...
            }
        '''
        self.gpt_client = OpenAI(api_key=kwargs['api_key'])
        self.temp = kwargs['temp']
        model = kwargs['model']
        prompt = kwargs['prompt']
        scenario = kwargs['scenario']
        dataset_path = kwargs['dataset_path']
        result_path = kwargs['result_path']
        result_full_path = os.path.join(result_path, model + ".json")
        results = {} if os.path.isfile(result_full_path) == False else json.loads(open(result_full_path, "r", encoding='utf-8').read())

        try:
            # Scenarios
            if scenario not in results:
                results[scenario] = {}
            
            # Run all dirs (Augmentations)
            for A in os.listdir(dataset_path):
                # Check for dir name
                if A not in ["A1", "A2", "A3", "A4", "A5", "A6", "A7"]:
                    continue

                print("\nRunning experiment for {}".format(A))
                # Check if A exists
                if A not in results[scenario]:
                    results[scenario][A] = {}
                
                data_path = os.path.join(dataset_path, A, 'dataset')
                gt_path = os.path.join(dataset_path, A, 'ground_truth')
                emb_path = os.path.join(dataset_path, A, 'embeddings')

                for cwe in os.listdir(data_path):
                    cwe = cwe.lower()
                    # Check for dir name
                    if cwe not in self.cwes:
                        continue

                    print("\nRunning experiment for {}".format(cwe))
                    # Check if cwe exists
                    if cwe not in results[scenario][A]:
                        results[scenario][A][cwe] = {}

                    # Run all files
                    for file in os.listdir(os.path.join(data_path, cwe.upper())):
                        print("\nExperiment for {}".format(file))
                        if file.endswith(".c") or file.endswith(".py"):
                            # Put A0 in the beginning
                            if 'A0' not in results[scenario]:
                                results[scenario]['A0'] = {}
                            if cwe not in results[scenario]['A0']:
                                results[scenario]['A0'][cwe] = {}
                            if file not in results[scenario]['A0'][cwe]:
                                prompts_data = json.loads(open(os.path.join('results/prompts', model + '.json'), "r", encoding='utf-8').read())
                                results[scenario]['A0'][cwe][file] = prompts_data[cwe][file][prompt]

                            label = 0 if file[0] == 'p' else 1

                            # Check if file exists
                            if file not in results[scenario][A][cwe]:
                                results[scenario][A][cwe][file] = {}
                            
                            # Get code
                            code = open(os.path.join(data_path, cwe.upper(), file), "r", encoding='utf-8').read()

                            # Run experiment
                            if "content" not in results[scenario][A][cwe][file]:
                                response = self.prompts[prompt](cwe=cwe, code=code)
                                if not response:
                                    open(result_full_path, "w").write(json.dumps(results, indent=4, sort_keys=True))
                                    return
                                results[scenario][A][cwe][file]["content"] = response
                                results[scenario][A][cwe][file]["label"] = label
                            print("Response done!!")

                            # Extract info
                            if "pred" not in results[scenario][A][cwe][file] or "reason" not in results[scenario][A][cwe][file]:
                                pred, reason = self.extract_info(cwe=cwe, text=results[scenario][A][cwe][file]["content"])
                                if pred == None or reason == None:
                                    open(result_full_path, "w").write(json.dumps(results, indent=4, sort_keys=True))
                                    return
                                results[scenario][A][cwe][file]["pred"] = pred
                                results[scenario][A][cwe][file]["reason"] = reason
                            print("Extraction done!!")

                            # Check if reason is n/a
                            if results[scenario][A][cwe][file]["reason"] == "n/a":
                                results[scenario][A][cwe][file]["rouge"] = None
                                results[scenario][A][cwe][file]["cos_sim"] = None
                                results[scenario][A][cwe][file]["gpt_eval"] = None

                            # Evaluate using ground truth
                            gt = open(os.path.join(gt_path, cwe.upper(), file.split(".")[0] + ".txt"), "r").read()

                            # 1) Compute rouge score
                            if "rouge" not in results[scenario][A][cwe][file]:
                                rouge_score = self.rouge(reason=results[scenario][A][cwe][file]["reason"], ground_truth=gt)
                                results[scenario][A][cwe][file]["rouge"] = rouge_score
                            print("Rouge done!!")

                            # 2) Compute cosine similarity
                            if "cos_sim" not in results[scenario][A][cwe][file]:
                                gt_emb = None
                                with open(os.path.join(emb_path, cwe.upper(), file.split(".")[0]), "rb") as f:
                                    gt_emb = pickle.load(f)
                                cos_sim = self.cos_similarity(reason=results[scenario][A][cwe][file]["reason"], ground_truth=gt_emb)
                                if cos_sim == None:
                                    open(result_full_path, "w").write(json.dumps(results, indent=4, sort_keys=True))
                                    return
                                results[scenario][A][cwe][file]["cos_sim"] = cos_sim
                            print("Cosine similarity done!!")

                            # 3) Compute gpt evaluation
                            if "gpt_eval" not in results[scenario][A][cwe][file]:
                                gpt_eval = self.gpt_eval(reason=results[scenario][A][cwe][file]["reason"], ground_truth=gt)
                                if not gpt_eval:
                                    open(result_full_path, "w").write(json.dumps(results, indent=4, sort_keys=True))
                                    return
                                results[scenario][A][cwe][file]["gpt_eval"] = gpt_eval
                            print("GPT evaluation done!!")
        finally:
            # Save results
            open(result_full_path, "w").write(json.dumps(results, indent=4, sort_keys=True))

    def run_non_trivial_robustness_experiments(self, **kwargs):
        '''
        This function runs the experiments to test robustness on the given model on non-trivial augmentations.

        ARGUMENTS:
        ----------
            api_key: openai api key (str)
            temp: recommended temperature for the given model (float)
            model: model name (str)
            prompt: prompt to use for the test (str)
            scenario: scenario to use for the test (str)
            dataset_path: path to the dataset (str)
            result_path: path to the result file (str)

        RETURNS:
        --------
            None

        ACTIONS:
        --------
            Runs the experiment on the given model and saves the results in the result file.
            {
                "Scenario": {
                    "A1": {
                        "0": {
                            "CWE-X": {
                                "file": {
                                    "content": "response",
                                    "pred": "yes/no/n/a",
                                    "reason": "reason/n/a",
                                    "rouge": "rouge score",
                                    "cos_sim": "cosine similarity score",
                                    "gpt_eval": "yes/no"
                                },
                                ...
                            },
                            ...
                        },
                        "1": ...
                    },
                    ...
                },
                ...
            }
        '''
        self.gpt_client = OpenAI(api_key=kwargs['api_key'])
        self.temp = kwargs['temp']
        model = kwargs['model']
        prompt = kwargs['prompt']
        scenario = kwargs['scenario']
        dataset_path = kwargs['dataset_path']
        result_path = kwargs['result_path']
        result_full_path = os.path.join(result_path, model + ".json")
        results = {} if os.path.isfile(result_full_path) == False else json.loads(open(result_full_path, "r", encoding='utf-8').read())

        aug_test = {
            "A1": {
                "cwe-787": "cwe-787",
                "cwe-416": "cwe-416"
            },
            "A2": {
                "cwe-787": "cwe-787",
                "cwe-416": "cwe-416",
                "cwe-79": "cwe-79",
                "cwe-89": "cwe-89"
            },
            "A3": {
                "cwe-787": "cwe-787",
                "cwe-416": "cwe-416",
                "cwe-79": "cwe-79",
                "cwe-89": "cwe-89"
            },
            "A4": {
                "cwe-787": "cwe-787",
                "cwe-416": "cwe-787"
            },
            "A5": {
                "cwe-787": "cwe-787",
                "cwe-79": "cwe-79",
                "cwe-22": "cwe-22"
            },
            "A6": {
                "cwe-787": "cwe-787",
                "cwe-22": "cwe-787",
                "cwe-77": "cwe-77"
            }
        }

        try:
            # Scenarios
            if scenario not in results:
                results[scenario] = {}
            
            # Run all dirs (Augmentations)
            for A in os.listdir(dataset_path):
                # Check for dir name
                if A not in ["A1", "A2", "A3", "A4", "A5", "A6"]:
                    continue

                print("\nRunning experiment for {}".format(A))
                # Check if A exists
                if A not in results[scenario]:
                    results[scenario][A] = {"0": {}, "1": {}}

                # Run for before and after augmentation
                for t in ['0', '1']:
                    print("\nRunning experiment for {}".format(t))
                    data_path = os.path.join(dataset_path, A, A + '_' + t, 'dataset')
                    gt_path = os.path.join(dataset_path, A, A + '_' + t, 'ground-truth')
                    emb_path = os.path.join(dataset_path, A, A + '_' + t, 'embeddings')

                    # Run all dirs (cwes)
                    for cwe in os.listdir(data_path):
                        cwe = cwe.lower()
                        # Check for dir name
                        if cwe not in self.cwes:
                            continue

                        print("\nRunning experiment for {}".format(cwe))
                        # Check if cwe exists
                        if cwe not in results[scenario][A][t]:
                            results[scenario][A][t][cwe] = {}

                        # Run all files
                        for file in os.listdir(os.path.join(data_path, cwe.upper())):
                            print("\nExperiment for {}".format(file))
                            if file.endswith(".c") or file.endswith(".py"):
                                label = 0 if file[0] == 'p' else 1

                                # Check if file exists
                                if file not in results[scenario][A][t][cwe]:
                                    results[scenario][A][t][cwe][file] = {}
                                
                                # Get code
                                code = open(os.path.join(data_path, cwe.upper(), file), "r", encoding='utf-8').read()

                                # Run experiment
                                if "content" not in results[scenario][A][t][cwe][file]:
                                    response = self.prompts[prompt](cwe=aug_test[A][cwe], code=code)
                                    if not response:
                                        open(result_full_path, "w").write(json.dumps(results, indent=4, sort_keys=True))
                                        return
                                    results[scenario][A][t][cwe][file]["content"] = response
                                    results[scenario][A][t][cwe][file]["label"] = label
                                print("Response done!!")

                                # Extract info
                                if "pred" not in results[scenario][A][t][cwe][file] or "reason" not in results[scenario][A][t][cwe][file]:
                                    pred, reason = self.extract_info(cwe=cwe, text=results[scenario][A][t][cwe][file]["content"])
                                    if pred == None or reason == None:
                                        open(result_full_path, "w").write(json.dumps(results, indent=4, sort_keys=True))
                                        return
                                    results[scenario][A][t][cwe][file]["pred"] = pred
                                    results[scenario][A][t][cwe][file]["reason"] = reason
                                print("Extraction done!!")

                                # Check if reason is n/a
                                if results[scenario][A][t][cwe][file]["reason"] == "n/a":
                                    results[scenario][A][t][cwe][file]["rouge"] = None
                                    results[scenario][A][t][cwe][file]["cos_sim"] = None
                                    results[scenario][A][t][cwe][file]["gpt_eval"] = None

                                # Evaluate using ground truth
                                gt = open(os.path.join(gt_path, cwe.upper(), file.split(".")[0] + ".txt"), "r", encoding='utf-8').read()

                                # 1) Compute rouge score
                                if "rouge" not in results[scenario][A][t][cwe][file]:
                                    rouge_score = self.rouge(
                                        reason=results[scenario][A][t][cwe][file]["reason"], 
                                        ground_truth=gt
                                    )
                                    results[scenario][A][t][cwe][file]["rouge"] = rouge_score
                                print("Rouge done!!")

                                # 2) Compute cosine similarity
                                if "cos_sim" not in results[scenario][A][t][cwe][file]:
                                    gt_emb = None
                                    with open(os.path.join(emb_path, cwe.upper(), file.split(".")[0]), "rb") as f:
                                        gt_emb = pickle.load(f)
                                    cos_sim = self.cos_similarity(
                                        reason=results[scenario][A][t][cwe][file]["reason"], 
                                        ground_truth=gt_emb
                                    )
                                    if cos_sim == None:
                                        open(result_full_path, "w").write(json.dumps(results, indent=4, sort_keys=True))
                                        return
                                    results[scenario][A][t][cwe][file]["cos_sim"] = cos_sim
                                print("Cosine similarity done!!")

                                # 3) Compute gpt evaluation
                                if "gpt_eval" not in results[scenario][A][t][cwe][file]:
                                    gpt_eval = self.gpt_eval(
                                        reason=results[scenario][A][t][cwe][file]["reason"], 
                                        ground_truth=gt
                                    )
                                    if not gpt_eval:
                                        open(result_full_path, "w").write(json.dumps(results, indent=4, sort_keys=True))
                                        return
                                    results[scenario][A][t][cwe][file]["gpt_eval"] = gpt_eval
                                print("GPT evaluation done!!")
        finally:
            # Save results
            open(result_full_path, "w").write(json.dumps(results, indent=4, sort_keys=True))

    def run_real_world_experiments(self, **kwargs):
        '''
        This function runs experiments on the given model using real world code.

        ARGUMENTS:
        ----------
            api_key: openai api key (str)
            temp: recommended temperature for the given model (float)
            model: model name (str)
            prompt: prompt to use for the test (str)
            scenario: scenario to use for the test (str)
            dataset_path: path to the dataset (str)
            result_path: path to the result file (str)

        RETURNS:
        --------
            None

        ACTIONS:
        --------
            Runs the experiment on the given model and saves the results in the result file.
            {
                "project": {
                    "cve": {
                        "file": {
                            "scenario": {
                                "content": "response",
                                "pred": "yes/no/n/a",
                                "reason": "reason/n/a",
                                "rouge": "rouge score",
                                "cos_sim": "cosine similarity score",
                                "gpt_eval": "yes/no"
                            },
                            ...
                        },
                        ...
                    },
                    ...
                },
                ...
            }
        '''
        self.gpt_client = OpenAI(api_key=kwargs['api_key'])
        self.temp = kwargs['temp']
        model = kwargs['model']
        prompt = kwargs['prompt']
        scenario = kwargs['scenario']
        dataset_path = kwargs['dataset_path']
        result_path = kwargs['result_path']
        result_full_path = os.path.join(result_path, model + ".json")
        results = {} if os.path.isfile(result_full_path) == False else json.loads(open(result_full_path, "r", encoding='utf-8').read())

        cve_details = json.loads(open(os.path.join(dataset_path, 'cve_details.json'), "r", encoding='utf-8').read())

        try:
            print("\nRunning experiment for {}".format(scenario))
            # Check if model exists
            print("\nRunning experiment for {}".format(model))

            # Run for all projects
            for project in os.listdir(dataset_path):
                if project == 'cve_details.json' or project == 'README.md':
                    continue
                print("\nRunning experiment for {}".format(project))
                # Check if project exists
                if project not in results:
                    results[project] = {}
                
                project_path = os.path.join(dataset_path, project)
                # Run for all CVEs
                for cve in os.listdir(project_path):
                    print("\nExperiment for {}".format(cve))
                    # Check if cve exists
                    if cve not in results[project]:
                        results[project][cve] = {}
                    
                    cve_path = os.path.join(project_path, cve)
                    # Run for both 'vuln' and 'patch' files
                    for file in ['vuln', 'patch']:
                        print("\nExperiment for {}".format(file))
                        # Check if file exists
                        if file not in results[project][cve]:
                            results[project][cve][file] = {}

                        # Check if scenario exists
                        if scenario not in results[project][cve][file]:
                            results[project][cve][file][scenario] = {}
                        
                        file_path = os.path.join(cve_path, file + '.c')
                        gt_path = os.path.join(cve_path, file + '.txt')
                        emb_path = os.path.join(cve_path, file)

                        # Get code
                        code = open(file_path, "r", encoding='utf-8').read()

                        # Run experiment
                        if "content" not in results[project][cve][file][scenario]:
                            response = self.prompts[prompt](cwe=cve_details[project.lower()][cve]["cwe"], code=code)
                            if not response:
                                open(result_full_path, "w").write(json.dumps(results, indent=4, sort_keys=True))
                                return
                            results[project][cve][file][scenario]["content"] = response
                        print("Response done!!")

                        # Extract info
                        if "pred" not in results[project][cve][file][scenario] or "reason" not in results[project][cve][file][scenario]:
                            pred, reason = self.extract_info(cwe=cve_details[project.lower()][cve]["cwe"], text=results[project][cve][file][scenario]["content"])
                            if pred == None or reason == None:
                                open(result_full_path, "w").write(json.dumps(results, indent=4, sort_keys=True))
                                return
                            results[project][cve][file][scenario]["pred"] = pred
                            results[project][cve][file][scenario]["reason"] = reason
                        print("Extraction done!!")

                        # Check if reason is n/a
                        if results[project][cve][file][scenario]["reason"] == "n/a":
                            results[project][cve][file][scenario]["rouge"] = None
                            results[project][cve][file][scenario]["cos_sim"] = None
                            results[project][cve][file][scenario]["gpt_eval"] = None

                        # Evaluate using ground truth
                        gt = open(gt_path, "r", encoding='utf-8').read()

                        # 1) Compute rouge score
                        if "rouge" not in results[project][cve][file][scenario]:
                            rouge_score = self.rouge(
                                reason=results[project][cve][file][scenario]["reason"], 
                                ground_truth=gt
                            )
                            results[project][cve][file][scenario]["rouge"] = rouge_score
                        print("Rouge done!!")

                        # 2) Compute cosine similarity
                        if "cos_sim" not in results[project][cve][file][scenario]:
                            gt_emb = None
                            with open(emb_path, "rb") as f:
                                gt_emb = pickle.load(f)
                            cos_sim = self.cos_similarity(
                                reason=results[project][cve][file][scenario]["reason"], 
                                ground_truth=gt_emb
                            )
                            if cos_sim == None:
                                open(result_full_path, "w").write(json.dumps(results, indent=4, sort_keys=True))
                                return
                            results[project][cve][file][scenario]["cos_sim"] = cos_sim
                        print("Cosine similarity done!!")

                        # 3) Compute gpt evaluation
                        if "gpt_eval" not in results[project][cve][file][scenario]:
                            gpt_eval = self.gpt_eval(
                                reason=results[project][cve][file][scenario]["reason"], 
                                ground_truth=gt
                            )
                            if not gpt_eval:
                                open(result_full_path, "w").write(json.dumps(results, indent=4, sort_keys=True))
                                return
                            results[project][cve][file][scenario]["gpt_eval"] = gpt_eval
                        print("GPT evaluation done!!")
        finally:
            # Save results
            open(result_full_path, "w").write(json.dumps(results, indent=4, sort_keys=True))

    def run_all(self, **kwargs):
        '''
        This function runs all the experiments on the given model.

        ARGUMENTS:
        ----------
            api_key: openai api key (str)
            model: model name (str)

        RETURNS:
        --------
            None
        '''
        api_key = kwargs['api_key']
        model = kwargs['model']
        dataset_path = 'datasets'

        # make `results` directory
        result_path = 'results'
        os.system('mkdir ' + result_path)

        ### Deterministic Responses Experiment!!
        print("\n#######################################")
        print("Deterministic Responses Experiment!!")
        print("#######################################\n")

        # Create directory to store results
        det_res_result_path = os.path.join(result_path, 'determinism')
        os.system('mkdir ' + det_res_result_path)
        # Files selection for the experiment
        cwe_files = [("cwe-787", "2.c"), ("cwe-787", "p_2.c"), ("cwe-89", "2.py"), ("cwe-89", "p_2.py")]
        # Run on selected prompts
        for prompt in ['promptS1', 'promptS2', 'promptS3', 'promptS4', 'promptS5', 'promptS6']:
            # Run on specific temperatures
            for temp in [0.2, 0.0]:
                self.run_temp_test(
                    api_key=api_key,
                    temp=temp,
                    model=model,
                    k=10,
                    do_reason=True,
                    do_extract=True,
                    cwe_files=cwe_files,
                    prompt=prompt,
                    dataset_path=os.path.join(dataset_path, 'hand-crafted'),
                    result_path=det_res_result_path
                )
        print("\n#######################################")
        print("Deterministic Responses Experiment done!!")
        print("#######################################\n")
        
        ### Range of Parameters Experiment!!
        print("\n#######################################")
        print("Range of Parameters Experiment!!")
        print("#######################################\n")

        # Create directory to store results
        range_param_result_path = os.path.join(result_path, 'range-params')
        os.system('mkdir ' + range_param_result_path)
        # Files, prompt, and temperature range selection for the experiment
        cwe_files = [("cwe-787", "3.c"), ("cwe-787", "p_3.c"), ("cwe-89", "3.py"), ("cwe-89", "p_3.py")]
        prompt = 'promptS4'
        temps = [0.2, 0.0, 0.25, 0.5, 0.75, 1.0]
        for temp in temps:
            self.run_temp_test(
                api_key=api_key,
                temp=temp,
                model=model,
                k=10,
                do_reason=True,
                do_extract=True,
                cwe_files=cwe_files,
                prompt=prompt,
                dataset_path=os.path.join(dataset_path, 'hand-crafted'),
                result_path=range_param_result_path
            )
        print("\n#######################################")
        print("Range of Parameters Experiment done!!")
        print("#######################################\n")

        ### Prompts Experiment!!
        print("\n#######################################")
        print("Prompts Experiment!!")
        print("#######################################\n")

        # Create directory to store results
        prompts_result_path = os.path.join(result_path, 'prompts')
        os.system('mkdir ' + prompts_result_path)
        # Run on all prompts
        self.run_prompts_experiments(
            api_key=api_key,
            temp=0.0,
            model=model,
            dataset_path=os.path.join(dataset_path, 'hand-crafted'),
            result_path=prompts_result_path
        )
        print("\n#######################################")
        print("Prompts Experiment done!!")
        print("#######################################\n")

        # Calculate Best Prompts
        best_prompts_path = os.path.join(result_path, 'best_prompts.json')
        if not os.path.isfile(best_prompts_path):
            best_prompts_loaded = {}
        else:
            best_prompts_loaded = json.loads(open(best_prompts_path, "r", encoding='utf-8').read())
        best_prompts_loaded[model] = self.find_best_prompts(result_path=prompts_result_path, model=model)
        open(os.path.join(result_path, 'best_prompts.json'), "w").write(json.dumps(best_prompts_loaded, indent=4, sort_keys=True))

        ### Robustness Experiment!!
        print("\n#######################################")
        print("Robustness Experiments!!")
        print("#######################################\n")

        # Create directory to store results
        robustness_result_path = os.path.join(result_path, 'robustness')
        os.system('mkdir ' + robustness_result_path)

        print("\n#######################################")
        print("1) Trivial Cases!!")
        print("#######################################\n")

        # Create directory to store results
        trivial_result_path = os.path.join(robustness_result_path, 'trivial')
        os.system('mkdir ' + trivial_result_path)

        # # Get Best Prompts
        best_fs_prompt = best_prompts_loaded[model]['FS']
        best_zs_prompt = best_prompts_loaded[model]['ZS']
        prompts = [('promptS1', 'S'), (best_zs_prompt, 'ZS'), (best_fs_prompt, 'FS')]

        for p, s in prompts:
            self.run_trivial_robustness_experiments(
                api_key=api_key,
                temp=0.0,
                model=model,
                prompt=p,
                scenario=s,
                dataset_path=os.path.join(dataset_path, 'augmented', 'trivial'),
                result_path=trivial_result_path
            )
        print("\n#######################################")
        print("Trivial Cases done!!")
        print("#######################################\n")

        print("\n#######################################")
        print("Non-Trivial Cases!!")
        print("#######################################\n")

        # Create directory to store results
        non_trivial_result_path = os.path.join(robustness_result_path, 'non-trivial')
        os.system('mkdir ' + non_trivial_result_path)

        for p, s in prompts:
            self.run_non_trivial_robustness_experiments(
                api_key=api_key,
                temp=0.0,
                model=model,
                prompt=p,
                scenario=s,
                dataset_path=os.path.join(dataset_path, 'augmented', 'non-trivial'),
                result_path=non_trivial_result_path
            )
        print("\n#######################################")
        print("Non-Trivial Cases done!!")
        print("#######################################\n")

        ### Real World Experiment!!
        print("\n#######################################")
        print("Real World Experiment!!")
        print("#######################################\n")

        # Create directory to store results
        real_world_result_path = os.path.join(result_path, 'real-world')
        os.system('mkdir ' + real_world_result_path)

        # Run on real world dataset
        scenarios = ['ZT', 'ZR', 'FT', 'FR']
        for sce in scenarios:
            self.run_real_world_experiments(
                api_key=api_key,
                temp=0.0,
                model=model,
                prompt=best_prompts_loaded[model][sce],
                scenario=sce,
                dataset_path=os.path.join(dataset_path, 'real-world'),
                result_path=real_world_result_path
            )
        print("\n#######################################")
        print("Real World Experiment done!!")
        print("#######################################\n")