# Scientific Skills Reference

When developing new features, read the corresponding SKILL.md first,
then write code following the style of app/core/ai_client.py.

## Prompt Reference (SKILL.md)

- scientific_skills_ref/SKILL_hypothesis.md - topic evaluation prompts
- scientific_skills_ref/SKILL_literature_review.md - literature review prompts
- scientific_skills_ref/SKILL_scientific_writing.md - writing assistance prompts
- scientific_skills_ref/SKILL_experimental_design.md - experiment review prompts
- scientific_skills_ref/SKILL_citation_management.md - GB/T7714 citation prompts
- scientific_skills_ref/SKILL_database_lookup.md - database selection logic

## Reusable Python Scripts

- scientific_skills_ref/scripts/search_pubmed.py -> app/core/literature_reviewer/
- scientific_skills_ref/scripts/format_bibtex.py -> app/core/literature_reviewer/
- scientific_skills_ref/scripts/validate_citations.py -> app/core/literature_reviewer/
- scientific_skills_ref/scripts/search_google_scholar.py -> app/core/literature_reviewer/
- scientific_skills_ref/scripts/doe_designs.py -> app/core/experiment_evaluator/
- scientific_skills_ref/scripts/randomization.py -> app/core/experiment_evaluator/

## Coding Rules

- All prompts must return JSON, parsed via ai_client.parse_json_response()
- Always provide a fallback default dict on parse failure
- Differentiate prompts by paper type: humanities / science_engineering / arts
- New Celery queues: topic_eval / lit_review / writing_assist / experiment_eval
- Quota costs: topic_eval=3, lit_review=5, writing_assist=2, experiment_eval=3

