from __future__ import annotations
from ast import Dict
from ctypes import Union

import logging

from dataclasses import dataclass
import sys
import threading
import time
from typing import Any, List, Optional

from gpt_engineer.core.ai import AI, Message
from gpt_engineer.core.chat_to_files import (
    format_file_to_input,
    get_code_strings,
    overwrite_files_with_edits,
    to_files_and_memory,
)
from gpt_engineer.core.db import DBs
from gpt_engineer.core.steps import (
    STEPS,
    setup_sys_prompt,
    setup_sys_prompt_existing_code,
    curr_fn,
)

from langchain.callbacks.openai_info import MODEL_COST_PER_1K_TOKENS
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import (
    LLMResult,
    AIMessage,
    HumanMessage,
    SystemMessage,
)

# Set up logging
logger = logging.getLogger(__name__)


class StreamInterceptor(BaseCallbackHandler):
    """
    A class used to intercept and handle the stream of tokens from the LLM.
    """

    def __init__(self):
        """
        Initialize the StreamInterceptor class.
        """
        self.tokens = ""
        self.llm_started = False
        self.llm_finished = False

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """
        Method to handle the start of the LLM.

        Parameters
        ----------
        serialized : Dict[str, Any]
            The serialized data.
        prompts : List[str]
            The list of prompts.
        **kwargs : Any
            Additional arguments.
        """
        self.llm_started = True

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """
        Method to handle new LLM token. Only available when streaming is enabled.

        Parameters
        ----------
        token : str
            The new token.
        **kwargs : Any
            Additional arguments.
        """
        """Run on new LLM token. Only available when streaming is enabled."""
        self.tokens += token

    def get_tokens(self) -> List[str]:
        """
        Method to return all tokens and clear the list.

        Returns
        -------
        List[str]
            The list of tokens.
        """
        """Return all tokens and clear the list."""
        return_tokens = self.tokens
        self.tokens = ""
        return return_tokens

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """
        Method to handle the end of the LLM.

        Parameters
        ----------
        response : LLMResult
            The response from the LLM.
        **kwargs : Any
            Additional arguments.
        """
        """Run when LLM ends running."""
        # print(response)
        self.llm_finished = True


class AIAppsforge(AI):
    """
    A class that extends the AI class to provide additional functionality.
    """

    def __init__(
        self, model_name="gpt-4", temperature=0.1, azure_endpoint="", openai_api_key=""
    ):
        super().__init__(model_name, temperature, azure_endpoint, openai_api_key)
        self.streaming_handler = StreamInterceptor()

    def next(
        self,
        messages: List[Message],
        prompt: Optional[str] = None,
        *,
        step_name: str,
    ) -> List[Message]:
        """
        Method to advance the conversation by sending message history to LLM and updating with the response.

        Parameters
        ----------
        messages : List[Message]
            The list of messages in the conversation.
        prompt : Optional[str], optional
            The prompt to use, by default None.
        step_name : str
            The name of the step.

        Returns
        -------
        List[Message]
            The updated list of messages in the conversation.
        """
        """
        Advances the conversation by sending message history
        to LLM and updating with the response.

        Parameters
        ----------
        messages : List[Message]
            The list of messages in the conversation.
        prompt : Optional[str], optional
            The prompt to use, by default None.
        step_name : str
            The name of the step.

        Returns
        -------
        List[Message]
            The updated list of messages in the conversation.
        """
        """
        Advances the conversation by sending message history
        to LLM and updating with the response.
        """
        if prompt:
            messages.append(self.fuser(prompt))

        logger.debug(f"Creating a new chat completion: {messages}")
        callbacks = [self.streaming_handler]
        response = self.backoff_inference(messages, callbacks)

        self.update_token_usage_log(
            messages=messages, answer=response.content, step_name=step_name
        )
        messages.append(response)
        logger.debug(f"Chat completion finished: {messages}")

        return messages


def improve_code(ai: AI, dbs: DBs, output_tokens: List[str]):
    """
    Function to improve the code.

    Parameters
    ----------
    ai : AI
        The AI object.
    dbs : DBs
        The DBs object.
    output_tokens : List[str]
        The list of output tokens.

    Returns
    -------
    List[Message]
        The list of messages.
    """

    files_info = get_code_strings(
        dbs.workspace, dbs.project_metadata
    )  # this has file names relative to the workspace path

    messages = [
        ai.fsystem(setup_sys_prompt_existing_code(dbs)),
    ]
    # Add files as input
    for file_name, file_str in files_info.items():
        code_input = format_file_to_input(file_name, file_str)
        messages.append(ai.fuser(f"{code_input}"))

    messages.append(ai.fuser(f"Request: {dbs.input['prompt']}"))

    messages = run_llm_and_get_tokens(ai, messages, output_tokens, curr_fn)

    overwrite_files_with_edits(messages[-1].content.strip(), dbs)
    return messages


def app_simple_gen(ai: AI, dbs: DBs, output_tokens: List[str]) -> List[Message]:
    """
    Function to generate a simple app.

    Parameters
    ----------
    ai : AI
        The AI object.
    dbs : DBs
        The DBs object.
    output_tokens : List[str]
        The list of output tokens.

    Returns
    -------
    List[Message]
        The list of messages.
    """

    messages: List[Message] = [
        SystemMessage(content=setup_sys_prompt(dbs)),
        HumanMessage(content=dbs.input["prompt"]),
    ]

    messages = run_llm_and_get_tokens(ai, messages, output_tokens, curr_fn)

    to_files_and_memory(messages[-1].content.strip(), dbs)
    return messages


# Create a function that calls the next method
def call_next(ai, messages, curr_fn):
    """
    Function to call the next method.

    Parameters
    ----------
    ai : AI
        The AI object.
    messages : List[Message]
        The list of messages.
    curr_fn : function
        The current function.
    """
    ai.next(messages, step_name=curr_fn())


def run_llm_and_get_tokens(
    ai: AI, messages: List[Message], output_tokens: List[str], curr_fn: function
) -> List[Message]:
    """
    Function to run the LLM and continuously get tokens until the LLM is finished.

    Parameters
    ----------
    ai : AI
        The AI object.
    messages : List[Message]
        The list of messages.
    output_tokens : List[str]
        The list of output tokens.
    curr_fn : function
        The current function.

    Returns
    -------
    List[Message]
        The list of messages.
    """
    call_next_thread = threading.Thread(target=call_next, args=(ai, messages, curr_fn))
    call_next_thread.start()

    while not ai.streaming_handler.llm_finished:
        tokens = ai.streaming_handler.get_tokens()
        output_tokens += tokens
        time.sleep(0.05)

    call_next_thread.join()

    return messages
