# Glossary

Names people and agents use for code objects, mapped to the code's own
names. `/explain-the-code` reads this to build its dictionary. Add a row
when you meet a new alias; one section per repo or area.

## megalith: apps/wx-system, service-todo

| Said | Code | What it is |
|---|---|---|
| the enrollment | `TaskFlowWorker` | one worker in one task flow, with counts of their tasks by status |
| the summary | `TaskFlowWorkerAggregates` | one row per `TaskFlowWorker`, copying in the worker, tags and task counts |
