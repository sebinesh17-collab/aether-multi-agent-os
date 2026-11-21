TOOL_CATALOG = [
 {"name":"inspect_uploaded_files","category":"files","description":"Read extracted text and metadata for files attached to the current project.","authorization":"project owner"},
 {"name":"search_source_context","category":"files","description":"Find relevant terms in extracted project source text and return bounded excerpts.","authorization":"project owner"},
 {"name":"create_text_artifact","category":"artifacts","description":"Materialize validated UTF-8 text/code files under the project artifact directory.","authorization":"project worker"},
 {"name":"download_project_bundle","category":"artifacts","description":"Package generated source and documentation artifacts into a ZIP archive.","authorization":"project owner"},
 {"name":"validate_json","category":"quality","description":"Parse JSON content and report structural errors without executing it.","authorization":"project worker"},
 {"name":"calculate_sha256","category":"integrity","description":"Calculate SHA-256 checksums for uploaded files and generated artifacts.","authorization":"project worker"},
 {"name":"agent_debate","category":"decision","description":"Run independent Frontend and Backend proposals, then call the leadership escalation workflow.","authorization":"project owner"},
 {"name":"leader_council_review","category":"decision","description":"Convene a Leader panel, then HOD and Principal panels if unresolved.","authorization":"decision orchestrator"},
 {"name":"master_arbitration","category":"decision","description":"Invoke the single Master Leader only for critical unresolved matters.","authorization":"critical decision orchestrator"},
 {"name":"isolated_cloud_terminal","category":"execution","description":"Run bounded commands and package installation in an optional remote isolated sandbox.","authorization":"authenticated owner; sandbox enabled"},
 {"name":"firebase_storage_upload","category":"storage","description":"Upload project input files to the configured Firebase Storage bucket.","authorization":"project owner"},
 {"name":"send_completion_email","category":"notifications","description":"Send project completion results through the configured SMTP relay.","authorization":"project worker"}
]
