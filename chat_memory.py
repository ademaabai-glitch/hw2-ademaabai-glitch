import json
import os
import sys
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-5.6-luna"

# Загружаем файлы данных
with open("data/records.json", "r", encoding="utf-8") as f:
    records = json.load(f)

with open("data/policy.json", "r", encoding="utf-8") as f:
    policy = json.load(f)

with open("data/chat_script.json", "r", encoding="utf-8") as f:
    chat_data = json.load(f)

with open("data/memory_state.schema.json", "r", encoding="utf-8") as f:
    memory_schema = json.load(f)

SYSTEM_PROMPT = f"""You are a helpful grant office assistant.
RECORDS:
{json.dumps(records, ensure_ascii=False)}

POLICY:
{json.dumps(policy, ensure_ascii=False)}

Respond accurately and concisely to applicant enquiries."""

COMPRESSION_PROMPT = """Summarize the conversation so far into a structured memory state JSON matching this schema strictly.
Capture all key facts, applicant details, verified documents, and current status."""

STATE_RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "memory_state",
        "strict": True,
        "schema": memory_schema
    }
}

def compress_history(messages):
    prompt_messages = messages + [
        {"role": "system", "content": COMPRESSION_PROMPT}
    ]
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=prompt_messages,
            response_format=STATE_RESPONSE_SCHEMA
        )
        state_obj = json.loads(response.choices[0].message.content)
        return state_obj, response.usage.total_tokens
    except Exception as e:
        print(f"[Ошибка сжатия]: {e}")
        return None, 0

def run_scripted(compress_enabled=False):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    compressed_state = None
    token_log = []

    # Извлекаем список сообщений и контрольных вопросов из структуры файла
    conversation = chat_data.get("conversation", [])
    probes = chat_data.get("probes", [])

    mode_name = "Со сжатием памяти" if compress_enabled else "Без сжатия (обычный)"
    print(f"\n--- Запуск режима: {mode_name} ---")

    step_counter = 0
    for user_text in conversation:
        # Проверяем команду сжатия
        if user_text.strip() == "<compress>":
            if compress_enabled:
                print("\n[Сжатие] Встречена команда <compress>. Выполняем сжатие памяти...")
                state, c_tokens = compress_history(messages)
                if state:
                    compressed_state = state
                    messages = [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "system", "content": f"CURRENT CONVERSATION STATE: {json.dumps(compressed_state, ensure_ascii=False)}"}
                    ]
                    print(f"[Сжатие] Память успешно сжата! Затрачено токенов: {c_tokens}\n")
            else:
                print("[Пропуск] Встречен маркер <compress>, пропускаем шаг в режиме без сжатия.")
            continue

        step_counter += 1
        messages.append({"role": "user", "content": user_text})

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages
        )

        reply = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        token_log.append({"turn_id": step_counter, "total_tokens": tokens_used})

        messages.append({"role": "assistant", "content": reply})
        print(f"Шаг {step_counter} [Токенов: {tokens_used}]: {user_text[:40]}... -> {reply[:50]}...")

    print("\n--- Проверка контрольных вопросов (Probes) ---")
    probe_results = []
    for probe in probes:
        p_id = probe.get("id", "")
        question = probe.get("question", "")
        expect_list = probe.get("expect_contains", [])

        probe_msg = messages + [{"role": "user", "content": question}]
        res = client.chat.completions.create(
            model=MODEL,
            messages=probe_msg
        )
        answer = res.choices[0].message.content

        # Проверяем, содержит ли ответ ожидаемое ключевое слово
        retrieved = any(exp.lower() in answer.lower() for exp in expect_list)
        status = "Сохранено (Retrieved)" if retrieved else "Утеряно (Lost)"

        probe_results.append({
            "id": p_id,
            "question": question,
            "status": status,
            "answer": answer
        })
        print(f"[{p_id}] Статус: {status}")
        print(f"    Вопрос: {question}")
        print(f"    Ответ:  {answer}\n")

    return token_log, probe_results, compressed_state

def main():
    print("=== ВЫПОЛНЕНИЕ SUBLAB MEDIUM: ПРОГОН БЕЗ СЖАТИЯ ===")
    uncomp_tokens, uncomp_probes, _ = run_scripted(compress_enabled=False)

    print("\n" + "="*70 + "\n")

    print("=== ВЫПОЛНЕНИЕ SUBLAB MEDIUM: ПРОГОН СО СЖАТИЕМ ===")
    comp_tokens, comp_probes, final_state = run_scripted(compress_enabled=True)

    print("\n=== СРАВНЕНИЕ ИСПОЛЬЗОВАНИЯ ТОКЕНОВ ===")
    print(f"{'№ Шага (Turn ID)':<18} | {'Токены (Без сжатия)':<25} | {'Токены (Со сжатием)':<25}")
    print("-" * 75)

    max_turns = max(len(uncomp_tokens), len(comp_tokens))
    for i in range(max_turns):
        u_t = uncomp_tokens[i] if i < len(uncomp_tokens) else {"turn_id": "-", "total_tokens": "-"}
        c_t = comp_tokens[i] if i < len(comp_tokens) else {"turn_id": "-", "total_tokens": "-"}
        print(f"{str(u_t['turn_id']):<18} | {str(u_t['total_tokens']):<25} | {str(c_t['total_tokens']):<25}")

    print("\n=== ФИНАЛЬНЫЙ СЖАТЫЙ ОБЪЕКТ СОСТОЯНИЯ (MEMORY STATE) ===")
    print(json.dumps(final_state, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
