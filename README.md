## Dev setup

1. Create a venv at .venv (it is git-ignored):
    ```bash
    python -m venv .venv
    ```

   (If you're using PyCharm, you'll want to set it as the Python interpreter and mark the directory as excluded so it doesn't show up in search results.)

2. Activate it:
    ```bash
    source .venv/Scripts/activate
    ```

3. Pick an LLM provider to use from [here](https://langchain-ai.github.io/langgraph/tutorials/get-started/1-build-basic-chatbot/#3-add-a-node) (Google/Gemini is free).
4. Ensure its LangGraph plugin exists in `requirements.txt` (you may commit this).
5. Create an API key with the provider. Then create `./core.py` and copy the LLM initialization code (from the previous link) into it. Looks like this:
   ```python
   import os
   from langchain.chat_models import init_chat_model
   
   os.environ["GOOGLE_API_KEY"] = "<your API key>"
   
   llm = init_chat_model("google_genai:gemini-2.0-flash")
   ```

6. Download dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Running

1. Activate the venv:
    ```bash
    source .venv/Scripts/activate
    ```
   
2. Run it:
   ```bash
   python main.py
   ```

## Resources
- [LangGraph basics tutorials](https://langchain-ai.github.io/langgraph/tutorials/get-started/1-build-basic-chatbot/#2-create-a-stategraph)
- [Discussion with ChatGPT about the graph design for this game](https://chatgpt.com/share/6838fafe-f994-8010-aa8c-7abb1f64cdab)
