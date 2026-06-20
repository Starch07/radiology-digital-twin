content = r'''import os
import time
from typing import Dict, Optional, Union, Callable, List, Tuple
from google import genai
from google.genai import types
import openai
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx
import asyncio
from tqdm.asyncio import tqdm_asyncio

load_dotenv()

GEMINI_SYSTEM_INSTRUCTION = """You are an AI assistant. Your task is to answer the 'New Survey Question' as if you are the person described in the 'Persona Profile' (which consists of their past survey responses). Adhere to the persona by being consistent with their previous answers and stated characteristics. Follow all instructions provided for the new question carefully regarding the format of your answer."""

class VerificationFailedError(Exception):
    def __init__(self, message, prompt_id, llm_response_data=None):
        super().__init__(message)
        self.prompt_id = prompt_id
        self.llm_response_data = llm_response_data

class LLMConfig:
    def __init__(self, model_name, temperature=0.7, max_tokens=None, system_instruction=None, max_retries=10, max_concurrent_requests=5, verification_callback=None, verification_callback_args=None):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_instruction = system_instruction or GEMINI_SYSTEM_INSTRUCTION
        self.max_retries = max_retries
        self.max_concurrent_requests = max_concurrent_requests
        self.verification_callback = verification_callback
        self.verification_callback_args = verification_callback_args if verification_callback_args is not None else {}

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=60), retry=retry_if_exception_type((ConnectionError, TimeoutError, openai.APITimeoutError, openai.APIConnectionError, openai.RateLimitError, openai.APIError)), reraise=True)
async def _get_openai_response_direct(prompt, config):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    async with httpx.AsyncClient(timeout=1000.0) as client:
        aclient = openai.AsyncOpenAI(api_key=api_key, http_client=client)
        messages = [{"role": "system", "content": config.system_instruction}, {"role": "user", "content": prompt}]
        response = await aclient.chat.completions.create(model=config.model_name, messages=messages, temperature=config.temperature, max_tokens=config.max_tokens)
        return {"response_text": response.choices[0].message.content, "usage_details": {"prompt_token_count": response.usage.prompt_tokens, "completion_token_count": response.usage.completion_tokens, "total_token_count": response.usage.total_tokens}}

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=60), retry=retry_if_exception_type((ConnectionError, TimeoutError)), reraise=True)
async def _get_gemini_response_direct(prompt, config):
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")
    g_client = genai.Client(api_key=api_key)
    response = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: g_client.models.generate_content(
            model=config.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=config.system_instruction,
                temperature=config.temperature,
                max_output_tokens=config.max_tokens,
            ),
        )
    )
    if not response.candidates:
        return {"error": "No candidates returned from Gemini", "response_text": "", "usage_details": {}}
    finish_reason = str(response.candidates[0].finish_reason) if response.candidates else "UNKNOWN"
    if "SAFETY" in finish_reason or "RECITATION" in finish_reason:
        return {"error": f"Generation stopped: {finish_reason}", "response_text": "", "usage_details": {}}
    usage_metadata = response.usage_metadata
    return {"response_text": response.text, "usage_details": {"prompt_token_count": getattr(usage_metadata, "prompt_token_count", 0), "candidates_token_count": getattr(usage_metadata, "candidates_token_count", 0), "total_token_count": getattr(usage_metadata, "total_token_count", 0)}}

async def get_llm_response_with_internal_retry(prompt, config, provider):
    try:
        if provider.lower() == "gemini":
            return await _get_gemini_response_direct(prompt, config)
        elif provider.lower() == "openai":
            return await _get_openai_response_direct(prompt, config)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    except Exception as e:
        return {"error": f"LLM API call failed: {str(e)}", "provider": provider}

async def _process_single_prompt_attempt_with_verification(prompt_id, prompt_text, config, provider, semaphore):
    async with semaphore:
        last_exception_details = None
        for attempt in range(config.max_retries):
            try:
                llm_response_data = await get_llm_response_with_internal_retry(prompt_text, config, provider)
                if "error" in llm_response_data and llm_response_data["error"]:
                    return prompt_id, llm_response_data
                if config.verification_callback:
                    verified = await asyncio.to_thread(config.verification_callback, prompt_id, llm_response_data, prompt_text, **config.verification_callback_args)
                    if not verified:
                        last_exception_details = {"error": f"Verification failed on attempt {attempt + 1}", "prompt_id": prompt_id, "llm_response_data": llm_response_data}
                        if attempt == config.max_retries - 1:
                            return prompt_id, last_exception_details
                        await asyncio.sleep(min(2 * 2 ** attempt, 30))
                        continue
                return prompt_id, llm_response_data
            except Exception as e:
                last_exception_details = {"error": f"Unexpected error: {str(e)}", "prompt_id": prompt_id}
                if attempt == config.max_retries - 1:
                    return prompt_id, last_exception_details
                await asyncio.sleep(min(2 * 2 ** attempt, 30))
        return prompt_id, last_exception_details if last_exception_details else {"error": f"Exhausted all retries for {prompt_id}."}

async def process_prompts_batch(prompts, config, provider="gemini", desc="Processing LLM prompts and verifying"):
    semaphore = asyncio.Semaphore(config.max_concurrent_requests)
    results = {}
    tasks = [_process_single_prompt_attempt_with_verification(pid, p_text, config, provider, semaphore) for pid, p_text in prompts]
    for future in tqdm_asyncio(asyncio.as_completed(tasks), total=len(tasks), desc=desc):
        prompt_id, response_data = await future
        results[prompt_id] = response_data
    return results
'''

with open('text_simulation/llm_helper.py', 'w') as f:
    f.write(content)
print('Done! Lines written:', len(content.splitlines()))
