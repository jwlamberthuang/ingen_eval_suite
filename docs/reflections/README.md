# Reflections

- [One-page retrospective — Word](W04_Retrospective.docx) and
  [editable Markdown](retrospective.md): personal learning, transfer from earlier
  benchmarking work, the approximation perspective, and career exploration.
  The text incorporates the intern's supplied experience and career notes;
  the intern reported reviewing the prepared changes on 3 November 2026.
- [Final methodological log](phase_04.md): preserving the recorded baseline
  while distinguishing reproducible computation from measurement validity.

Earlier methodological logs remain available for [initial design](phase_01.md),
[RAG implementation](phase_02.md), and [extended evaluation](phase_03.md).
They describe the sequence of decisions rather than the repository's navigation
structure.

The retrospective Word document uses Times New Roman for Latin text and Songti SC
for Chinese. Its Markdown is the maintained text source. After reconciling any
direct Word edits, rebuild from the repository root:

```sh
python -m pip install -r requirements-documents.txt
python scripts/documents/build_reflections.py --overwrite
```

Inspect the resulting document in Word and verify that it remains one page
before distributing it. Font substitutions and office-suite differences can
change pagination.
