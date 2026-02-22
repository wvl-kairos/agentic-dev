#!/usr/bin/env python3
"""
UserPromptSubmit Hook: Check for Pending Review

This hook runs before Claude processes a user message. If there's a pending
review, it injects the review instructions into the context.

Exit codes:
  0 - No pending review
  2 - Review pending, stdout contains instructions to inject
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
        get_agents_for_files,
        get_threshold,
        set_review_status,
        get_review_state,
        ReviewStatus
    )
except ImportError:
    def get_modified_files():
        log_file = Path('.claude/hooks/modified_files.log')
        if not log_file.exists():
            return []
        return [f for f in log_file.read_text().strip().split('\n') if f]

    def clear_modified_files():
        log_file = Path('.claude/hooks/modified_files.log')
        if log_file.exists():
            log_file.unlink()

    def get_agents_for_files(files):
        return {'frontend-reviewer', 'backend-reviewer', 'security-reviewer', 'performance-reviewer', 'testing-reviewer'}

    def get_threshold():
        return int(os.environ.get('CODE_REVIEW_THRESHOLD', '80'))

    def set_review_status(status, files=None):
        pass

    def get_review_state():
        return {'status': 'idle'}

    class ReviewStatus:
        IDLE = 'idle'
        REVIEWING = 'reviewing'


def generate_review_prompt(files: list, agents: set, threshold: int) -> str:
    """Generate the prompt for the review orchestrator."""

    files_list = '\n'.join(f'- {f}' for f in files)
    agents_list = ', '.join(sorted(agents))

    return f"""
<auto-review-triggered>
## Automatic Code Review

The following files have been modified and need review before continuing:

{files_list}

**IMPORTANT**: Before addressing the user's message, first run a quick code review:

1. Use the Task tool to spawn these reviewers in parallel: {agents_list}
2. Each reviewer should check the files relevant to their specialty
3. Confidence threshold: {threshold}
4. After collecting findings, present a brief summary
5. Then proceed to address the user's original message

If there are critical issues, mention them prominently. For warnings/suggestions, list them briefly.
</auto-review-triggered>

"""


def main():
    try:
        # Use CLAUDE_PROJECT_DIR if available, otherwise try current directory
        project_dir = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())
        pending_file = Path(project_dir) / '.claude' / 'hooks' / 'review_pending.flag'

        print(f"[check-pending-review] Checking for flag at: {pending_file}", file=sys.stderr)

        # Check if there's a pending review
        if not pending_file.exists():
            sys.exit(0)

        # Read the pending files
        pending_content = pending_file.read_text().strip()
        if not pending_content:
            pending_file.unlink()
            sys.exit(0)

        # Get the files from the flag (or from modified_files.log)
        files = get_modified_files()
        if not files:
            # Use files from the flag
            files = [f for f in pending_content.split('\n') if f]

        if not files:
            pending_file.unlink()
            sys.exit(0)

        # Check review state
        state = get_review_state()
        status = state.get('status', ReviewStatus.IDLE)

        if status != ReviewStatus.IDLE:
            # Already in a review cycle, skip
            pending_file.unlink()
            sys.exit(0)

        # Determine which agents to use
        agents = get_agents_for_files(files)
        if not agents:
            pending_file.unlink()
            sys.exit(0)

        # Get configuration
        threshold = get_threshold()

        # Set status to REVIEWING
        set_review_status(ReviewStatus.REVIEWING, files)

        # Generate the review prompt
        prompt = generate_review_prompt(files, agents, threshold)

        print(f"[check-pending-review] FOUND PENDING REVIEW! Files: {files}", file=sys.stderr)
        print(f"[check-pending-review] Agents: {agents}", file=sys.stderr)
        print(f"[check-pending-review] Generating prompt ({len(prompt)} chars)", file=sys.stderr)

        # Clear the pending flag and modified files
        pending_file.unlink()
        clear_modified_files()

        # Output the prompt to stdout - this gets injected into context
        print(prompt)

        print(f"[check-pending-review] Prompt sent to stdout", file=sys.stderr)

        sys.exit(0)

    except Exception as e:
        print(f"[check-pending-review] Error: {e}", file=sys.stderr)
        sys.exit(0)  # Don't block on errors


if __name__ == '__main__':
    main()
