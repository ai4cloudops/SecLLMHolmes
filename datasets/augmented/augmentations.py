import random
import string
import re

class TrivialAugmentations4C:
    def __init__(self):
        self.aug = {
            'a1': self.a1,
            'a2': self.a2,
            'a3': self.a3,
            'a4': self.a4,
            'a5': self.a5,
            'a6': self.a6,
            'a7': self.a7
        }

    # Rename function parameters randomly
    def a1(self, **kwargs):
        code = kwargs['code']
        def rename_parameter(code, old_parameter_name):
            letters = string.ascii_lowercase
            new_parameter_name = ''.join(random.choice(letters) for i in range(2))
            
            parameter = old_parameter_name.replace("*", "")
            parameter = parameter.replace("[", "")
            
            if parameter not in ["...", "private"]:
            
                neutral_characters = ["(", ")", ",", ";", " ", "*", "[", "]", "-", ">", "&", ":"]
                
                occurences = [m.start() for m in re.finditer(parameter, code)]
                num_inserted_chars = 0
                
                for occurence in occurences:
                    
                    occurence += num_inserted_chars
                    
                    if occurence + len(parameter) < len(code): 
                    
                        prev_char = code[occurence - 1]
                        next_char = code[occurence + len(parameter)]
                        
                        if (prev_char in neutral_characters and next_char in neutral_characters):
                            code = code[0:occurence] + new_parameter_name + code[occurence + len(parameter):]
                            num_inserted_chars += len(new_parameter_name) - len(parameter)
            return code

        if "(" in code and ")" in code:
            parameters = code.split(")")[0].split("(")[1]
            
            if len(parameters) > 0:
                if "," in parameters:
                    for param in parameters.split(","):
                        parameter = param.split(" ")[-1]
                        code = rename_parameter(code, parameter)
                else:
                    parameter = parameters.split(" ")[-1]
                    code = rename_parameter(code, parameter)        
        return code

    # Rename function randomly
    def a2(self, **kwargs):
        code = kwargs['code']
        letters = string.ascii_lowercase
        new_function_name = ''.join(random.choice(letters) for i in range(2))
        
        if "(" in code and ")" in code:
            before_function = code.split("(")[0]
            
            if " " in before_function:
                function_name = before_function.split(" ")[-1]
                
                if function_name != "" and function_name != " ":
                
                    code = code.replace(function_name, new_function_name)    
        return code

    # Add random unreachable code
    def a3(self, **kwargs):
        code = kwargs['code']
        text_to_insert = 'void helpfunc() {\n    while (1) {'
        
        for _ in range(20):
            text_to_insert += "\n\t\tbreak;"
                
        text_to_insert += '\n    }\n}\n'

        code = code + "\n\n" + text_to_insert
        return code
    
    # Add random comments
    def a4(self, **kwargs):
        code = kwargs['code']
        comment = '/* void helpfunc() {\n    while (1) {'
        
        for _ in range(20):
            comment += "\n\t\tbreak;"
                
        comment += '\n    }\n}\n*/'
        code = comment + '\n\n' + code
        return code

    # Add random whitespace
    def a5(self, **kwargs):
        code = kwargs['code']
        code_lines = code.split('\n')
        pos_to_insert = random.randint(0, len(code_lines))

        text_to_insert = [' ' * 20]
        code = code_lines[0:pos_to_insert] + text_to_insert + code_lines[pos_to_insert:]
        code = '\n'.join(code)
        return code

    # Add a useless function
    def a6(self, **kwargs):
        code = kwargs['code']
        begin_of_function = code.index('{')
        text_to_insert = '\n    help_func();'
        code = code[0:begin_of_function + 1] + text_to_insert + code[begin_of_function + 1:]
        func_to_insert = 'void helpfunc() {\n    while (1) {'
        for i in range(20):
            func_to_insert += "\n\t\tbreak;"
        func_to_insert += '\n    }\n    return;\n}\n'
        code = code + "\n\n" + func_to_insert
        return code

    # Add '\n' character
    def a7(self, **kwargs):
        code = kwargs['code']
        code = re.sub('\n','\n\n',code)
        return code

class TrivialAugmentations4Py:
    def __init__(self):
        self.aug = {
            'a1': self.a1,
            'a2': self.a2,
            'a3': self.a3,
            'a4': self.a4,
            'a5': self.a5,
            'a6': self.a6,
            'a7': self.a7
        }

        # Rename function parameters randomly
    def a1(self, **kwargs):
        code = kwargs['code']
        def random_word(size=2):
            return ''.join(random.choice(string.ascii_lowercase) for _ in range(size))

        def functions_with_arguments(code):
            pattern = re.compile(r'def (\w+)\((\w+[^)]*)\):')
            matches = pattern.findall(code)
            return [match[0] for match in matches]

        def change_args_names_in_function(code, target_function):
            func_pattern = re.compile(r'def ' + target_function + r'\(([^)]+)\):')
            match = func_pattern.search(code)

            if not match:
                return code

            args_str = match.group(1)
            args = [arg.strip() for arg in args_str.split(',')]
            replace_map = {}

            # Generate random two-letter words for each argument
            for arg in args:
                new_name = random_word()
                while new_name in code:  # Ensure uniqueness
                    new_name = random_word()
                replace_map[arg] = new_name

            # Replace the arguments in the function definition
            for old_name, new_name in replace_map.items():
                args_str = args_str.replace(old_name, new_name)

            # Update the function definition in the code
            code = code[:match.start(1)] + args_str + code[match.end(1):]

            # Replace the usage of the arguments in the function body
            function_body_start = match.end()
            function_body_end = code.find("def ", function_body_start)  # Find the next "def" keyword
            function_body_end = function_body_end if function_body_end != -1 else len(code)

            function_body = code[function_body_start:function_body_end]

            for old_name, new_name in replace_map.items():
                function_body = re.sub(r'\b' + old_name + r'\b', new_name, function_body)  # Using \b to ensure whole word match

            return code[:function_body_start] + function_body + code[function_body_end:]

        funcs = functions_with_arguments(code)
        for func in funcs:
            code = change_args_names_in_function(code, func)
        return code

    # Rename function randomly
    def a2(self, **kwargs):
        code = kwargs['code']
        def random_string(length=4):
            letters = string.ascii_lowercase
            return ''.join(random.choice(letters) for i in range(length))
        
        # Pattern to match function definitions
        pattern_def = r"\bdef\s+(\w+)\("
        # Find all function names
        matches = re.findall(pattern_def, code)

        # Create a mapping of original function name to random name
        name_mapping = {name: random_string() for name in matches}

        # Replace function definitions
        for original, new in name_mapping.items():
            pattern = r"\bdef\s+" + original + r"\("
            code = re.sub(pattern, f"def {new}(", code)

        # Replace function calls
        for original, new in name_mapping.items():
            # This will replace all function calls that have word boundaries
            # before and after the function name
            pattern = r"\b" + original + r"\("
            code = re.sub(pattern, f"{new}(", code)

        return code

    # Add random unreachable code
    def a3(self, **kwargs):
        code = kwargs['code']
        text_to_insert = 'def helpfunc():\n    while 0:'
        
        for i in range(20):
            text_to_insert += "\n\tbreak"
        text_to_insert += '\n'

        code = code + "\n\n" + text_to_insert
        return code
    
    # Add random comments
    def a4(self, **kwargs):
        code = kwargs['code']
        comment = '# def helpfunc():\n#     while 0:'
        
        for _ in range(20):
            comment += "\n# \tbreak"
                
        comment += '\n'
        code = comment + "\n\n" + code
        return code

    # Add random whitespace
    def a5(self, **kwargs):
        code = kwargs['code']
        code_lines = code.splitlines()
        pos_to_insert = random.randint(0, len(code_lines) - 1)

        code_lines[pos_to_insert] = code_lines[pos_to_insert] + ' ' * 20
        code = '\n'.join(code_lines)
        return code

    # Add a useless function
    def a6(self, **kwargs):
        code = kwargs['code']
        begin_of_function = code[code.index('def'):].index(':') + code.index('def')
        text_to_insert = '\n    help_func()'
        code = code[0:begin_of_function + 1] + text_to_insert + code[begin_of_function + 1:]
        func_to_insert = 'def helpfunc():\n    while 0:'
        for _ in range(20):
            func_to_insert += "\n\tbreak"
        func_to_insert += '\n    return'
        code = code + "\n\n" + func_to_insert
        return code

    # Remove '\n' and '\t' characters
    def a7(self, **kwargs):
        code = kwargs['code']
        code = re.sub('\n','\n\n',code)
        return code

class NonTrivialAugmentations:
    def __init__(self):
        pass

    # Change a variable name to ‘buffer’
    def a1(self, **kwargs):
        pass

    # Change the name of a safe function to ‘vulnerable’ function
    def a2(self, **kwargs):
        pass
    
    # Change the name of an unsafe function to ‘non_vulnerable’ function
    def a3(self, **kwargs):
        pass

    # Add a function that uses ‘strcpy’ in a safe way
    def a4(self, **kwargs):
        pass

    # Add ‘realpath’ function to a program with path traversal vulnerability
    def a5(self, **kwargs):
        pass

    # Add a hash-define ‘strcpy’ function
    def a6(self, **kwargs):
        pass

    # Add a map-define vulnerable function
    def a7(self, **kwargs):
        pass
