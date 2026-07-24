import sys
sys.path.insert(0, r"c:\Users\nerdyxdr\Desktop\RAG-chatbot")
from unittest.mock import MagicMock

# Mock dotenv
sys.modules['dotenv'] = MagicMock()

# Mock pydantic
mock_pydantic = MagicMock()
class DummyBaseModel:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
mock_pydantic.BaseModel = DummyBaseModel
mock_pydantic.Field = lambda default=..., **kwargs: default
sys.modules['pydantic'] = mock_pydantic

# Mock langchain_core.prompts
sys.modules['langchain_core'] = MagicMock()
sys.modules['langchain_core.prompts'] = MagicMock()

# Mock rag_service.get_llm
mock_rag_service = MagicMock()
mock_llm = MagicMock()

# Setup mock LLM chain output
mock_chain = MagicMock()
mock_response = MagicMock()
mock_response.content = '{\n  "intent": "Pricing",\n  "confidence": 0.95,\n  "reasoning": "User asked about subscription costs."\n}'
mock_chain.invoke.return_value = mock_response

mock_prompt_template_class = MagicMock()
mock_prompt_template_instance = MagicMock()
mock_prompt_template_instance.__or__.return_value = mock_chain
mock_prompt_template_class.return_value = mock_prompt_template_instance
sys.modules['langchain_core.prompts'].PromptTemplate = mock_prompt_template_class

mock_rag_service.get_llm.return_value = mock_llm
sys.modules['app.services.rag_service'] = mock_rag_service

# Import intent service module
import app.services.intent as intent_mod

# 1. Test LLM-driven Intent Classification for "Pricing"
res = intent_mod.classify_intent("How much does the monthly enterprise plan cost?")
assert res["intent"] == "Pricing"
assert res["confidence"] == 0.95
assert "subscription costs" in res["reasoning"]

# 2. Test fallback classification when LLM throws exception
mock_chain.invoke.side_effect = Exception("LLM Error")
res_fallback = intent_mod.classify_intent("I want to buy a subscription for my sales team")
assert res_fallback["intent"] in ["Sales", "Pricing"]
assert res_fallback["confidence"] == 0.7

print("Verification SUCCESS: LLM structured JSON intent classification and fallback logic verified!")
