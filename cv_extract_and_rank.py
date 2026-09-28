import glob
import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-4o"

# ---------------------------------------------------------------------------
# 1. Загрузка вспомогательных файлов
# ---------------------------------------------------------------------------
CANDIDATES_DIR = "data/candidates"
RUBRIC_FILE = "data/candidate_rubric.json"

if os.path.exists(RUBRIC_FILE):
    with open(RUBRIC_FILE, "r", encoding="utf-8") as f:
        rubric_data = json.load(f)
else:
    rubric_data = {
        "weights": {"academic": 0.4, "research": 0.3, "experience": 0.3}
    }

# ---------------------------------------------------------------------------
# 2. Схема и промпт для ИЗВЛЕЧЕНИЯ (Part 1 — Extraction)
# ---------------------------------------------------------------------------
EXTRACTION_SYSTEM_PROMPT = """You are a precise CV extraction system.
Extract structured candidate profiles strictly from the story provided.

CRITICAL EXTRACTION RULES:
1. NO ESTIMATION / NO INFERENCE: If a fact (like GPA) is missing, the field MUST be null. Never guess.
2. GPA SCALES: Record the original scale. Convert to standard 4.0 scale if another scale is used. If absent, set gpa_4_scale to null.
3. PUBLICATION STATUS:
   - Count ONLY outputs explicitly marked as 'published' or 'accepted' in published_peer_reviewed_count.
   - 'submitted', 'under review', 'in preparation', or 'in press' DO NOT count as published.
4. CONTRADICTIONS:
   - If the story states contradictory facts (e.g. GPA 3.2 and 3.5 in the same text), DO NOT resolve or average them.
   - Set the field (e.g., gpa_4_scale) to null, set has_contradictions=true, and describe the issue in contradiction_details.
5. EVIDENTIAL QUOTES: Provide exact short quotes from the story backing up each major field."""

EXTRACTION_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "candidate_cv",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "candidate_id": {"type": ["string", "null"]},
                "full_name": {"type": ["string", "null"]},
                "degree": {"type": ["string", "null"]},
                "graduation_year": {"type": ["integer", "null"]},
                "gpa_raw": {"type": ["number", "null"]},
                "original_gpa_scale": {"type": ["number", "null"]},
                "gpa_4_scale": {"type": ["number", "null"]},
                "languages": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "published_peer_reviewed_count": {"type": "integer"},
                "other_publications_count": {"type": "integer"},
                "total_countable_months_experience": {"type": "integer"},
                "has_contradictions": {"type": "boolean"},
                "contradiction_details": {"type": ["string", "null"]},
                "evidence_quotes": {
                    "type": "object",
                    "properties": {
                        "gpa_quote": {"type": ["string", "null"]},
                        "publications_quote": {"type": ["string", "null"]},
                        "experience_quote": {"type": ["string", "null"]}
                    },
                    "required": ["gpa_quote", "publications_quote", "experience_quote"],
                    "additionalProperties": False
                }
            },
            "required": [
                "candidate_id", "full_name", "degree", "graduation_year",
                "gpa_raw", "original_gpa_scale", "gpa_4_scale", "languages",
                "published_peer_reviewed_count", "other_publications_count",
                "total_countable_months_experience", "has_contradictions",
                "contradiction_details", "evidence_quotes"
            ],
            "additionalProperties": False
        }
    }
}

# ---------------------------------------------------------------------------
# 3. Схема и промпт для ОЦЕНКИ (Part 2 — Scoring)
# ---------------------------------------------------------------------------
SCORING_SYSTEM_PROMPT = f"""You are an evaluator scoring candidates strictly on their extracted CV profiles.

RUBRIC RULES:
{json.dumps(rubric_data, ensure_ascii=False, indent=2)}

Rate the profile on three sub-criteria with a score from 0.0 to 5.0:
1. academic: Score for GPA and degree quality (0 if missing/contradictory/null).
2. research: Score for peer-reviewed published outputs only.
3. experience: Score for countable months of relevant work/lab experience.

Do NOT calculate total scores or declare a winner. Return only the 3 sub-scores."""

SCORING_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "candidate_scores",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "academic": {"type": "number"},
                "research": {"type": "number"},
                "experience": {"type": "number"}
            },
            "required": ["academic", "research", "experience"],
            "additionalProperties": False
        }
    }
}

# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------
def extract_cv(story_text, filename):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": f"File: {filename}\nStory:\n{story_text}"}
        ],
        response_format=EXTRACTION_SCHEMA
    )
    return json.loads(response.choices[0].message.content)

def score_candidate(cv_data):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SCORING_SYSTEM_PROMPT},
            {"role": "user", "content": f"Candidate CV Data:\n{json.dumps(cv_data, ensure_ascii=False, indent=2)}"}
        ],
        response_format=SCORING_SCHEMA
    )
    return json.loads(response.choices[0].message.content)

def get_prose_winner(all_cvs):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a scholarship committee chair. Review these candidate profiles and state in prose who should win and why (in 2-3 sentences)."},
            {"role": "user", "content": f"Profiles:\n{json.dumps(all_cvs, ensure_ascii=False, indent=2)}"}
        ]
    )
    return response.choices[0].message.content

# ---------------------------------------------------------------------------
# Точка входа (Main execution)
# ---------------------------------------------------------------------------
def main():
    story_files = sorted(glob.glob(os.path.join(CANDIDATES_DIR, "*")))
    if not story_files:
        print(f"Ошибка: файлы не найдены в {CANDIDATES_DIR}")
        return

    extracted_cvs = []
    results = []
    weights = {"academic": 0.4, "research": 0.3, "experience": 0.3}

    print("=== PART 1 & 2: EXTRACTION & COMPUTED SCORING ===\n")

    for filepath in story_files:
        filename = os.path.basename(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            story_text = f.read()

        print(f"Извлечение данных: {filename}...")
        cv = extract_cv(story_text, filename)
        extracted_cvs.append(cv)

        scores = score_candidate(cv)

        # Вычисление итогового балла КОДОМ (а не нейросетью!)
        weighted_total = round(
            (scores["academic"] * weights["academic"]) +
            (scores["research"] * weights["research"]) +
            (scores["experience"] * weights["experience"]), 2
        )

        results.append({
            "story": filename,
            "candidate_id": cv.get("candidate_id") or filename,
            "academic": scores["academic"],
            "research": scores["research"],
            "experience": scores["experience"],
            "weighted_total": weighted_total,
            "cv": cv
        })

    # Сортировка результата в коде
    results.sort(key=lambda x: x["weighted_total"], reverse=True)
    winner = results[0]

    # Печать итоговой таблицы
    print("\n" + "="*75)
    print(f"{'Story':<12} | {'Academic':<9} | {'Research':<9} | {'Experience':<10} | {'Weighted Total (CODE)':<20}")
    print("-" * 75)
    for r in results:
        print(f"{r['story']:<12} | {r['academic']:<9.2f} | {r['research']:<9.2f} | {r['experience']:<10.2f} | {r['weighted_total']:<20.2f}")
    print("="*75)

    print(f"\n🏆 WINNER COMPUTED BY CODE: {winner['story']} (Candidate ID: {winner['candidate_id']}) with score {winner['weighted_total']}")

    # Запрос мнения в прозе
    print("\n=== PROSE WINNER ANSWER (ASKED SEPARATELY) ===")
    prose_answer = get_prose_winner(extracted_cvs)
    print(prose_answer)

    # Дамп JSON истории с противоречием (story-06)
    story_6 = next((r["cv"] for r in results if "06" in r["story"]), None)
    if story_6:
        print("\n=== RAW JSON FOR CONTRADICTORY STORY (story-06) ===")
        print(json.dumps(story_6, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
