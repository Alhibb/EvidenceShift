# Related work and positioning

Sources checked on 14 November 2026. These notes are based on the authors' abstracts, not a full systematic review. Read the complete papers and evaluation rubrics before claiming novelty or choosing a final comparison.

1. Han Wang, Archiki Prasad, Elias Stengel-Eskin and Mohit Bansal (2025), *Retrieval-Augmented Generation with Conflicting Evidence*. https://arxiv.org/abs/2504.13079 . Introduces RAMDocs and MADAM-RAG to study ambiguity, misinformation and noisy evidence jointly. EvidenceShift is a much smaller controlled synthetic pilot, not a replacement for that benchmark or a comparable evaluation of its method.

2. Arie Cattan et al. (2025), *DRAGged into Conflicts: Detecting and Addressing Conflicting Sources in Search-Augmented LLMs*. https://arxiv.org/abs/2506.08500 . Introduces a conflict taxonomy and CONFLICTS benchmark; its abstract reports benefits from explicit conflict reasoning prompts. Therefore the general intervention in EvidenceShift is not new. The defensible positioning is a modest replication/extension focused on date-versus-authority distinctions and document-order sensitivity, subject to comparison with the full paper.

3. Apart Research, *AI x Epistemics Research Sprint*, 13–15 November 2026. https://apartresearch.com/sprints/ai-x-epistemics-research-sprint-2026-11-13-to-2026-11-15 . The sprint prioritises a clear research question, execution and evidence. A small synthetic pilot might fit model epistemics evaluation; fit does not imply novelty or competitiveness.

Technical interface reference: https://platform.openai.com/docs/api-reference/chat/create . The runner sends standard chat-completion requests over HTTP using the Python standard library. Provider-specific models and supported parameters must be checked on a development run. OpenAI-compatible endpoints are not guaranteed to implement every field identically. No provider API was exercised during package construction.

## What to add if time permits

After reading the complete CONFLICTS paper, identify which authority/effective-date slices overlap. Use a clearly documented public subset or add independently written, less explicit packets as an external-validity check. Respect dataset licensing. Do not silently expand the frozen primary test; designate additions exploratory. No performance comparison with published results is valid unless task, data, model and scoring are aligned.
