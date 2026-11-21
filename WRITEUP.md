# Meeting Memory Agent — Technical Write-up

## 1. Architecture

The Meeting Memory Agent is an evidence-grounded question-answering system built on the AMI Meeting Corpus. It processes 138 meetings, 48,148 speaker turns, and 35 teams.

The architecture follows a modular pipeline:

**Transcript Ingestion → Validation → SQLite Storage → Retrieval → Context Expansion → LLM Generation → Citation Validation**

Transcripts are parsed into structured speaker turns and validated using Pydantic. Validated data is stored in SQLite with relational constraints and indexes. SQLite FTS5 provides full-text search, with BM25 ranking relevant passages. Multiple retrieval queries are combined using Reciprocal Rank Fusion (RRF), followed by meeting-diversity selection. Neighboring transcript turns are added to provide conversational context.

An orchestrator coordinates retrieval, evidence coverage checks, generation, and final validation.

## 2. Model vs. Code Decisions

I used the LLM for tasks requiring natural-language understanding: interpreting questions, synthesizing information across meetings, and selecting relevant citation IDs.

I kept deterministic and verifiable operations in application code. These include transcript parsing, schema validation, database operations, retrieval ranking, citation mapping, quote verification, team validation, and meeting-coverage checks.

A key design decision was to prevent the LLM from directly supplying final quotations. Instead, it selects citation IDs, and application code retrieves the original speaker-turn text. This reduces fabricated quotation risk and makes quote verification deterministic.

This separation keeps the model responsible for language reasoning while application code enforces data integrity and assignment constraints.

## 3. Tools Used and Limitations

- **Python and Pydantic:** Structured transcript parsing and validation.
- **SQLite and FTS5:** Persistent storage and full-text retrieval. Lexical search can miss relevant passages when wording differs significantly.
- **Groq API with the OpenAI-compatible SDK:** LLM-based answer generation. Generation remains non-deterministic and depends on provider availability and model output quality.
- **Reciprocal Rank Fusion:** Combines multiple retrieval rankings, but cannot recover evidence that retrieval fails to find.
- **Pytest and Ruff:** Automated tests and code-quality checks.
- **Git and GitHub:** Version control and source-code delivery.

The citation validator checks quote existence, minimum quote length, speaker-turn boundaries, team membership, duplicate citations, and distinct-meeting coverage. However, it does not prove that a quotation semantically supports the generated answer. Human review and semantic evaluation remain necessary.

## 4. Production Requirements at Real Scale

A production deployment would require:

- Hybrid lexical and vector retrieval with measured retrieval quality.
- Automated answer-quality and semantic citation evaluation.
- Observability for latency, token usage, cost, retrieval results, and failures.
- Timeouts, bounded retries, rate limits, caching, and concurrency controls.
- Scalable storage and indexing as the corpus grows.
- Authentication, authorization, data isolation, and secure secret management.
- Regression testing, monitoring, human review, and reproducible deployment pipelines.

The current implementation provides a working evidence-grounded baseline. Production readiness would require additional reliability, evaluation, security, and scalability work.

**Dataset:** AMI Meeting Corpus — University of Edinburgh and partners. See `data/CREDITS.txt` for attribution and licensing information.