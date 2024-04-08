from adapter import LLMAdapter
from google.cloud import aiplatform
from vertexai.preview.language_models import CodeChatModel, ChatModel, InputOutputTextPair

class VertexAICodeChatAdapter(LLMAdapter):  
    def __init__(self, temp=0.0):
        super().__init__()
        self.temp = temp

    def prepare_prompt(self, **kwargs):
        if kwargs['prompt'] == 'Question':
            prompt = "Code:\n" + kwargs['code'] + "\nQuestion: " + kwargs['question'] + "\nAnswer: "
        if kwargs['prompt'] == 'Analysis':
            prompt = "Code:\n" + kwargs['code'] + "\nAnalysis: "
        if kwargs['prompt'] == 'Q/A':
            prompt = "Code:\n" + kwargs['code'] + "\nQuestion: " + kwargs['question'] + "\nAnswer: " + kwargs['answer']
        if kwargs['prompt'] == 'Def':
            prompt = kwargs['defin'] + "\n\nCode:\n" + kwargs['code'] + "\nQuestion: " + kwargs['question'] + "\nAnswer: "
        if kwargs['prompt'] == 'None':
            prompt = "Code:\n" + kwargs['code'] + "\n"
        return prompt

    def prepare(self, **kwargs):
        aiplatform.init(project=kwargs['project_id'], location=kwargs['location'])

    # Step-by-Step Prompt 3 (ZS)
    def promptR3(self, **kwargs):
        cwe = kwargs['cwe']
        cwe_name = self.cwes[cwe]
        code = kwargs['code']

        # system
        sys = ""

        # example
        exp = []

        # overview
        prompt = "Code:\n" + code + "\n\nTask: Provide a brief overview of the code.\nOverview: "
        overview_response = self.chat(system=sys, examples=exp, text=prompt)

        # sub-components
        prompt += overview_response + "\n\nTask: Based on the overview identify the sub-components in code that could lead to a security vulnerability knows as {}.\nSub-components: ".format(cwe_name)
        sub_response = self.chat(system=sys, examples=exp, text=prompt)

        # detailed analysis
        prompt += sub_response + "\n\nTask: Perform a detailed analysis of the identified sub-components for the existence of the {}.\nDetailed Analysis: ".format(cwe_name + " vulnerability")
        analysis_response = self.chat(system=sys, examples=exp, text=prompt)

        # answer
        prompt += analysis_response + "\n\nTask: Based on the detailed analysis decide and answer whether the {} is present in the given code or not.\nAnswer: ".format(cwe_name + " vulnerability")
        ans_response = self.chat(system=sys, examples=exp, text=prompt)

        # response
        response = "Overview:\n" + overview_response + "\n\nSub-cmponents:\n" + sub_response + "\n\nDetailed Analysis:\n" + analysis_response + "\n\nAnswer:\n" + ans_response
        return response
    
    def chat(self, **kwargs):
        text = kwargs['text']
        parameters = {
            "temperature": self.temp,
            "max_output_tokens": 1024
        }
        code_chat_model = CodeChatModel.from_pretrained("codechat-bison@001")
          
        chat = code_chat_model.start_chat()
        message = ""
        if 'system' in kwargs and kwargs['system'] != "":
            message += "Context: " + kwargs['system'] + "\n\n"
       
        if 'examples' in kwargs and len(kwargs['examples']) > 0: 
            message += "Examples:\n"
            cnt = 1
            for ex in kwargs['examples']:
                message += "Example " + str(cnt) + ":\n"
                message += ex[0]
                message += ex[1] + "\n\n"
                cnt += 1
        message += text

        try:
            response = chat.send_message(
                message, **parameters
            )
            return response.text
        except:
            return None

class VertexAIChatAdapter(LLMAdapter):
    def __init__(self, temp=0.0):
        super().__init__()
        self.temp = temp
        
    def prepare_prompt(self, **kwargs):
        if kwargs['prompt'] == 'Question':
            prompt = "Code:\n" + kwargs['code'] + "\nQuestion: " + kwargs['question'] + "\nAnswer: "
        if kwargs['prompt'] == 'Analysis':
            prompt = "Code:\n" + kwargs['code'] + "\nAnalysis: "
        if kwargs['prompt'] == 'Q/A':
            prompt = "Code:\n" + kwargs['code'] + "\nQuestion: " + kwargs['question'] + "\nAnswer: " + kwargs['answer']
        if kwargs['prompt'] == 'Def':
            prompt = kwargs['defin'] + "\n\nCode:\n" + kwargs['code'] + "\nQuestion: " + kwargs['question'] + "\nAnswer: "
        if kwargs['prompt'] == 'None':
            prompt = "Code:\n" + kwargs['code'] + "\n"
        return prompt

    def prepare(self, **kwargs):
        aiplatform.init(project=kwargs['project_id'], location=kwargs['location'])

    def chat(self, **kwargs):
        text = kwargs['text']
        parameters = {
            "temperature": self.temp,
            "max_output_tokens": 1024
        }
        code_chat_model = ChatModel.from_pretrained("chat-bison@001")
      
        system = None
        if 'system' in kwargs and kwargs['system'] != "":
            system = kwargs['system']
        
        examples = None
        if 'examples' in kwargs and len(kwargs['examples']) > 0: 
            examples = []
            for ex in kwargs['examples']:
                examples.append(InputOutputTextPair(ex[0], ex[1]))
                
        chat = code_chat_model.start_chat(context=system, examples=examples)    
        try:
            response = chat.send_message(
                text, **parameters
            )
            return response.text
        except:
            return None 
