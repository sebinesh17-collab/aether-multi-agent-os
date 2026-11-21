from app.agents.catalog import roster_counts, load_agent

def test_roster_has_exactly_16111_profiles():
    assert roster_counts()["total"] == 16111
    assert sum(roster_counts()[k] for k in ("master","principal","hod","leader","specialist")) == 16111

def test_master_is_unique_and_prompted():
    a=load_agent("master-001")
    assert a["tier"] == "master"
    assert "critical" in a["system_prompt"].lower()

def test_department_prompts_exist():
    assert load_agent("specialist-00003")["department"] == "Frontend Engineering"
    assert load_agent("specialist-00004")["department"] == "Backend Engineering"
