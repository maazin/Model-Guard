# ADR-0006: Local retrieval and LLM provider strategy

**Status:** Accepted

## Decision

- **Index:** section-level chunks (`## heading`) of the selected version's governance documents, vectorised with scikit-learn TF-IDF (1–2 grams) and ranked by cosine similarity. No pgvector, no embeddings service, no network.
- **Providers:** `LLMProvider` interface with `RuleBasedProvider` (mandatory, offline, deterministic), and optional `AnthropicProvider` / `OpenAIProvider` selected only when the corresponding API key is present.
- **Safety contract:** every provider's output is validated against the Pydantic `CopilotResponse` schema; invalid output returns a safe fallback; citations not in the retrieved set are dropped; retrieved text is wrapped as data and the model has no tools; the question is rejected if it contains borrower-like identifiers; only metadata is logged.

## Rationale

The copilot's job is to find missing evidence in a small, structured corpus. Lexical retrieval over headed sections is sufficient, keeps citations exact, and makes the offline fallback produce the *same* gaps as the readiness engine, which is the property the tests assert.

## Consequences

pgvector can replace `LocalIndex` behind the same `search(query, k)` method if the corpus grows; nothing else changes.
