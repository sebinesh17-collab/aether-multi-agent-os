import json, re
from pathlib import Path, PurePosixPath
from ..config import settings

def _safe_relative(value: str) -> Path:
    raw=str(value).replace("\\", "/")
    rel=PurePosixPath(raw)
    if rel.is_absolute() or not rel.parts or any(x in ("", ".", "..") for x in rel.parts):
        raise ValueError("Artifact path must be a safe relative path")
    if len(rel.parts)>12 or any(len(x)>120 for x in rel.parts):
        raise ValueError("Artifact path is too deep or contains an oversized segment")
    return Path(*rel.parts)

def materialize_output(raw: str, project_id: int, sequence: int) -> str:
    """Parse JSON artifact output and persist only bounded UTF-8 text files."""
    root=Path(settings.artifact_dir)/f"project_{project_id}"
    root.mkdir(parents=True,exist_ok=True)
    try: data=json.loads(raw)
    except Exception:
        rel=Path("task-results")/f"task-{sequence:05d}.md"
        target=root/rel; target.parent.mkdir(parents=True,exist_ok=True); target.write_text(raw,encoding="utf-8")
        return json.dumps({"summary":"Agent returned free-form text; saved as a Markdown result.","artifacts":[str(rel)]},ensure_ascii=False)
    if not isinstance(data,dict): data={"summary":str(data),"artifacts":[]}
    created=[]; total=0
    for index,item in enumerate(data.get("artifacts",[])[:20]):
        if not isinstance(item,dict) or not isinstance(item.get("content"),str): continue
        try: rel=_safe_relative(item.get("path") or f"task-results/task-{sequence:05d}-{index}.txt")
        except ValueError: continue
        content=item["content"]
        if len(content.encode("utf-8"))>500_000 or total+len(content.encode("utf-8"))>2_000_000: continue
        target=root/rel
        if target.exists(): target=root/"task-artifacts"/f"task-{sequence:05d}"/rel
        target.parent.mkdir(parents=True,exist_ok=True)
        resolved=target.resolve()
        if not resolved.is_relative_to(root.resolve()): continue
        target.write_text(content,encoding="utf-8")
        created.append(str(target.relative_to(root))); total+=len(content.encode("utf-8"))
    summary=str(data.get("summary", "Task completed"))[:12000]
    return json.dumps({"summary":summary,"artifacts":created,"validation":data.get("validation",[]),"risks":data.get("risks",[])},ensure_ascii=False)
