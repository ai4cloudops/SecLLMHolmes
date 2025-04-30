<div align="center">
  <p>
    <h1>SecLLMHolmes 🔍</h1>
    <img src="https://github.com/user-attachments/assets/de8ef359-3475-4882-bd1e-d245aa6f081b" width="200" height="200" />
  </p>
</div>

<div align="center">
  <a href="https://arxiv.org/abs/2312.12575">
    <b><em>Paper 🔗</em></b>
  </a>
  <br></br>
  <p>
    <b><em>🎉 IEEE Symposium on Security and Privacy 2024!</em></b>
  </p>
</div>
<hr>

## 🛠️ Updates (Latest - Nov 6, 2024)
> 🚨 See [UPDATES.md](https://github.com/saadullah01/SecLLMHolmes/blob/main/UPDATES.md) for details

<hr>

SecLLMHolmes is a generalized, fully automated, and scalable framework to systematically evaluate the performance (i.e., ***accuracy*** and ***reasoning*** capabilities) of LLMs for vulnerability detection.

## ⚙️ Features
1. Assessing identification and reasoning in vulnerability detection
2. Fully-automated evaluation
3. Scalable to any ***chat-based LLM***
4. Comprehensive testing over 8-distinct and critical dimensions for vulnerability detection
5. Evaluation over C/C++ and Python programming languages
6. Assessment over code scenarios with three complexity levels
7. Tests for eight most dangerous classes of vulnerabilities (CWEs)
8. Robustness testing over range of minor to major code augmentations
9. Assessment over a diverse set of 17 prompts

## 🔬 Build an `adapter` to evaluate YOUR LLM from scratch
To evaluate your LLM using our framework, you need to create an adapter. You can do this by simply modifying the ([src/adapter.py](https://github.com/saadullah01/SecLLMHolmes/blob/main/src/adapter.py)) and implementing the following three functions in it:

1. `prepare_prompt`: define best prompting practices and rules specific to your LLM
2. `prepare`: define, prepare, or load your model
3. `chat`: define message structure and chat inference method

> **Note:** For more details, please refer to our paper (Section 3.1) and see [examples of adapters](https://github.com/saadullah01/SecLLMHolmes/tree/main/adapter-examples) for LLMs included in our study.

* **Get OpenAI API-KEY:** As our evaluation framework uses OpenAI's GPT-4o API, you need to provide your own API-KEY. ([OpenAI's official documentation](https://platform.openai.com/docs/quickstart/step-2-set-up-your-api-key))

* **Add Model's Name:** This model name will be used to store the evaluation results for your LLM

## 🏃🏽‍♂️‍➡️ How to Run
After you have created your adapter, please go ahead and follow these steps to run your evaluation:

1. Create python environment
```
python3 -m venv env
source env/bin/activate
```
2. Install the required packages
```
pip install -r requirements.txt
```
> **Note:** For need to manually install all packages that are required to run your LLM
3. Run your adapter, and it will create a `results` directory and store all results in it
```
cd src
python adapter.py
```
