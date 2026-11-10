# Example output — generated 2026-11-10

## Q1
```
Question: When should adults be screened for type 2 diabetes and which tests are used?

What the included sources say:
- Adults aged 35 to 70 years who have overweight or obesity should be screened for type 2 diabetes, and screening should be considered earlier in people with a first-degree relative with diabetes, a history of gestational diabetes, or high-risk ethnicity. [1]
- Screening can be performed with HbA1c, fasting plasma glucose, or a 75 g oral glucose tolerance test, and no single test is preferred in all settings. [1]
- If results are normal, repeat screening every 3 years is reasonable, with more frequent testing when risk factors change. [1]

Sources:
[1] Screening for Type 2 Diabetes in Adults — Sample corpus — summary in the style of ADA Standards of Care, 2024 (doc-001)

Disclaimer: This is general information from a small sample corpus, not medical advice. It does not replace a clinician who knows your history. If you are unwell or worried, speak to a qualified healthcare professional.

--- trace ---
[guardrails] check_input (1.0 ms) — When should adults be screened for type 2 diabetes and which
[planner] plan_question (0.1 ms)
[retriever] bm25_search (1.0 ms) — 3 sub-queries
[verifier] extract_and_verify (18.2 ms)
[answer] compose_from_verified_only (0.3 ms)
```

## Q2
```
Question: What are the benefits and limitations of AI in radiology imaging?

What the included sources say:
- Deep learning systems for radiology imaging have matched or exceeded average human performance on narrow tasks such as detecting lung nodules on CT, identifying diabetic retinopathy on fundus images, and flagging intracranial haemorrhage for priority reporting. [1]
- The clearest practical benefit is workflow: triage models that move urgent studies to the top of a worklist reduce reporting delay for time-critical findings. [1]
- A diagnostic AI system should be evaluated in stages: technical validation on held-out data, external validation at independent sites, silent prospective evaluation where predictions are recorded but not acted on, and finally an impact study measuring patient or workflow outcomes. [2]
- Clinicians remain accountable for decisions made with AI support, so the system should present its output in a way that makes disagreement and override easy. [2]

Sources:
[1] Artificial Intelligence in Radiology: Benefits and Limitations — Sample corpus — imaging informatics review summary, 2024 (doc-007)
[2] Evaluating Diagnostic AI Before Clinical Deployment — Sample corpus — clinical AI evaluation framework summary, 2023 (doc-008)

Disclaimer: This is general information from a small sample corpus, not medical advice. It does not replace a clinician who knows your history. If you are unwell or worried, speak to a qualified healthcare professional.
```

## Guardrail example
```
I can't diagnose you or advise on your personal medication or dose. That needs a clinician who can examine you and see your full history. I can share general, published information on the condition or test you're asking about if that would help — please rephrase it as a general question.

Disclaimer: This is general information from a small sample corpus, not medical advice. It does not replace a clinician who knows your history. If you are unwell or worried, speak to a qualified healthcare professional.
```

## Evaluation (bundled eval set only)
```json
{
  "cases": 6,
  "retrieval_recall_at_k": 1.0,
  "citation_precision": 1.0,
  "faithfulness_supported_ratio": 1.0,
  "per_case": [
    {
      "question": "When should adults be screened for type 2 diabetes and which tests are used?",
      "retrieval_hit": true,
      "retrieved": [
        "doc-001"
      ]
    },
    {
      "question": "How is hypertension diagnosed and what blood pressure thresholds define it?",
      "retrieval_hit": true,
      "retrieved": [
        "doc-003",
        "doc-004"
      ]
    },
    {
      "question": "How can sepsis be recognised early and what should happen in the first hour?",
      "retrieval_hit": true,
      "retrieved": [
        "doc-005",
        "doc-006",
        "doc-014"
      ]
    },
    {
      "question": "What are the benefits and limitations of AI in radiology imaging?",
      "retrieval_hit": true,
      "retrieved": [
        "doc-007",
        "doc-008"
      ]
    },
    {
      "question": "Who should be screened for colorectal cancer and at what age does screening start?",
      "retrieval_hit": true,
      "retrieved": [
        "doc-009",
        "doc-010"
      ]
    },
    {
      "question": "How is depression screened for in primary care?",
      "retrieval_hit": true,
      "retrieved": [
        "doc-011"
      ]
    }
  ],
  "note": "Measured only on the bundled eval set against the sample corpus."
}
```
