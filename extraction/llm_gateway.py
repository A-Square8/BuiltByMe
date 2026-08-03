import json
from typing import Optional, Type, Any, Dict
from pydantic import BaseModel

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate


class LLMGatewayException(Exception):
    pass


def get_llm_client(provider: str, api_key: str, temperature: float = 0.2) -> BaseChatModel:
    """
    Instantiates the correct LangChain chat model based on the provider.
    """
    provider = provider.lower().strip()
    
    if not api_key:
        raise LLMGatewayException(f"API key is required for provider '{provider}'.")
        
    try:
        if provider == 'groq':
            from langchain_groq import ChatGroq
            return ChatGroq(
                api_key=api_key,
                model_name="llama-3.1-8b-instant",  # Defaulting to a fast model
                temperature=temperature
            )
        elif provider == 'gemini':
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                api_key=api_key,
                model="gemini-3.5-flash-lite",
                temperature=temperature
            )
        elif provider == 'nvidia':
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=api_key,
                model="stepfun-ai/step-3.5-flash",
                temperature=temperature,
                max_tokens=16384,
                request_timeout=480
            )
        else:
            raise LLMGatewayException(f"Unsupported AI provider: {provider}")
    except ImportError as e:
        raise LLMGatewayException(f"Failed to import required packages for '{provider}'. Error: {e}")
    except Exception as e:
        raise LLMGatewayException(f"Failed to initialize LLM client for '{provider}'. Error: {e}")


def generate_content(
    provider: str,
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    response_schema: Optional[Type[BaseModel]] = None,
    temperature: float = 0.2
) -> Any:
    """
    Generates content using the specified LLM provider.
    
    Args:
        provider: 'groq', 'gemini', or 'nvidia'.
        api_key: The API key for the chosen provider.
        system_prompt: Instructions for the LLM.
        user_prompt: The specific content request.
        response_schema: A Pydantic BaseModel class for structured output.
        temperature: Sampling temperature.
        
    Returns:
        If response_schema is provided, returns an instance of that Pydantic model.
        Otherwise, returns the raw string content.
    """
    try:
        llm = get_llm_client(provider, api_key, temperature)
        
        parser = None
        # Apply structured output if a schema is provided
        if response_schema:
            if provider == 'nvidia':
                from langchain_core.output_parsers import PydanticOutputParser
                parser = PydanticOutputParser(pydantic_object=response_schema)
                system_prompt += f"\n\n{parser.get_format_instructions()}"
            else:
                try:
                    llm = llm.with_structured_output(response_schema)
                except NotImplementedError:
                    raise LLMGatewayException(f"Provider '{provider}' does not support structured output in LangChain.")
                
        # Invoke the model
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = llm.invoke(messages)
        
        if response_schema:
            if provider == 'nvidia' and parser:
                return parser.invoke(response)
            else:
                return response # This is a parsed Pydantic object
        else:
            return response.content # This is a string

    except LLMGatewayException:
        raise
    except Exception as e:
        raise LLMGatewayException(f"Error during content generation: {str(e)}")
