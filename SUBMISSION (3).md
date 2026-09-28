# HW2 submission

**Name:** Abay Adema
**Student ID:** S23070175
**Group:** CSS4007-ENG-8 
**Repository:** hw2-ademaabai-glitch

## AI tool disclosure

I used Claude to help write short answers to the written questions. I ran all the code and produced all the tables and results myself.

---

## Sublab Easy — one task, four roles

### Decisions per role

| Enquiry | policy_officer | front_desk | auditor | bilingual_clerk |
|---|---|---|---|---|
| E-01 | granted | granted | more_info | granted |
| E-02 | ___ | ___ (amount 150000) | ___ | ___ (amount 150000) |
| E-03 | refused | more_info | refused | refused |
| E-04 | refused | more_info | refused | refused |
| E-05 | granted | granted | more_info | granted |
| E-06 | granted | granted | more_info | granted |
| E-07 | granted | granted | more_info | granted |
| E-08 | ___ | ___ | ___ | ___ |
| E-09 | refused | more_info | refused | refused |
| E-10 | more_info | more_info | more_info | refused |
| **agrees with `expected`** | ___/10 | ___/10 | ___/10 | ___/10 |
| **parsed** | ___/10 | ___/10 | ___/10 | ___/10 |
| **schema-valid** | ___/10 | ___/10 | ___/10 | ___/10 |

### Which field moved, on which enquiry, under which role

| Field | Enquiries that moved | Role(s) that moved it |
|---|---|---|
| `found` | none (moved on no enquiry) | none |
| `decision` | E-01, E-03, E-04, E-05, E-06, E-07, E-09, E-10 | auditor (E-01, E-05, E-06, E-07); front_desk (E-03, E-04, E-09); bilingual_clerk (E-10) |
| `amount` | E-02 | front_desk, bilingual_clerk |
| `missing_documents` | E-09 | front_desk |

### Raw replies

Reply for one enquiry where a role changed the decision (E-03, front_desk):

```
___ paste the full reply from your run ___
```

Reply for E-07 (the Kazakh enquiry) from the bilingual clerk:

```
___ paste the full reply from your run ___
```

### Written answers

**1. Which fields are role-sensitive and which are not?**

> `decision` is the most role-sensitive field: it moved on 8 enquiries. `amount` moved once (E-02) and `missing_documents` moved once (E-09). `found` did not move on any enquiry, so it is stable. Facts about the record are stable, but judgment is not.

**2. Which enquiries are most sensitive to the role, and why those?**

> E-03 and E-04 changed only under front_desk, which softens `refused` to `more_info`. They test cases where a strict answer is `refused` but a polite role hesitates. E-07 is the Kazakh enquiry and changed only under the auditor, who asks for more information. It tests language and cautious behaviour. E-10 is the only enquiry where the bilingual clerk differs from the policy officer (`refused` vs `more_info`). It tests an unclear case where the role decides how to break the tie. ___ (edit this using the text of the enquiries in `enquiries.json`)

**3. Where does discretion belong — the role paragraph, or code that reads `decision` afterwards?**

> Discretion belongs in code that reads `decision` afterwards, not only in the role paragraph. A downstream program sees only the JSON. It cannot tell which role produced a record, or whether `more_info` came from caution or from real doubt. If the role is not saved with the record, this information is lost.

**4. Is a role a boundary?**

> No. In Week 2 terms, a role paragraph is just text in the prompt. It changes the odds of an answer but does not enforce anything. If a wrong `decision` were expensive, I would put rules in code: a hard check of the amount against policy, a rule that `refused` needs human review, and a log of the role and prompt version with each record.

---

## Sublab Medium — memory you choose

### Tokens per call

| Call | A — never compressed | B — compressed at the `compress` turn |
|---|---|---|
| 1 | 823 | 765 |
| 2 | 844 | 835 |
| 3 | 863 | 845 |
| 4 | 918 | 893 |
| 5 | 1025 | 1012 |
| 6 | 1165 | 1094 |
| 7 | 1190 | 1212 |
| 8 | 1279 | 1311 |
| 9 | 1434 | 1416 |
| 10 | skipped (compress marker) | 2175 (compression call) |
| 11 | 1449 | 972 |
| 12 | 1484 | 1006 |
| **peak** | 1484 | 2175 (1416 without the compression call) |
| **total for the run** | 12474 | 13536 (11361 without the compression call) |

### Probes after the conversation

| Probe | Tests | A retrieved? | A answer | B retrieved? | B answer |
|---|---|---|---|---|---|
| Q-1 identity | turn 1 | yes | Daniyar Qoshan, A-202 | yes | Daniyar Qoshan, A-202 |
| Q-2 missing document | turn 5 | yes | ID card | yes | id card |
| Q-3 band and amount | turns 3–4 | yes | band 2, 150,000 KZT | yes | band 2, 150,000 KZT |
| Q-4 the constraint | turn 6 | yes (hedged: said "Thursday" but told me to confirm with the office) | Thursday, but "record does not specify" | yes | Thursdays |
| Q-5 the open question | turn 7 | yes | scanned vs original employer letter; policy does not say | yes | scanned vs original employer letter; policy does not say |
| **retrieved** | | 5/5 | | 5/5 | |

### The state my compression produced

```json
{
  "applicant_id": "A-202",
  "topic": "Need-based Study Grant 2026 eligibility and document submission",
  "facts": [
    "Applicant stated their name is Daniyar Qoshan.",
    "Applicant stated they sent their transcript last week.",
    "Applicant stated their family's certificate shows income band 2.",
    "Applicant stated they could not upload their id card because their home scanner broke.",
    "Applicant stated their sister Aruzhan applied last year and is on file."
  ],
  "decisions": [
    "Based on the record, the applicant currently does not qualify because the id card is not on file.",
    "If the id card is added and all requirements are met, the income-band-2 grant amount is 150,000 KZT.",
    "The policy does not specify whether an employer letter may be scanned or must be original, and it is not a substitute for the required id card.",
    "The policy does not specify whether a decision will be made the same day the id card is submitted.",
    "The sister's application does not affect the applicant's eligibility; applications are assessed separately."
  ],
  "constraints": [
    "Applicant can come to the office only on Thursdays.",
    "Applicant has lab all week otherwise."
  ],
  "open_questions": [],
  "language": "English"
}
```

### Written answers

**1. What did compression buy?**

> Peak tokens were 1484 without compression and 1416 with it (2175 if the compression call is counted). Both runs retrieved 5/5 probes, so nothing was lost. After the compress turn, each call was about 480 tokens cheaper (972 vs 1449, 1006 vs 1484). But the compression call itself cost 2175, so the total was not smaller (13536 vs 12474). It only pays off in a longer conversation. Also, A answered Q-4 with a hedge, and B answered it clearly.

**2. Why must the state be structured rather than a paragraph?**

> With named fields (`facts`, `constraints`, `decisions`, `open_questions`), the model must put each thing in a slot. A paragraph can silently drop the constraint or the ID. With an object, my code can check that the fields exist. It can also read one field, like `constraints`, without parsing text.

**3. What is missing from your state that you would add?**

> I would add `documents_received` (transcript: yes, id card: no) and the language the user prefers (the user started in Kazakh, but my state says English). I would also put the employer-letter question in `open_questions`, because it is empty now. To pay for this, I would drop the sister fact and "lab all week", because they do not change the decision.

**4. When is compression the wrong choice?**

> It is wrong when exact wording matters and cannot be recovered, for example a legal or medical talk, or a contract negotiation with exact numbers and dates. My program would not notice: it only checks the probes I wrote, so a lost detail I did not test would pass silently.

---

## Sublab Hard — stories in, CVs out, the best candidate by code

### Part 1 — extraction

| Story | Parsed? | Valid? | Fields that came back `null` | Traps hit |
|---|---|---|---|---|
| story-01 | yes | ___ | ___ | none |
| story-02 | yes | ___ | GPA fields (`gpa_raw`, `original_gpa_scale`, `gpa_4_scale`) | no GPA stated |
| story-03 | yes | ___ | ___ | GPA on another scale (converted to 3.68) |
| story-04 | yes | ___ | ___ | ___ |
| story-05 | yes | ___ | ___ | ___ |
| story-06 | yes | ___ | `candidate_id`, `gpa_raw`, `original_gpa_scale`, `gpa_4_scale` | contradicts itself (GPA 3.2 vs 3.5) |

The four traps, for reference: no GPA stated · a GPA on another scale · a paper that is not published · a story that contradicts itself.

Extraction for **story-06**:

```json
{
  "candidate_id": null,
  "full_name": "Nurzhan Abilov",
  "degree": "BSc in Statistics",
  "graduation_year": 2024,
  "gpa_raw": null,
  "original_gpa_scale": null,
  "gpa_4_scale": null,
  "languages": [
    "Kazakh",
    "Russian",
    "English"
  ],
  "published_peer_reviewed_count": 1,
  "other_publications_count": 1,
  "total_countable_months_experience": 40,
  "has_contradictions": true,
  "contradiction_details": "GPA mentioned as both 3.2 and 3.5, indicating uncertainty in the actual GPA.",
  "evidence_quotes": {
    "gpa_quote": "My GPA was 3.2. Actually I should double-check that, I think it was 3.5",
    "publications_quote": "one paper published, in a peer-reviewed proceedings, on survey weighting.",
    "experience_quote": "I have been at an insurance analytics team since February 2023, which is about forty months."
  }
}
```

### Part 2 — scores and the winner

| Candidate | academic (0–5) | research (0–5) | experience (0–5) | weighted total (code) |
|---|---|---|---|---|
| story-01 | 5.00 | 5.00 | 2.00 | 4.10 |
| story-02 | 0.00 | 1.00 | 5.00 | 1.80 |
| story-03 | 3.68 | 1.00 | 2.50 | 2.52 |
| story-04 | 3.00 | 3.00 | 5.00 | 3.60 |
| story-05 | 5.00 | 3.00 | 2.00 | 3.50 |
| story-06 | 0.00 | 3.00 | 5.00 | 2.40 |

**Winner, computed by my code:** story-01 (score 4.10)

**The model's prose answer, asked separately ("who should win?"):**

> Aziza Bekova should be awarded the scholarship due to her impressive academic record, evidenced by a GPA of 3.8 on a 4.0 scale, and significant research contributions with two published peer-reviewed papers. Her language skills and eight months of experience as a junior analyst further enhance her profile, showcasing her well-rounded capabilities and potential in the field of Computer Science.

### Part 3 — written answers

**1. Which rule did you have to add, and what broke without it?**

> ___ (edit) I added a rule to convert a GPA on another scale to the 4.0 scale in code (story-03). Without it, that story got academic 0.00 because the code could not compare the numbers. I also had to separate `published_peer_reviewed_count` from `other_publications_count`, so a paper that is not published does not count as research (this changed the research scores). Story-06 forced a third rule: a `has_contradictions` flag.

**2. Where did the model guess, and where did your code have to decide?**

> ___ (edit) Example of a guess: in the prose answer the model chose a winner with a short story about one person and did not use the rubric weights. Example of a code decision: my code gave academic 0.00 when the GPA was `null` (story-02, story-06), and it fixed the weights (0.4 academic, 0.3 research, 0.3 experience). The model cannot decide how to score a missing value.

**3. Did your prose ranking and your computed ranking agree?**

> Yes. The prose answer chose Aziza Bekova (story-01) and the code also chose story-01 (4.10). I trust the computed ranking, because the weights and rules are fixed and I can check every number. The prose answer only talks about one person and does not compare the others. To trust the prose alone, I would need to see it agree with the code on many different sets of stories, and give reasons that match the rubric.

**4. The rubric has no anchor for a contradicted field.**

> The model returned `null` for the GPA of story-06 and set `has_contradictions: true`, and my code then gave academic 0.00. This is too harsh, because the real GPA (3.2 or 3.5) is not zero. The rule should be: when a field is contradicted, do not score it as 0 silently. Use the lower value (3.2), mark the record `needs_review`, and let a human confirm. Here it does not change the winner: story-06 would need academic above 4.25 to pass story-01 (4.10), and a GPA of 3.2 or 3.5 cannot give that.

**5. How close were your top two candidates?**

> Story-01 got 4.10 and story-04 got 3.60. The gap is 0.50, which is much more than 0.05, so it is not close. I would tell the committee that story-01 wins clearly. To make a close call defensible, I would save the source quote for each value (I already keep `evidence_quotes`) and show the committee how each score was calculated.

---

## Reflection (optional, one short paragraph)

> Next time, I will ask for structured output with a fixed schema and validate it in code. I will not let the model decide anything that needs a fixed rule, like scores for missing or contradicted values. I will also log the role and prompt version with every result, and check important results with tests instead of only trusting the prose answer.
