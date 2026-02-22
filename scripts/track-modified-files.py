#!/usr/bin/env python3
"""
PostToolUse Hook: Track Modified Files

This hook runs after Edit, Write, or MultiEdit tools to track which files
have been modified. The list is used by the Stop hook to trigger auto-review.

Input (via stdin): JSON with tool_name and tool_input
Output: None (logs to file)
Exit codes:
  0 - Success
  1 - Error (won't block Claude)
"""

import sys
import json
import os
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent / 'utils'))

from datetime import datetime

def debug_log(message: str):
    """Write debug log to file."""
    try:
        log_dir = Path('.claude/hooks')
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / 'hooks_debug.log'
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        with open(log_file, 'a') as f:
            f.write(f"[{timestamp}] [track-files] {message}\n")
    except Exception:
        pass


try:
    from file_tracker import add_modified_file, should_track_file, get_review_state, ReviewStatus
except ImportError:
    # Fallback if utils not available
    def add_modified_file(f):
        log_file = Path('.claude/hooks/modified_files.log')
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, 'a') as f_out:
            f_out.write(f + '\n')
        return True

    def should_track_file(f):
        ignore = ['node_modules/', 'dist/', '.git/', '*.min.js']
        return not any(p.replace('*', '') in f for p in ignore)

    def get_review_state():
        return {'status': 'idle'}

    class ReviewStatus:
        IDLE = 'idle'
        FIXING = 'fixing'
        COMPLETED = 'completed'


def main():
    debug_log("=== POSTTOOLUSE HOOK TRIGGERED ===")

    try:
        # Read hook input from stdin
        input_data = json.load(sys.stdin)
        debug_log(f"Input data: {json.dumps(input_data)[:200]}...")

        tool_name = input_data.get('tool_name', '')
        tool_input = input_data.get('tool_input', {})
        debug_log(f"Tool: {tool_name}")
        
        # Only process file modification tools
        if tool_name not in ['Edit', 'Write', 'MultiEdit']:
            sys.exit(0)
        
        # Extract file path(s)
        files_to_track = []
        
        if tool_name in ['Edit', 'Write']:
            file_path = tool_input.get('file_path') or tool_input.get('path')
            if file_path:
                files_to_track.append(file_path)
        
        elif tool_name == 'MultiEdit':
            edits = tool_input.get('edits', [])
            for edit in edits:
                file_path = edit.get('file_path') or edit.get('path')
                if file_path:
                    files_to_track.append(file_path)
        
        # Track each file (respecting review state)
        state = get_review_state()
        status = state.get('status', 'idle')
        debug_log(f"Review state: status={status}")
        debug_log(f"Files to track: {files_to_track}")

        for file_path in files_to_track:
            if should_track_file(file_path):
                add_modified_file(file_path)
                debug_log(f"TRACKED: {file_path}")
                # Debug logging (optional)
                if os.environ.get('DEBUG_HOOKS'):
                    print(f"[track-modified-files] Tracked: {file_path}", file=sys.stderr)
            else:
                debug_log(f"SKIPPED (status={status}): {file_path}")
                if os.environ.get('DEBUG_HOOKS'):
                    print(f"[track-modified-files] Skipped (status={status}): {file_path}", file=sys.stderr)

        debug_log("=== POSTTOOLUSE HOOK COMPLETE ===")
        sys.exit(0)
        
    except Exception as e:
        # Log error but don't block Claude
        print(f"[track-modified-files] Error: {e}", file=sys.stderr)
        sys.exit(0)  # Exit 0 to not block


if __name__ == '__main__':
    main()
