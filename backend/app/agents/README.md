# Existing AI assistant

This package contains the original in-process LangGraph assistant and remains
unchanged during the repository reorganization. It continues to expose the existing
`/api/agents/chat` route through the LMS backend.

The extracted replacement lives in [`services/ai`](../../../services/ai/README.md).
Do not partially split this package across processes without an explicit API,
authorization, failure-handling, and data-ownership design.
