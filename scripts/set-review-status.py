#!/usr/bin/env python3
"""
Utility script to set the review status.

Usage:
    python3 set-review-status.py <status>

Where <status> is one of:
    idle              - Reset to idle, ready for new review cycle
    reviewing         - Review is in progress
    awaiting_approval - Review done, waiting for user decision
    fixing            - User approved fixes, applying them
    completed         - Review cycle complete

Example:
    python3 set-review-status.py fixing
    python3 set-review-status.py completed
    python3 set-review-status.py idle
"""

import sys
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent / 'utils'))

try:
    from file_tracker import set_review_status, get_review_state, ReviewStatus
except ImportError:
    print("Error: Could not import file_tracker utilities", file=sys.stderr)
    sys.exit(1)


VALID_STATUSES = {
    'idle': ReviewStatus.IDLE,
    'reviewing': ReviewStatus.REVIEWING,
    'awaiting_approval': ReviewStatus.AWAITING_APPROVAL,
    'fixing': ReviewStatus.FIXING,
    'completed': ReviewStatus.COMPLETED,
}


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 set-review-status.py <status>", file=sys.stderr)
        print(f"Valid statuses: {', '.join(VALID_STATUSES.keys())}", file=sys.stderr)
        sys.exit(1)

    status_arg = sys.argv[1].lower()

    if status_arg not in VALID_STATUSES:
        print(f"Error: Invalid status '{status_arg}'", file=sys.stderr)
        print(f"Valid statuses: {', '.join(VALID_STATUSES.keys())}", file=sys.stderr)
        sys.exit(1)

    # Get current state for comparison
    old_state = get_review_state()
    old_status = old_state.get('status', 'unknown')

    # Set new status
    new_status = VALID_STATUSES[status_arg]
    set_review_status(new_status)

    print(f"Review status changed: {old_status} -> {new_status}")


if __name__ == '__main__':
    main()
