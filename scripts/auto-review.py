#!/usr/bin/env python3
"""
Stop Hook: Auto Code Review

Runs when Claude finishes working. If there are modified files, outputs
review instructions to STDERR and exits with code 2 to force Claude
to continue working (perform the review).

Exit codes:
  0 - No review needed (no modified files or already reviewing)
  2 - Review needed (stderr contains instructions, forces Claude to act)
"""

import sys
import os
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent / 'utils'))

try:
    from file_tracker import (
        get_modified_files,
        clear_modified_files,
        should_auto_review,
        get_agents_for_files,
        get_threshold,
        get_review_state,
        set_review_status,
        ReviewStatus
    )
except ImportError:
    # Minimal fallback
    def get_modified_files():
        project_dir = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())
        log_file = Path(project_dir) / '.claude' / 'hooks' / 'modified_files.log'
        if not log_file.exists():
            return []
        return [f for f in log_file.read_text().strip().split('\n') if f]

    def clear_modified_files():
        project_dir = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())
        log_file = Path(project_dir) / '.claude' / 'hooks' / 'modified_files.log'
        if log_file.exists():
            log_file.unlink()

    def should_auto_review():
        return bool(get_modified_files())

    def get_agents_for_files(files):
        return {'frontend-reviewer', 'backend-reviewer', 'security-reviewer', 'performance-reviewer', 'testing-reviewer'}

    def get_threshold():
        return int(os.environ.get('CODE_REVIEW_THRESHOLD', '80'))

    def get_review_state():
        return {'status': 'idle'}

    def set_review_status(status, files=None):
        project_dir = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())
        state_file = Path(project_dir) / '.claude' / 'hooks' / 'review_state.json'
        state_file.parent.mkdir(parents=True, exist_ok=True)
        import json
        state_file.write_text(json.dumps({'status': status, 'files': files or []}))

    class ReviewStatus:
        IDLE = 'idle'
        REVIEWING = 'reviewing'


def generate_review_instructions(files: list, agents: set, threshold: int) -> str:
    """Generate review instructions for Claude."""

    files_list = '\n'.join(f'  - {f}' for f in files)
    agents_list = ', '.join(sorted(agents))

    return f"""
## 🔍 Automatic Code Review Required

The following files were modified and need review:

{files_list}

**Execute this review now using the Task tool:**

1. Spawn these specialized reviewers **in parallel** using the Task tool:
   - {agents_list}

2. Each reviewer should analyze the files relevant to their specialty and return findings in this format:
   - Category (security/performance/frontend/backend/testing)
   - Severity (critical/warning/suggestion)
   - File and line number
   - Description of issue
   - Suggested fix

3. After all reviewers complete, consolidate and present findings:
   - Group by severity (Critical → Warning → Suggestion)
   - Only include findings with confidence >= {threshold}%
   - Show code examples for fixes

4. Present summary table:
   | Severity | Count |
   |----------|-------|
   | Critical | X |
   | Warning | X |
   | Suggestion | X |

**Begin the review now.**
"""


def main():
    # Debug: log that we're running
    project_dir = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())
    debug_log = Path(project_dir) / '.claude' / 'hooks' / 'auto_review_debug.log'
    debug_log.parent.mkdir(parents=True, exist_ok=True)
    from datetime import datetime
    with open(debug_log, 'a') as f:
        f.write(f"[{datetime.now()}] auto-review.py started\n")
        f.write(f"  CLAUDE_PROJECT_DIR={project_dir}\n")
        f.write(f"  AUTO_REVIEW_ENABLED={os.environ.get('AUTO_REVIEW_ENABLED', 'not set')}\n")

    # Check if auto-review is enabled (default: TRUE)
    if os.environ.get('AUTO_REVIEW_ENABLED', 'true').lower() in ('false', '0', 'no'):
        with open(debug_log, 'a') as f:
            f.write(f"  -> Disabled, exiting\n")
        sys.exit(0)

    # Check current review state - prevent infinite loops
    state = get_review_state()
    status = state.get('status', ReviewStatus.IDLE)

    with open(debug_log, 'a') as f:
        f.write(f"  Review state: {status}\n")

    if status != ReviewStatus.IDLE:
        with open(debug_log, 'a') as f:
            f.write(f"  -> Already reviewing, exiting\n")
        sys.exit(0)

    # Check for modified files
    if not should_auto_review():
        with open(debug_log, 'a') as f:
            f.write(f"  -> No files to review, exiting\n")
        sys.exit(0)

    files = get_modified_files()
    with open(debug_log, 'a') as f:
        f.write(f"  Modified files: {files}\n")

    if not files:
        with open(debug_log, 'a') as f:
            f.write(f"  -> No files found, exiting\n")
        sys.exit(0)

    # Determine which agents to use
    agents = get_agents_for_files(files)
    with open(debug_log, 'a') as f:
        f.write(f"  Agents: {agents}\n")

    if not agents:
        with open(debug_log, 'a') as f:
            f.write(f"  -> No agents, exiting\n")
        sys.exit(0)

    # Get configuration
    threshold = get_threshold()

    # Set status to REVIEWING to prevent loops
    set_review_status(ReviewStatus.REVIEWING, files)

    # Generate review instructions
    instructions = generate_review_instructions(files, agents, threshold)

    # Clear the modified files log
    clear_modified_files()

    with open(debug_log, 'a') as f:
        f.write(f"  -> TRIGGERING REVIEW! Exit code 2\n")
        f.write(f"  Instructions length: {len(instructions)}\n")

    # Output instructions to STDERR (this is what Claude will receive)
    print(instructions, file=sys.stderr)

    # Exit with code 2 to force Claude to continue working
    sys.exit(2)


if __name__ == '__main__':
    main()
