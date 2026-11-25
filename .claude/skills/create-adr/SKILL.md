---
name: create-adr
description: "Draft a new eShop_AI Architecture Decision Record from docs/adr/template.md with the next free number, context, decision, alternatives, consequences and linked requirements and tasks. Manual invocation only; updates the decision index only when authorized."
argument-hint: "<short decision title>"
disable-model-invocation: true
---

# Create an ADR

Decision: **$ARGUMENTS**.

1. **Allocate the number**: list `docs/adr/NNNN-*.md`, take the highest
   number plus one (four digits), and confirm no file or index row in
   `docs/DECISIONS.md` already uses it.
2. **Check for overlap** with accepted ADRs and unresolved decisions (UD-NN
   in `docs/PRD.md` section 20 and `docs/DECISIONS.md`). If an accepted ADR
   already decides this, propose superseding it instead of duplicating.
3. **Draft** `docs/adr/NNNN-short-title.md` by copying `docs/adr/template.md`:
   status **Proposed**, today's date, the Jira key, context with PRD IDs
   (not repeated text), a one- or two-sentence decision, at least two
   alternatives with reasons, positive and negative consequences, related
   requirements, tasks and architecture sections, and measurable
   reconsideration conditions.
4. **Ask before indexing.** Adding the row to `docs/DECISIONS.md`
   (number, title, status, date) and marking the ADR **Accepted** require
   the project owner's approval. Never edit the decision of an accepted ADR.
5. **Validate** with `python3 scripts/validate_docs.py --strict`.

## Output

The ADR path, a summary of the decision and alternatives, open questions
for the owner, and the validator result.
