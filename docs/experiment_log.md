# Experiment log

Short notes, written as I went. Numbers are from the bundled sample
corpus and eval sets only — see the README's evaluation section before
quoting any of them anywhere.

## 2 Nov 2026 — The answer that should not exist

I asked the agent about Wilson disease, which is not in the corpus at
all. It still composed an "answer", stitched from a statins paragraph
and a screening paragraph that shared words like "diagnosed" and
"treatment". Every claim verified — against chunks that had nothing to
do with the question. Verification per claim is not enough; I need a
gate on whether there was enough *relevant* evidence to answer at all.
That is what became selective answering.

## 5 Nov 2026 — Retrieval failure analysis

Ran `notebooks/01_retrieval_failure_analysis.py` over the eval set plus
the out-of-corpus questions. The in-corpus questions are healthy:
expected document retrieved first every time (margins vary — sepsis is
the thinnest at 0.25, and it also has the lowest evidence strength). The
interesting failures are all out-of-corpus: five of the six still
retrieve *something* (the insulin question pulls the diabetes screening
document, strength 0.60), and only the amoxicillin question retrieves
nothing. So a "no retrieval, no answer" rule would catch almost none of
the bad cases — the strength score has to use coverage and retrieval
saturation, not just hit/miss.

## 9 Nov 2026 — Risk–coverage sweep, threshold choice

Swept the abstention threshold from 0.0 to 0.8 over 12 questions
(`notebooks/02_risk_coverage_experiment.py`, results in
`results/risk_coverage.csv`). At threshold 0 the system answers 11 of
12 and 5 of those answers are unsupported — risk 0.455. Risk hits 0 at
threshold 0.60, where all 6 in-corpus questions are still answered
(coverage 0.5). I set the default to 0.62 rather than exactly 0.60 for
a small safety margin, and noted the uncomfortable part honestly: the
gap between the strongest out-of-corpus score (0.596, the insulin
question) and the weakest in-corpus one (0.634, sepsis) is narrow. On a
corpus this small that is expected; the threshold will need
re-calibrating the moment the corpus grows.
