#!/usr/bin/env python3
"""
Stop Hook: Mark Review Pending

This hook runs when Claude finishes working. It checks if there are modified
files and marks that a review is pending (to be triggered on next user message).

Exit codes:
  0 - Success (no action needed or review marked as pending)
  1 - Error
"""

import sys
import os
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent / 'utils'))

try:
    from file_tracker import (
        get_modified_files,
        should_auto_review,
        get_review_state,
        ReviewStatus
    )
except ImportError:
    def get_modified_files():
        log_file = Path('.claude/hooks/modified_files.log')
        if not log_file.exists():
            return []
        return [f for f in log_file.read_text().strip().split('\n') if f]

    def should_auto_review():
        return bool(get_modified_files())

    def get_review_state():
        return {'status': 'idle'}

    class ReviewStatus:
        IDLE = 'idle'
        REVIEWING = 'reviewing'


def main():
    try:
        # Check if auto-review is enabled
        if os.environ.get('AUTO_REVIEW_ENABLED', 'true').lower() in ('false', '0', 'no'):
            sys.exit(0)

        # Check current review state - prevent infinite loops
        state = get_review_state()
        status = state.get('status', ReviewStatus.IDLE)

        if status != ReviewStatus.IDLE:
            # Already in a review cycle
            sys.exit(0)

        # Check for modified files
        if not should_auto_review():
            sys.exit(0)

        files = get_modified_files()
        if not files:
            sys.exit(0)

        # Mark review as pending by creating a flag file
        # Use CLAUDE_PROJECT_DIR if available, otherwise try to find .claude directory
        project_dir = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())
        pending_file = Path(project_dir) / '.claude' / 'hooks' / 'review_pending.flag'
        pending_file.parent.mkdir(parents=True, exist_ok=True)
        pending_file.write_text('\n'.join(files))
        print(f"[mark-review-pending] Flag created at: {pending_file}", file=sys.stderr)

        # Show feedback to user
        print(f"[auto-review] {len(files)} file(s) modified. Review will run on your next message.", file=sys.stderr)

        sys.exit(0)

    except Exception as e:
        print(f"[mark-review-pending] Error: {e}", file=sys.stderr)
        sys.exit(0)  # Don't block on errors


if __name__ == '__main__':
    main()
