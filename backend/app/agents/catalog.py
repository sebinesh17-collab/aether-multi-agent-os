from pathlib import Path
import json
PROMPT_ROOT = Path(__file__).parent / "prompts"
TIERS = {"master": 1, "principal": 10, "hod": 100, "leader": 1000, "specialist": 15000}

def load_agent(agent_id: str) -> dict:
    tier, number = agent_id.split("-")
    path = PROMPT_ROOT / tier / f"{agent_id}.json"
    if not path.exists(): raise KeyError(f"Unknown agent profile: {agent_id}")
    return json.loads(path.read_text(encoding="utf-8"))

def roster_counts() -> dict:
    return TIERS | {"total": sum(TIERS.values())}
