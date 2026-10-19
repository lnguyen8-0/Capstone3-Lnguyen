# Capstone Unit 3

## Validation Outputs for Bronze Step 1

Validating whether the RDS endpoints are reachable. Running following query:

```
(venv) du_356063-1790187761@U-3A4DVVZQ1BTTJ:~/code/ga/lectures/sql-agent/Capstone3-Lnguyen$ python3 -c "
import os; from dotenv import load_dotenv; load_dotenv()
import psycopg2
conn = psycopg2.connect(host=os.getenv('RDS_HOST'), port=os.getenv('RDS_PORT'), dbname=os.getenv('RDS_DATABASE'), user=os.getenv('RDS_USER'), password=os.getenv('RDS_PASSWORD'))
cur = conn.cursor()
for t in ['clients','projects','consultants','invoices']:
    cur.execute(f'SELECT COUNT(*) FROM {t}'); print(t, cur.fetchone()[0])
"
clients 5
projects 6
consultants 6
invoices 7
```

We connected to the RDS and can query the clients, projects consulstants and invoices.

Second, OpenSearch is accessible:

```
(venv) du_356063-1790187761@U-3A4DVVZQ1BTTJ:~/code/ga/lectures/sql-agent/Capstone3-Lnguyen$ python3 -c "                                     
import os, boto3; from dotenv import load_dotenv; load_dotenv()
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
creds = boto3.Session().get_credentials()
auth = AWS4Auth(creds.access_key, creds.secret_key, 'us-east-1', 'es', session_token=creds.token)
client = OpenSearch(hosts=[{'host': os.getenv('OPENSEARCH_ENDPOINT'), 'port': 443}], http_auth=auth, use_ssl=True, verify_certs=True, connection_class=RequestsHttpConnection)
print(client.count(index='documents'))
"
{'count': 8, '_shards': {'total': 5, 'successful': 5, 'skipped': 0, 'failed': 0}}
```

We see the documents are readable. 

**Step 1 result: PASSED** — RDS returns rows from all 4 tables; OpenSearch `documents` index has 8 documents.

---

## Validation Outputs for Bronze Step 2

Both agents must return exactly the keys: `success`, `answer`, `sources`, `metadata`.

Running the following to check:

```python
from dotenv import load_dotenv; load_dotenv()
from agents.sql_agent import run_sql_agent
from agents.retrieval_agent import run_retrieval_agent

sql = run_sql_agent('How many active projects do we have?')
ret = run_retrieval_agent('What is our onboarding process?')

print('sql_agent keys:       ', sorted(sql.keys()))
print('retrieval_agent keys: ', sorted(ret.keys()))
```

Output:

```
sql_agent keys:        ['answer', 'metadata', 'sources', 'success']
retrieval_agent keys:  ['answer', 'metadata', 'sources', 'success']
```

Both agents return the standardized interface. Fix applied: `retrieval_agent.py` was updated to read `OPENSEARCH_ENDPOINT` from `.env` instead of a hardcoded endpoint.

**Step 2 result: PASSED** — both `run_sql_agent` and `run_retrieval_agent` return exactly `success`, `answer`, `sources`, `metadata`.

---

## Validation Outputs for Bronze Step 3

The tool registry (`tool_registery.py`) registers both agents with specific descriptions that say what each tool is for and what it is not for.

**`sql_agent` description:**
> Use for questions that require querying the relational database: counts, totals, filters, aggregations, and lookups against the clients, projects, consultants, and invoices tables. Do NOT use for policy questions, process descriptions, guidelines, or any question whose answer lives in a document rather than a database row.

**`retrieval_agent` description:**
> Use for questions answered by searching indexed documents: policies, procedures, onboarding guides, case studies, and narrative content. Do NOT use for questions about specific records, numbers, counts, budgets, statuses, or anything retrievable from the relational database tables.

The registry also exposes `get_all_schemas()` to return all tool descriptions and `call_tool(name, question)` to invoke a tool by name.

**Step 3 result: PASSED** — both descriptions name what each tool is for and what it is not for.

---

## Validation Outputs for Bronze Step 4

The LangGraph orchestrator routes questions through a linear pipeline:

```
router → sql_agent → retrieval_agent → synthesiser → END
```

Routing is keyword-based. The router sets `route` to `"sql"`, `"retrieval"`, or `"both"`. Each agent node checks `route` and skips itself if not needed. The synthesiser combines whatever results are present into one cited answer.

**Test 1 — SQL-only question:**
```
Q: How many active projects do we have?
Route: sql
Answer: You currently have 4 active projects.
Source: SQL Agent (SELECT COUNT(*) FROM projects WHERE status = 'active')
Tokens: {'input': 104, 'output': 67}
```

**Test 2 — Retrieval-only question:**
```
Q: What is our onboarding process?
Route: retrieval
Answer: The customer success owner builds an onboarding plan covering objectives,
        stakeholders, milestones, training, success measures, and escalation paths.
Source: Retrieval Agent | Capstone2_Company.pdf
Tokens: {'input': 297, 'output': 331}
```

**Test 3 — Both sources needed:**
```
Q: How many active projects do we have, and what's our onboarding policy?
Route: both
Answer: 4 active projects (SQL Agent, projects table) + onboarding policy
        (Retrieval Agent, Capstone2_Company.pdf) — both sources cited.
Tokens: {'input': 510, 'output': 347}
```

**Step 4 result: PASSED** — single-tool and multi-tool routing both work; synthesis attributes results to each agent.

---

## Validation Outputs for Bronze Step 5

SQL validation is enforced in `execute_query_safely()` in `agents/sql_agent.py` — there is no path to the database that skips `validate_sql()`.

Test suite run against `validate_sql()`:

```
[PASS] Valid SELECT
       Query:    SELECT * FROM clients WHERE status = 'active'
       Expected: ALLOW | Got: ALLOW | Reason: OK

[PASS] Destructive DELETE
       Query:    DELETE FROM clients WHERE id = 1
       Expected: BLOCK | Got: BLOCK | Reason: Blocked: 'DELETE' is not permitted. Only SELECT queries are allowed.

[PASS] Column named deleted_at
       Query:    SELECT id, deleted_at FROM clients
       Expected: ALLOW | Got: ALLOW | Reason: OK

[PASS] Stacked with blocked keyword
       Query:    SELECT * FROM clients; DROP TABLE clients
       Expected: BLOCK | Got: BLOCK | Reason: Blocked: 'DROP' is not permitted. Only SELECT queries are allowed.

[PASS] Stacked two SELECTs
       Query:    SELECT * FROM clients; SELECT * FROM projects
       Expected: BLOCK | Got: BLOCK | Reason: Blocked: multiple statements detected (possible stacked query attempt).

All tests passed!
```

**Step 5 result: PASSED** — all 5 required cases pass, including whole-word matching (case 3) and independent stacking check (case 5).

