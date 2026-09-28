import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-5.6-luna"

# Загружаем данные из папки data
with open("data/records.json", "r", encoding="utf-8") as f:
    records = json.load(f)

with open("data/policy.json", "r", encoding="utf-8") as f:
    policy = json.load(f)

with open("data/enquiries.json", "r", encoding="utf-8") as f:
    enquiries = json.load(f)

# Системные промпты для 4 ролей
ROLE_PROMPTS = {
    "policy_officer": """You are a Policy Officer for a grant office.
Apply the policy rule exactly as written. Grant what it allows, refuse what it refuses, ask for missing documents as 'more_info'.
Do not soften decisions, and treat no claims in enquiries as evidence—only rely on official records.""",

    "front_desk": """You are a Front Desk agent.
Never turn an applicant away with a refusal. Anything the rule cannot grant today must come back as 'more_info', explaining clearly what document or information the applicant needs to return with.""",

    "auditor": """You are an Auditor.
Never grant a request on a first reading. Report what the record shows, mark anything needing a second reader or verification as 'more_info', and cite the specific rule or document relied upon.""",

    "bilingual_clerk": """You are a Bilingual Clerk.
Decide exactly as a policy officer would, but write the 'reason' field in the same language as the enquiry (e.g., Kazakh if the enquiry is in Kazakh, English if in English)."""
}

# Схема ответа (JSON Schema)
RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "grant_decision",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "applicant_id": {"type": "string"},
                "found": {"type": "boolean"},
                "decision": {
                    "type": "string",
                    "enum": ["granted", "refused", "more_info", "not_found"]
                },
                "amount": {"type": "number"},
                "missing_documents": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "reason": {"type": "string"}
            },
            "required": ["applicant_id", "found", "decision", "amount", "missing_documents", "reason"],
            "additionalProperties": False
        }
    }
}

def process_enquiry(role_name, enquiry):
    system_prompt = f"""{ROLE_PROMPTS[role_name]}

RECORDS DATABASE:
{json.dumps(records, ensure_ascii=False)}

GRANT POLICY:
{json.dumps(policy, ensure_ascii=False)}

Return JSON matching the schema strictly."""

    user_prompt = f"Enquiry ID: {enquiry['id']}\nText: {enquiry['text']}"

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format=RESPONSE_SCHEMA
    )

    return json.loads(response.choices[0].message.content)

def main():
    print("=== RUNNING SUBLAB EASY: ROLE PROMPTS ===\n")
    results = {}

    for role in ROLE_PROMPTS.keys():
        print(f"Processing role: {role}...")
        results[role] = []
        for enq in enquiries:
            res = process_enquiry(role, enq)
            results[role].append({
                "id": enq["id"],
                "expected": enq["expected"],
                "got": res
            })

    print("\n=== FIELD MOVEMENT MATRIX ===")
    print(f"{'Enquiry':<10} | {'Field':<18} | {'Policy Officer':<15} | {'Front Desk':<15} | {'Auditor':<15} | {'Bilingual Clerk':<15}")
    print("-" * 100)

    fields_to_check = ["found", "decision", "amount", "missing_documents"]

    for idx, enq in enumerate(enquiries):
        e_id = enq["id"]
        po_res = results["policy_officer"][idx]["got"]

        for field in fields_to_check:
            po_val = str(po_res.get(field))
            fd_val = str(results["front_desk"][idx]["got"].get(field))
            au_val = str(results["auditor"][idx]["got"].get(field))
            bc_val = str(results["bilingual_clerk"][idx]["got"].get(field))

            # Печатаем строку, если хотя бы одна роль отличается от policy_officer
            if fd_val != po_val or au_val != po_val or bc_val != po_val:
                print(f"{e_id:<10} | {field:<18} | {po_val:<15} | {fd_val:<15} | {au_val:<15} | {bc_val:<15}")

if __name__ == "__main__":
    main()
