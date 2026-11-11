# Current portfolio authoring tools

The current builders keep the case PDF, Markdown, homepage summaries and featured evidence in the main Work Samples aligned. The public presentation uses bundled Inter fonts, dark ink, restrained indigo and pale neutral surfaces.

## Sources

- `04_case_studies/case_studies.json` is the case narrative source, including the shorter featured summaries used in the main PDF.
- The AI method builder uses the current method content and saved evaluation data in `01_ai_review`.
- `build_skills_portfolio.py` supplies the skills layout and links to the detailed exhibits.
- `homepage_template.html`, `homepage_triage.js` and `sync_web_copy.py` build the homepage from canonical cases, saved findings and module facts.
- `build_exhibit_pages.py` creates readable migration and knowledge pages directly from preserved reports.
- `assets/Inter-OFL.txt` and `assets/Inter_SOURCE.json` record the bundled font license and provenance.

## Build

Authoring requires Python 3.10+, ReportLab, Pillow and pypdf. These are document-generation dependencies; the scoring, migration and knowledge demonstrations use the Python standard library.

```sh
python3 -m pip install reportlab Pillow pypdf
python3 tools/build_portfolio.py
python3 tools/preflight.py
```

Run from the `public` folder, or give the full script path. No model, account or hosting service is called. The command rebuilds the current case, AI method, Work Samples PDFs, then synchronizes the case cards and tested demo facts. The overview sheet has been consolidated into page 1 of Work Samples. It does not modify the synthetic inputs, policies, prompts, saved model outputs or operational workbook.

After a content change, inspect the rendered pages before distributing the new PDFs. A successful build checks layout bounds and file structure; it does not replace legal review of the text.


## Interactive model demonstration

`build_review_demo.py` combines the preserved synthetic inputs, policy, prompts and archived model outputs with the versioned template and evidence-check code. It changes no source evidence.

```sh
python3 tools/build_review_demo.py --standalone
node tools/test_review_demo.cjs
```

The optional standalone file is written beside this folder as `AI_Review_Demonstration.html`, with embedded fonts and no companion-file dependencies. The regular `01_ai_review/replay.html` remains part of this portfolio. Local challenge outputs are temporary demonstrations, not new model runs.

## Release checks

`preflight.py` checks rendered HTML structure, local file and anchor links, external render dependencies and the two PDF link modes. It does not deploy the portfolio or call a model. Browser checks and legal-content review remain separate.

The public bundle is a standalone portfolio. Before replacing another site, preserve any existing pages and routes, then check the final hosted URLs.
