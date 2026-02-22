"""
File tracking utilities for the multi-agent code review system.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Set

# Configuration
LOG_DIR = Path(os.environ.get('CLAUDE_PROJECT_DIR', '.')) / '.claude' / 'hooks'
MODIFIED_FILES_LOG = LOG_DIR / 'modified_files.log'
REVIEW_STATE_FILE = LOG_DIR / 'review_state.json'
DEBUG_LOG_FILE = LOG_DIR / 'hooks_debug.log'


def debug_log(message: str, source: str = "file_tracker"):
    """Write a debug message to the hooks debug log."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        with open(DEBUG_LOG_FILE, 'a') as f:
            f.write(f"[{timestamp}] [{source}] {message}\n")
    except Exception:
        pass  # Don't let debug logging break anything

# Patterns to ignore
IGNORE_PATTERNS = [
    'node_modules/',
    'dist/',
    'build/',
    '.next/',
    '.git/',
    '__pycache__/',
    '*.min.js',
    '*.bundle.js',
    '*.map',
    'package-lock.json',
    'yarn.lock',
    'pnpm-lock.yaml',
    '*.pyc',
    '.env*',
    'coverage/',
]


def should_ignore(filepath: str) -> bool:
    """Check if a file should be ignored for review."""
    filepath_lower = filepath.lower()
    
    for pattern in IGNORE_PATTERNS:
        if pattern.endswith('/'):
            # Directory pattern
            if pattern[:-1] in filepath_lower:
                return True
        elif pattern.startswith('*'):
            # Extension pattern
            if filepath_lower.endswith(pattern[1:]):
                return True
        else:
            # Exact match
            if pattern in filepath_lower:
                return True
    
    return False


def ensure_log_dir():
    """Ensure the log directory exists."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def add_modified_file(filepath: str) -> bool:
    """Add a file to the modified files log."""
    if should_ignore(filepath):
        return False
    
    ensure_log_dir()
    
    # Read existing files
    existing = set()
    if MODIFIED_FILES_LOG.exists():
        existing = set(MODIFIED_FILES_LOG.read_text().strip().split('\n'))
        existing.discard('')  # Remove empty strings
    
    # Add new file
    existing.add(filepath)
    
    # Write back
    MODIFIED_FILES_LOG.write_text('\n'.join(sorted(existing)))
    return True


def get_modified_files() -> List[str]:
    """Get list of modified files since last review."""
    if not MODIFIED_FILES_LOG.exists():
        return []
    
    files = MODIFIED_FILES_LOG.read_text().strip().split('\n')
    return [f for f in files if f and not should_ignore(f)]


def clear_modified_files():
    """Clear the modified files log (after review)."""
    if MODIFIED_FILES_LOG.exists():
        MODIFIED_FILES_LOG.unlink()


class ReviewStatus:
    """Review status constants."""
    IDLE = 'idle'                       # No review in progress, tracking new changes
    REVIEWING = 'reviewing'             # Review is running
    AWAITING_APPROVAL = 'awaiting_approval'  # Review done, waiting for user decision
    FIXING = 'fixing'                   # User approved fixes, applying them
    COMPLETED = 'completed'             # Review cycle complete, ignoring changes to reviewed files


def get_review_state() -> dict:
    """Get the current review state."""
    if not REVIEW_STATE_FILE.exists():
        return {
            'status': ReviewStatus.IDLE,
            'last_review': None,
            'review_count': 0,
            'reviewed_files': [],       # Files reviewed in current cycle
            'pending_files': [],        # New files waiting for review
            'session_id': None          # Unique ID for this review cycle
        }

    try:
        state = json.loads(REVIEW_STATE_FILE.read_text())
        # Ensure all fields exist (backward compatibility)
        state.setdefault('status', ReviewStatus.IDLE)
        state.setdefault('reviewed_files', state.get('files_reviewed', []))
        state.setdefault('pending_files', [])
        state.setdefault('session_id', None)
        return state
    except (json.JSONDecodeError, IOError):
        return {
            'status': ReviewStatus.IDLE,
            'last_review': None,
            'review_count': 0,
            'reviewed_files': [],
            'pending_files': [],
            'session_id': None
        }


def save_review_state(state: dict):
    """Save the review state."""
    ensure_log_dir()
    REVIEW_STATE_FILE.write_text(json.dumps(state, indent=2))


def set_review_status(status: str, files: List[str] = None):
    """Update the review status."""
    import uuid

    state = get_review_state()
    old_status = state.get('status', ReviewStatus.IDLE)
    state['status'] = status

    if status == ReviewStatus.REVIEWING:
        # Starting a new review
        state['session_id'] = str(uuid.uuid4())[:8]
        state['reviewed_files'] = files or []
        state['last_review'] = datetime.now().isoformat()
        state['review_count'] = state.get('review_count', 0) + 1

    elif status == ReviewStatus.AWAITING_APPROVAL:
        # Review finished, waiting for user
        pass

    elif status == ReviewStatus.FIXING:
        # User approved fixes
        pass

    elif status == ReviewStatus.COMPLETED:
        # Review cycle complete
        pass

    elif status == ReviewStatus.IDLE:
        # Reset for new cycle
        state['reviewed_files'] = []
        state['pending_files'] = []
        state['session_id'] = None

    save_review_state(state)
    return state


def is_file_already_reviewed(filepath: str) -> bool:
    """Check if a file was already reviewed in the current cycle."""
    state = get_review_state()
    status = state.get('status', ReviewStatus.IDLE)

    # If we're in a review cycle, check if file was already reviewed
    if status in (ReviewStatus.REVIEWING, ReviewStatus.AWAITING_APPROVAL,
                  ReviewStatus.FIXING, ReviewStatus.COMPLETED):
        reviewed = state.get('reviewed_files', [])
        return filepath in reviewed

    return False


def should_track_file(filepath: str) -> bool:
    """
    Determine if a file modification should be tracked for review.

    Returns False if:
    - File should be ignored (node_modules, etc.)
    - File was already reviewed in current cycle and we're applying fixes
    """
    if should_ignore(filepath):
        return False

    state = get_review_state()
    status = state.get('status', ReviewStatus.IDLE)

    # If we're fixing or completed, don't track changes to already-reviewed files
    if status in (ReviewStatus.FIXING, ReviewStatus.COMPLETED):
        if is_file_already_reviewed(filepath):
            return False

    return True


def update_review_state(files_reviewed: List[str]):
    """Update the review state after a review (legacy compatibility)."""
    set_review_status(ReviewStatus.AWAITING_APPROVAL, files_reviewed)


def reset_review_cycle():
    """Reset the review cycle to idle state."""
    set_review_status(ReviewStatus.IDLE)


def should_auto_review() -> bool:
    """Determine if auto-review should run."""
    # Check if there are modified files
    files = get_modified_files()
    if not files:
        return False
    
    # Check if auto-review is enabled
    auto_review_enabled = os.environ.get('AUTO_REVIEW_ENABLED', 'true').lower()
    if auto_review_enabled in ('false', '0', 'no'):
        return False
    
    return True


def get_threshold() -> int:
    """Get the confidence threshold for review findings."""
    return int(os.environ.get('CODE_REVIEW_THRESHOLD', '80'))


def classify_files(files: List[str]) -> dict:
    """Classify files by type for agent selection."""
    classification = {
        'frontend': [],
        'backend': [],
        'security': [],
        'testing': [],
        'performance': [],
        'config': []
    }

    # File extension patterns
    frontend_extensions = ['.tsx', '.jsx', '.vue', '.svelte', '.css', '.scss', '.sass', '.less']
    code_extensions = ['.ts', '.js', '.py', '.go', '.java', '.rb', '.php', '.rs', '.c', '.cpp', '.cs']
    config_extensions = ['.json', '.yaml', '.yml', '.toml', '.ini', '.xml', '.env.example']
    infra_files = ['dockerfile', 'docker-compose', '.dockerignore', 'makefile', 'rakefile']
    query_extensions = ['.sql', '.graphql', '.gql', '.prisma']

    # Path patterns
    backend_patterns = ['/api/', '/server/', '/backend/', '/db/', '/database/', '/models/', '/services/', '/controllers/']
    security_patterns = ['/auth/', '/login/', '/security/', '/crypto/', '/password/', '/oauth/', '/jwt/', '/token/']
    test_patterns = ['.test.', '.spec.', '__tests__/', '/test/', '/tests/', '_test.', 'test_']
    ci_patterns = ['.github/', '.gitlab-ci', 'jenkins', '.circleci/', 'azure-pipelines']

    # Sensitive config files (always need security review)
    sensitive_configs = ['.env', 'secrets', 'credentials', 'config.prod', 'database.yml', 'settings.py']

    for filepath in files:
        filepath_lower = filepath.lower()
        filename = filepath_lower.split('/')[-1]

        # Check test files first (highest priority)
        # Only check filename and immediate parent directory, not full path
        parent_dir = filepath_lower.split('/')[-2] if '/' in filepath_lower else ''
        is_test_file = (
            any(p in filename for p in ['.test.', '.spec.', '_test.', 'test_']) or
            parent_dir in ['__tests__', 'test', 'tests', 'spec', 'specs']
        )
        if is_test_file:
            classification['testing'].append(filepath)
            continue

        # Check security-related paths
        is_security = any(p in filepath_lower for p in security_patterns)

        # Check sensitive config files (security review needed)
        is_sensitive_config = any(s in filepath_lower for s in sensitive_configs)

        if is_security or is_sensitive_config:
            classification['security'].append(filepath)
            # Also add to backend if it's code
            if any(filepath_lower.endswith(ext) for ext in code_extensions):
                classification['backend'].append(filepath)
                classification['performance'].append(filepath)
            continue

        # Check frontend files
        if any(filepath_lower.endswith(ext) for ext in frontend_extensions):
            classification['frontend'].append(filepath)
            classification['performance'].append(filepath)  # Frontend perf matters too
            continue

        # Check CI/CD and infrastructure files
        if any(p in filepath_lower for p in ci_patterns) or any(f in filename for f in infra_files):
            classification['config'].append(filepath)
            classification['security'].append(filepath)  # CI/CD configs can have secrets
            continue

        # Check query/schema files (SQL, GraphQL, Prisma)
        if any(filepath_lower.endswith(ext) for ext in query_extensions):
            classification['backend'].append(filepath)
            classification['security'].append(filepath)  # SQL injection potential
            classification['performance'].append(filepath)  # Query performance
            continue

        # Check config files
        if any(filepath_lower.endswith(ext) for ext in config_extensions):
            classification['config'].append(filepath)
            classification['backend'].append(filepath)  # Backend reviews configs too
            continue

        # Check backend-specific paths
        if any(p in filepath_lower for p in backend_patterns):
            classification['backend'].append(filepath)
            classification['performance'].append(filepath)
            continue

        # Generic code files go to backend + performance
        if any(filepath_lower.endswith(ext) for ext in code_extensions):
            classification['backend'].append(filepath)
            classification['performance'].append(filepath)
            continue

        # Remaining files: if they look like code/config, still review them
        # This catches things like shell scripts, makefiles without extension, etc.
        if '.' not in filename or filename.startswith('.'):
            # Files without extension or dotfiles - likely config
            classification['config'].append(filepath)

    return classification


def get_agents_for_files(files: List[str]) -> Set[str]:
    """Determine which agents should review based on file types."""
    classification = classify_files(files)
    agents = set()

    if classification['frontend']:
        agents.add('frontend-reviewer')

    if classification['backend'] or classification['config']:
        agents.add('backend-reviewer')

    if classification['security']:
        agents.add('security-reviewer')

    if classification['performance']:
        agents.add('performance-reviewer')

    # Include testing reviewer if there are code files that could have tests
    has_code = (classification['frontend'] or classification['backend'] or
                classification['security'] or classification['performance'])
    if has_code:
        agents.add('testing-reviewer')

    return agents


def get_files_for_agent(files: List[str], agent: str) -> List[str]:
    """Get the specific files that an agent should review."""
    classification = classify_files(files)

    agent_mapping = {
        'frontend-reviewer': classification['frontend'],
        'backend-reviewer': list(set(classification['backend'] + classification['config'])),
        'security-reviewer': classification['security'],
        'performance-reviewer': classification['performance'],
        'testing-reviewer': list(set(
            classification['frontend'] + classification['backend'] +
            classification['security'] + classification['performance']
        ))
    }

    return agent_mapping.get(agent, files)


if __name__ == '__main__':
    # Test the utilities
    print("Testing file tracker utilities...")
    
    test_files = [
        'src/components/UserCard.tsx',
        'src/api/users.ts',
        'src/auth/login.ts',
        'src/utils/helpers.test.ts',
        'node_modules/lodash/index.js',
    ]
    
    for f in test_files:
        print(f"  {f}: ignored={should_ignore(f)}")
    
    print("\nClassification:")
    classification = classify_files([f for f in test_files if not should_ignore(f)])
    for category, files in classification.items():
        if files:
            print(f"  {category}: {files}")
    
    print("\nAgents to use:")
    agents = get_agents_for_files([f for f in test_files if not should_ignore(f)])
    print(f"  {agents}")
