# Interactive Live Query Testing Guide

## Quick Start

### Run the Interactive Terminal

```bash
cd sprintobot/backend
python -X utf8 interactive_test.py
```

---

## What You'll See

```
================================================================================
🤖 Sprintobot - Interactive Live Query Testing
================================================================================

Initializing services...
✅ GitHub Service initialized
✅ AI Service ready

================================================================================
📝 INSTRUCTIONS
================================================================================
• Enter your natural language query about GitHub
• Type 'examples' to see sample queries
• Type 'quit' or 'exit' to stop
• Press Ctrl+C to interrupt
================================================================================

--------------------------------------------------------------------------------

🔍 Your query: _
```

---

## Example Session

### 1. Get Sample Queries

```
🔍 Your query: examples

================================================================================
💡 EXAMPLE QUERIES
================================================================================

📂 Simple Queries:
   • Show me my repositories
   • List my repos
   • What repos do I have access to?

📂 PR Queries (with discovery):
   • Show me PRs merged in the last 7 days
   • Get all open PRs
   • Show PRs waiting for review
   • List closed PRs

📂 Time-based Queries:
   • PRs merged in last 14 days
   • PRs waiting for review for 48 hours
   • Recent pull requests

📂 Specific Repository:
   • Get PRs from owner/repo
   • Show merged PRs from microsoft/vscode in last 5 days
   • List open PRs in owner/repo
```

---

### 2. Try a Simple Query

```
🔍 Your query: Show me my repositories

================================================================================
Query #1: Show me my repositories
================================================================================

======================================================================
🎯 Processing Natural Query
======================================================================
📊 Query Complexity: simple
🚀 Using Single-Pass Execution

📋 Executing 1 function call(s)
────────────────────────────────────────────────────────────
🔧 Executing [1/1]: get_authenticated_user_repositories
   Parameters: {}
   ✅ Result: 19 items

======================================================================
📊 Execution Summary:
   Method: single_pass_direct
   Gemini calls: 1
   Function executions: 1
   Efficiency: excellent
   Completed: True
======================================================================

================================================================================
📊 RESULTS
================================================================================

🔧 Execution Details:
   Method: single_pass_direct
   Iterations: 1
   Efficiency: excellent
   Success: True

📋 Function Calls:
   1. get_authenticated_user_repositories({})

📈 Data Retrieved:
   Result 1: 19 items
      - punjab-floods-donation-page
      - ati-mqtt-broker
      - iman_prompts
      ... and 16 more

================================================================================
```

---

### 3. Try a Query with Parameter Discovery

```
🔍 Your query: Show me PRs merged in the last 7 days

================================================================================
Query #2: Show me PRs merged in the last 7 days
================================================================================

======================================================================
🎯 Processing Natural Query
======================================================================
📊 Query Complexity: moderate
🔄 Using Iterative Execution

📋 Executing 2 function call(s)

────────────────────────────────────────────────────────────
🔧 Executing [1/2]: get_authenticated_user_repositories
   Parameters: {}
   ✅ Result: 19 items

────────────────────────────────────────────────────────────
🔧 Executing [2/2]: get_merged_prs_last_n_days
   🔍 Resolving placeholders...
      ⚠️  Found 19 repositories, using most recent: punjab-floods-donation-page
      ↳ Discovered repo: punjab-floods-donation-page
   ✨ Injected parameters: {'n': 7, 'repo': 'punjab-floods-donation-page'}
   ✅ Result: 0 items

================================================================================
📊 RESULTS
================================================================================

🔧 Execution Details:
   Method: iterative
   Iterations: 2
   Efficiency: good
   Success: True

📋 Function Calls:
   1. get_authenticated_user_repositories({})
   2. get_merged_prs_last_n_days({'n': 7, 'repo': 'punjab-floods-donation-page'})

📈 Data Retrieved:
   Result 1: 19 items (repositories)
   Result 2: 0 items (no PRs merged in last 7 days)

================================================================================
```

---

## Available Commands

| Command | Description |
|---------|-------------|
| Any query text | Execute the query against live APIs |
| `examples` | Show sample queries |
| `quit` or `exit` | Exit the session |
| `Ctrl+C` | Interrupt current query |

---

## What to Look For

### ✅ Success Indicators

1. **Parameter Injection Working:**
   ```
   ✨ Injected parameters: {'repo': 'reponame', 'n': 7}
   ```

2. **Iterative Execution:**
   ```
   🔄 Using Iterative Execution
   Step 1: Discovery
   Step 2: Main query with injected params
   ```

3. **Successful Results:**
   ```
   ✅ Result: X items
   Success: True
   ```

---

### ⚠️ Watch For

1. **Repository Selection:**
   ```
   ⚠️  Found 19 repositories, using most recent: reponame
   ```
   This is expected - system auto-selects the most recent repo.

2. **No Data:**
   ```
   Result: 0 items
   ```
   This is normal if there's no data matching your query.

3. **API Errors:**
   ```
   Error: 404 Not Found
   ```
   Usually means the repo doesn't exist or you don't have access.

---

## Sample Test Session

Here's a complete test session to verify all features:

### Test 1: Simple Query
```
Query: Show me my repositories
Expected: Single-pass execution, list of repos
```

### Test 2: Parameter Discovery
```
Query: Get all open PRs
Expected: 2-step execution, parameter injection visible
```

### Test 3: Time-Based Query
```
Query: PRs merged in last 14 days
Expected: Extracts n=14, discovers repo, executes
```

### Test 4: Specific Repository
```
Query: Get PRs from owner/repo
Expected: Single-pass, uses specified repo
```

---

## Tips for Testing

### 1. Start Simple
Begin with:
- "Show me my repositories"
- "List my repos"

### 2. Test Parameter Discovery
Try queries without specifying a repo:
- "Show me PRs"
- "Get open PRs"
- "PRs merged in last 7 days"

### 3. Test Parameter Extraction
Try time-based queries:
- "PRs merged in last 14 days" (should extract n=14)
- "PRs waiting for 48 hours" (should extract hours=48)

### 4. Test Specific Repos
Use actual repos from your GitHub:
- "Get PRs from your-username/your-repo"
- "Show open PRs in owner/repo"

---

## Troubleshooting

### Issue: "AI Service not enabled"
**Solution:** Check your GEMINI_API_KEY in config/.env

### Issue: "GitHub token invalid"
**Solution:** Regenerate token at https://github.com/settings/tokens

### Issue: "No repositories found"
**Solution:** Normal if your GitHub account has no repos

### Issue: "Function X not found"
**Solution:** Check that the integration module is loaded correctly

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Enter` | Submit query |
| `Ctrl+C` | Interrupt current query (can continue after) |
| Type `quit` | Exit gracefully |

---

## Output Explanation

### Execution Details
```
Method: iterative           # How the query was executed
Iterations: 2              # Number of LLM calls
Efficiency: good           # Token efficiency rating
Success: True              # Whether query completed
```

### Function Calls
Shows the actual API functions that were called with their parameters.

### Data Retrieved
Shows what data was returned from each function call.

---

## Advanced Usage

### Chain Multiple Queries

You can run multiple queries in sequence:

```
Query 1: Show me my repositories
Query 2: Get PRs from owner/repo
Query 3: Show PRs merged in last 7 days
```

Each query is independent and fresh.

---

### Compare Execution Methods

Try the same semantic query with different phrasing:

```
Query A: "Show me PRs merged in last 7 days"
  → Iterative execution (needs discovery)

Query B: "Show me PRs merged in last 7 days from owner/repo"
  → Single-pass (repo specified)
```

---

## Exit the Session

Type any of these:
- `quit`
- `exit`
- `q`

Or press `Ctrl+C` and then type `quit`.

---

## Next Steps After Testing

Once you've verified everything works:

1. ✅ Test simple queries
2. ✅ Test parameter discovery
3. ✅ Test parameter injection
4. ✅ Test error handling
5. 🚀 Deploy to production!

---

*Ready to test? Run: `python -X utf8 interactive_test.py`*
