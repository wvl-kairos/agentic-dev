# Code Review Patterns Skill

This skill provides common code review patterns and anti-patterns for the multi-agent code review system.

## Usage

This skill is auto-loaded by the review agents. It provides:
- Common anti-patterns to detect
- Severity classification guidelines
- Language-specific patterns
- Project-specific rules (customizable section at the bottom)

---

## Universal Anti-Patterns

### 1. Magic Numbers/Strings
**Severity**: Warning
**Languages**: All

```javascript
// BAD
if (status === 3) { ... }
setTimeout(fn, 86400000);

// GOOD
const STATUS_APPROVED = 3;
const ONE_DAY_MS = 24 * 60 * 60 * 1000;
if (status === STATUS_APPROVED) { ... }
setTimeout(fn, ONE_DAY_MS);
```

### 2. Deep Nesting
**Severity**: Warning
**Threshold**: > 3 levels

```javascript
// BAD - 4+ levels of nesting
if (a) {
  if (b) {
    if (c) {
      if (d) {
        // Hard to follow
      }
    }
  }
}

// GOOD - Early returns
if (!a) return;
if (!b) return;
if (!c) return;
if (!d) return;
// Clear logic
```

### 3. Function Length
**Severity**: Warning
**Threshold**: > 50 lines (configurable)

Long functions should be broken into smaller, focused functions.

### 4. Parameter Count
**Severity**: Suggestion
**Threshold**: > 4 parameters

```javascript
// BAD
function createUser(name, email, age, role, department, manager, startDate) { }

// GOOD
function createUser(userData: CreateUserInput) { }
```

### 5. Comment Smells
**Severity**: Suggestion

```javascript
// BAD - Commented out code
// const oldImplementation = () => { ... };

// BAD - Obvious comments
i++; // increment i

// BAD - TODO without context
// TODO: fix this

// GOOD - Explains WHY not WHAT
// We use setTimeout(0) here to defer execution until after
// the current event loop, ensuring DOM updates are complete
setTimeout(handler, 0);
```

---

## JavaScript/TypeScript Specific

### 6. Any Type Usage
**Severity**: Warning (TypeScript)

```typescript
// BAD
function processData(data: any): any { }

// GOOD
function processData(data: UserInput): ProcessedResult { }
```

### 7. Inconsistent Async Patterns
**Severity**: Warning

```javascript
// BAD - mixing callbacks and promises
function fetchData(callback) {
  return fetch(url).then(r => {
    callback(null, r);
    return r;
  });
}

// GOOD - consistent async/await
async function fetchData() {
  return await fetch(url);
}
```

### 8. Unhandled Promise Rejection
**Severity**: Critical

```javascript
// BAD
async function doWork() {
  someAsyncOperation(); // Missing await or .catch()
}

// GOOD
async function doWork() {
  await someAsyncOperation();
  // or
  someAsyncOperation().catch(handleError);
}
```

### 9. Console Statements in Production
**Severity**: Warning

```javascript
// BAD
console.log('debug:', data);

// GOOD - use proper logging
logger.debug('Processing data', { data });
```

---

## React Specific

### 10. Missing useCallback/useMemo Dependencies
**Severity**: Warning

```jsx
// BAD - missing dependency
const callback = useCallback(() => {
  doSomething(value);
}, []); // value should be in deps

// GOOD
const callback = useCallback(() => {
  doSomething(value);
}, [value]);
```

### 11. State Updates in Render
**Severity**: Critical

```jsx
// BAD - causes infinite loop
function Component() {
  const [count, setCount] = useState(0);
  setCount(count + 1); // BAD!
  return <div>{count}</div>;
}

// GOOD
function Component() {
  const [count, setCount] = useState(0);
  const increment = () => setCount(c => c + 1);
  return <button onClick={increment}>{count}</button>;
}
```

### 12. Missing Key in Lists
**Severity**: Critical

```jsx
// BAD
items.map(item => <Item {...item} />)

// GOOD
items.map(item => <Item key={item.id} {...item} />)
```

---

## Security Patterns

### 13. SQL Injection
**Severity**: Critical

```javascript
// BAD
const query = `SELECT * FROM users WHERE id = ${userId}`;

// GOOD
const query = 'SELECT * FROM users WHERE id = $1';
await db.query(query, [userId]);
```

### 14. XSS via innerHTML
**Severity**: Critical

```javascript
// BAD
element.innerHTML = userInput;
// In React:
<div dangerouslySetInnerHTML={{ __html: userInput }} />

// GOOD
element.textContent = userInput;
// In React:
<div>{userInput}</div>
```

### 15. Hardcoded Secrets
**Severity**: Critical

```javascript
// BAD
const API_KEY = 'sk-abc123...';
const password = 'admin123';

// GOOD
const API_KEY = process.env.API_KEY;
```

---

## Performance Patterns

### 16. N+1 Query
**Severity**: Critical

```javascript
// BAD
const users = await User.findAll();
for (const user of users) {
  user.profile = await Profile.findByUserId(user.id);
}

// GOOD
const users = await User.findAll({ include: [Profile] });
```

### 17. Unnecessary Re-renders
**Severity**: Warning (React)

```jsx
// BAD - creates new object every render
<Component style={{ color: 'red' }} />

// GOOD - stable reference
const style = useMemo(() => ({ color: 'red' }), []);
<Component style={style} />
```

---

## Project-Specific Rules

### Custom Rules Section

Add your project-specific rules below. These will be checked by all reviewers.

```yaml
# Example custom rules (edit this section)

banned_patterns:
  - pattern: "console.log"
    message: "Use logger instead of console.log"
    severity: warning
    
  - pattern: "TODO"
    message: "TODOs should have a ticket reference"
    severity: suggestion
    
required_patterns:
  - file_pattern: "src/api/**/*.ts"
    must_contain: "validateInput"
    message: "API handlers must validate input"
    severity: warning

naming_conventions:
  components: PascalCase
  hooks: useCamelCase
  constants: UPPER_SNAKE_CASE
  files:
    components: PascalCase.tsx
    hooks: use*.ts
    utils: camelCase.ts

max_file_lines: 500
max_function_lines: 50
max_nesting_depth: 3
```

---

## Severity Reference

| Severity | When to Use | Action Required |
|----------|-------------|-----------------|
| **Critical** | Security vulnerabilities, data corruption risks, crashes | Must fix before merge |
| **Warning** | Performance issues, maintainability problems, inconsistencies | Should fix before merge |
| **Suggestion** | Style improvements, optional optimizations, documentation | Consider for future |

---

## Confidence Score Guidelines

| Confidence | Meaning |
|------------|---------|
| 90-100 | Definite issue, clear violation of best practice |
| 80-89 | Very likely an issue, should be reviewed |
| 70-79 | Possible issue, may depend on context |
| 60-69 | Suspicious, worth investigating |
| < 60 | Uncertain, only flag if critical severity |
