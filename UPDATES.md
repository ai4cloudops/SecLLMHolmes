# Nov 6, 2024
1. Restructed the code for the SecLLMHolmes framework to allow maximum compatibility with other projects
2. Replaced GPT-4 with GPT-4o for both extracting information from LLM's responses and evaluating reasonings
3. Added structured pydantic model based output for extracting reason and prediction using GPT-4o's 'structured output' API
4. An issue was found in CWE-22 'p_2' and 'p_3' code examples, where the patch was still vulnerable. We have updated these code examples, their ground truths, and embeddings, everywhere in our dataset
5. README is also updated
6. UPDATES document added to keep track of all the changes made in the project after publication

# July 24, 2024
1. There was a bug found in one of the evaluation scripts that generated Tables for Section 4.8 'Real-World Cases' in our paper. Due to this bug, there were some points changed in Tables 16, 17, and 27
2. The bug was fixed, all tables were updated, and new version of the paper was uploaded

# May 23, 2024
1. OpenAI deprecated their `text-similarity-davinci-001` embeddings model, and we updated our pipeline with the latest most capable embeddings model `text-embedding-3-large`
2. Using the new embedding model, we updated embeddings of all examples in our dataset