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

mock_chain = MagicMock()
mock_response = MagicMock()
mock_response.content = '{\n  "name": "Jane Doe",\n  "email": "jane@acme.com",\n  "company": "Acme Corp"\n}'
mock_chain.invoke.return_value = mock_response

mock_prompt_template_class = MagicMock()
mock_prompt_template_instance = MagicMock()
mock_prompt_template_instance.__or__.return_value = mock_chain
mock_prompt_template_class.return_value = mock_prompt_template_instance
sys.modules['langchain_core.prompts'].PromptTemplate = mock_prompt_template_class

mock_rag_service.get_llm.return_value = mock_llm
sys.modules['app.services.rag_service'] = mock_rag_service

# Mock MongoDB leads collection
mock_leads_coll = MagicMock()
upserted_leads = {}
def mock_update_one(filter_query, update_doc, upsert=True):
    session_id = filter_query.get("session_id")
    upserted_leads[session_id] = update_doc["$set"]

mock_leads_coll.update_one.side_effect = mock_update_one

mock_mongo = MagicMock()
mock_mongo.get_leads_collection.return_value = mock_leads_coll
sys.modules['app.db.mongo'] = mock_mongo

# Import lead_scoring module
import app.services.lead_scoring as lead_mod

# 1. Test Entity Extraction
entities = lead_mod.extract_lead_entities("Hi, my name is Jane Doe from Acme Corp. Email me at jane@acme.com.")
assert entities["name"] == "Jane Doe"
assert entities["email"] == "jane@acme.com"
assert entities["company"] == "Acme Corp"

# 2. Test Score Calculation
score_sales_full = lead_mod.calculate_lead_score(
    intent="Sales",
    extracted_info=entities,
    turn_count=3
)
# Sales (40) + Email (25) + Company (20) + Name (10) + TurnCount>=3 (10) = 105 -> clamped to 100
assert score_sales_full == 100

score_pricing_partial = lead_mod.calculate_lead_score(
    intent="Pricing",
    extracted_info={"name": None, "email": "john@test.com", "company": None},
    turn_count=1
)
# Pricing (30) + Email (25) = 55
assert score_pricing_partial == 55

# 3. Test Process and Store Lead in MongoDB
lead_result = lead_mod.process_and_store_lead(
    session_id="lead_session_100",
    conversation_text="Hi, I am Jane Doe from Acme Corp (jane@acme.com). I want to buy subscriptions.",
    intent="Sales",
    turn_count=4
)

assert "lead_session_100" in upserted_leads
saved = upserted_leads["lead_session_100"]
assert saved["name"] == "Jane Doe"
assert saved["email"] == "jane@acme.com"
assert saved["company"] == "Acme Corp"
assert saved["score"] == 100

print("Verification SUCCESS: LLM entity extraction, lead scoring algorithm (0-100), and MongoDB leads persistence verified!")
