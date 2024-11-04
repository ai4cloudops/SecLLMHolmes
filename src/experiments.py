import os
import json
import pickle
from tqdm import tqdm
from openai import OpenAI

class ExperimentRunner:
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
                                prompts_path = os.path.join(os.path.join(os.path.dirname(__file__)), "..", "results", "prompts", model + ".json")
                                prompts_data = json.loads(open(prompts_path, "r", encoding='utf-8').read())
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
        dataset_path = os.path.join(os.path.dirname(__file__), '..', 'datasets')

        # make `results` directory
        result_path = os.path.join(os.path.dirname(__file__), '..', 'results')
        os.makedirs(result_path, exist_ok=True)

        ### Deterministic Responses Experiment!!
        print("\n#######################################")
        print("Deterministic Responses Experiment!!")
        print("#######################################\n")

        # Create directory to store results
        det_res_result_path = os.path.join(result_path, 'determinism')
        os.makedirs(det_res_result_path, exist_ok=True)
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
        os.makedirs(range_param_result_path, exist_ok=True)
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
        os.makedirs(prompts_result_path, exist_ok=True)
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
        os.makedirs(robustness_result_path, exist_ok=True)

        print("\n#######################################")
        print("1) Trivial Cases!!")
        print("#######################################\n")

        # Create directory to store results
        trivial_result_path = os.path.join(robustness_result_path, 'trivial')
        os.makedirs(trivial_result_path, exist_ok=True)

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
        os.makedirs(non_trivial_result_path, exist_ok=True)

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
        os.makedirs(real_world_result_path, exist_ok=True)

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
