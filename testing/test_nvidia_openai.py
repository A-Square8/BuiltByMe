import os
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

class TestModel(BaseModel):
    response: str

llm = ChatOpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="none", # We will just test instantiation
    model="stepfun-ai/step-3.5-flash",
    timeout=600,
    max_tokens=16384
)
print("Instantiated ChatOpenAI")
try:
    llm = llm.with_structured_output(TestModel)
    print("Supports structured output via Langchain adapter!")
except Exception as e:
    print(f"Error: {e}")
