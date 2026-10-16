"""
Pre-lesson access check for Building a Retrieval Agent.

Run this before the lesson starts to confirm you have everything this
lesson needs: local Sentence Transformers, a reachable OpenSearch domain
with an indexed `documents` index (from this morning's Document Ingestion
Pipeline lesson), and Bedrock access to Claude for answer generation.

Usage:
    python3 validate_access.py
    OPENSEARCH_DOMAIN=my-domain-name python3 validate_access.py   # if your
        domain isn't named "vector-search-lesson"
"""
import os
import sys

OPENSEARCH_DOMAIN = os.environ.get("OPENSEARCH_DOMAIN", "vector-search-lesson")
REGION = "us-east-1"
EXPECTED_DIMENSION = 384  # all-MiniLM-L6-v2

CHECKS_PASSED = []
CHECKS_FAILED = []
_state = {}


def check(name):
    def decorator(fn):
        print(f"Checking: {name} ... ", end="", flush=True)
        try:
            detail = fn()
            print(f"OK{f' ({detail})' if detail else ''}")
            CHECKS_PASSED.append(name)
        except Exception as e:
            print(f"FAILED\n  -> {type(e).__name__}: {e}")
            CHECKS_FAILED.append(name)
        return fn
    return decorator


@check("required packages are installed")
def _():
    import boto3, opensearchpy, requests_aws4auth, sentence_transformers  # noqa: F401
    return None


@check("AWS credentials are configured")
def _():
    import boto3
    identity = boto3.client("sts", region_name=REGION).get_caller_identity()
    return identity["Arn"]


@check(f"OpenSearch domain '{OPENSEARCH_DOMAIN}' exists and is reachable")
def _():
    import boto3
    client = boto3.client("opensearch", region_name=REGION)
    status = client.describe_domain(DomainName=OPENSEARCH_DOMAIN)["DomainStatus"]
    if status.get("Processing"):
        raise RuntimeError("domain exists but is still processing (creating/updating) — wait and retry")
    endpoint = status.get("Endpoint") or (status.get("Endpoints") or {}).get("vpc")
    if not endpoint:
        raise RuntimeError("domain has no endpoint yet")
    _state["endpoint"] = endpoint
    return endpoint


@check("'documents' index exists with a populated knn_vector field")
def _():
    import boto3
    from opensearchpy import OpenSearch, RequestsHttpConnection
    from requests_aws4auth import AWS4Auth

    if "endpoint" not in _state:
        raise RuntimeError("skipped — OpenSearch domain check failed above")

    credentials = boto3.Session().get_credentials()
    auth = AWS4Auth(credentials.access_key, credentials.secret_key, REGION, "es",
                     session_token=credentials.token)
    client = OpenSearch(
        hosts=[{"host": _state["endpoint"], "port": 443}],
        http_auth=auth, use_ssl=True, verify_certs=True,
        connection_class=RequestsHttpConnection,
    )

    mapping = client.indices.get_mapping(index="documents")
    props = mapping["documents"]["mappings"]["properties"]
    dim = props.get("embedding", {}).get("dimension")
    if dim != EXPECTED_DIMENSION:
        raise RuntimeError(
            f"'embedding' field is {dim}-dimensional, expected {EXPECTED_DIMENSION} "
            f"(all-MiniLM-L6-v2) — retrieve() will get a dimension-mismatch error"
        )

    count = client.count(index="documents")["count"]
    if count == 0:
        raise RuntimeError("index exists but has 0 documents — run this morning's ingestion pipeline first")
    return f"{count} document(s) indexed, dimension={dim}"


@check("Sentence Transformers model loads and produces 384-dim vectors")
def _():
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    vec = model.encode("test query").tolist()
    if len(vec) != EXPECTED_DIMENSION:
        raise RuntimeError(f"produced {len(vec)}-dim vector, expected {EXPECTED_DIMENSION}")
    return f"{len(vec)}-dim"


@check("Bedrock inference-profile access (Claude Sonnet 4.6, for answer generation)")
def _():
    import boto3
    import json

    account_id = boto3.client("sts", region_name=REGION).get_caller_identity()["Account"]
    model_id = f"arn:aws:bedrock:us-east-1:{account_id}:inference-profile/us.anthropic.claude-sonnet-4-6"

    bedrock = boto3.client("bedrock-runtime", region_name=REGION)
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 10,
        "messages": [{"role": "user", "content": "Reply with just: ok"}]
    }
    response = bedrock.invoke_model(modelId=model_id, body=json.dumps(body))
    result = json.loads(response["body"].read())
    return f"model responded: {result['content'][0]['text']!r}"


if __name__ == "__main__":
    print()
    print(f"Passed: {len(CHECKS_PASSED)}  Failed: {len(CHECKS_FAILED)}")
    if CHECKS_FAILED:
        print("\nFix the failed checks above before the lesson starts:")
        for name in CHECKS_FAILED:
            print(f"  - {name}")
        sys.exit(1)
    print("\nAll checks passed — you're ready for this lesson.")