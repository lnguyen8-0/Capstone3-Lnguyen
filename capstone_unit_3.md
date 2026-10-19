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

