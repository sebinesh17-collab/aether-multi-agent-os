import re
from ..config import settings
DEPARTMENTS = ["Product & Research", "Architecture", "Frontend Engineering", "Backend Engineering", "Data & AI", "Cloud & DevOps", "Security", "Quality Assurance", "Database", "Mobile", "Integrations", "UX & Accessibility", "Performance", "Documentation", "Release & Operations"]
PHASES = ["discovery", "requirements", "architecture", "design", "implementation", "integration", "testing", "security-review", "performance-review", "documentation", "deployment", "acceptance"]

def requirements_from_text(text: str) -> list[str]:
    rows=[]
    for line in text.splitlines():
        s=re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", line).strip()
        if len(s) >= 18 and not s.startswith("["): rows.append(s[:800])
    return list(dict.fromkeys(rows))[:500]

def build_task_plan(name: str, brief: str, source_texts: list[str]) -> list[dict]:
    corpus = "\n".join([brief] + source_texts)
    reqs = requirements_from_text(corpus)
    if not reqs: reqs = [brief.strip() or f"Deliver the project: {name}"]
    targets = min(settings.max_tasks_per_project, max(settings.min_tasks_per_project, len(reqs)*len(PHASES)))
    tasks=[]; seq=1
    # Fan out across requirements, phases, departments, and focused work slices.
    i=0
    while len(tasks) < targets:
        req=reqs[i % len(reqs)]; phase=PHASES[(i // len(reqs)) % len(PHASES)]; dept=DEPARTMENTS[i % len(DEPARTMENTS)]
        slice_no=(i // (len(reqs)*len(PHASES))) + 1
        tasks.append({"sequence":seq,"title":f"{phase.replace('-', ' ').title()}: {req[:115]} [work package {slice_no}]","description":f"Project: {name}\nDepartment: {dept}\nPhase: {phase}\nRequirement/source: {req}\nWork package: {slice_no}\nInstructions: inspect relevant source files, produce a concrete deliverable, state assumptions, list files or artifacts to change, include verification steps, and report blockers. Avoid claiming code was changed unless an artifact was actually produced.","phase":phase,"department":dept,"agent_id":f"specialist-{((seq-1)%15000)+1:05d}"})
        seq+=1; i+=1
    return tasks
