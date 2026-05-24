# MedInsight API

Clinical document intelligence platform. Secure ingestion, LLM-powered analysis, and audit-compliant access for healthcare data.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    GitHub Actions CI/CD                  │
│          lint → test → docker build → ECS deploy        │
└─────────────────────┬───────────────────────────────────┘
                      │
              ┌───────▼────────┐
              │  ALB (HTTPS)   │
              └───────┬────────┘
                      │
        ┌─────────────▼──────────────┐
        │   ECS Fargate (FastAPI)    │
        │   2 tasks · auto-scaling   │
        └──┬──────────┬──────────────┘
           │          │
    ┌──────▼──┐  ┌────▼────────┐
    │   S3    │  │  DynamoDB   │
    │ (docs)  │  │ (metadata + │
    │  KMS ↑  │  │  audit logs)│
    └─────────┘  └─────────────┘
           │
    ┌──────▼──────┐   ┌──────────────┐
    │ CloudTrail  │   │  OpenAI API  │
    │ (audit log) │   │ (GPT-4o)     │
    └─────────────┘   └──────────────┘
```

## Tech stack

| Layer | Technology |
|---|---|
| API | Python 3.11, FastAPI, Pydantic v2 |
| AI | OpenAI GPT-4o, LangChain agents |
| Cloud | AWS ECS Fargate, S3, DynamoDB, KMS, CloudTrail |
| IaC | Terraform (modular) |
| Containers | Docker multi-stage, non-root user |
| CI/CD | GitHub Actions (OIDC auth — no long-lived keys) |
| Security | Fernet encryption at rest, API key auth, audit logging |

## Quickstart (local)

```bash
# 1. Clone and install dependencies
git clone <repo>
cd medinsight-api
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env — set OPENAI_API_KEY and generate an ENCRYPTION_KEY:
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 3. Seed synthetic data (optional)
python synthetic_data/seed.py

# 4. Run
uvicorn app.main:app --reload
```

API docs available at http://localhost:8000/docs

## Docker

```bash
docker-compose up
```

To simulate AWS services locally, the compose file includes LocalStack (S3, DynamoDB, KMS).

## API endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/api/v1/documents` | Ingest a clinical document |
| GET | `/api/v1/documents` | List documents (filterable by patient_id) |
| GET | `/api/v1/documents/{id}` | Get document metadata (add `?include_content=true` for decrypted text) |
| POST | `/api/v1/analysis` | Run LLM analysis on a document |
| POST | `/api/v1/agent/query` | Ask the clinical agent a freeform question |
| GET | `/api/v1/audit/logs` | Retrieve audit trail |

All endpoints except `/health` require `X-API-Key` header.

### Example: Ingest + analyze

```bash
# Ingest a document
curl -X POST http://localhost:8000/api/v1/documents \
  -H "X-API-Key: dev-key-change-me-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Patient presents with fever, cough. Assessment: community-acquired pneumonia.",
    "patient_id": "pt-demo-001",
    "document_type": "progress_note"
  }'

# Run full analysis (use doc ID from above)
curl -X POST http://localhost:8000/api/v1/analysis \
  -H "X-API-Key: dev-key-change-me-in-production" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "<id>", "analysis_type": "full_analysis"}'

# Ask the agent
curl -X POST http://localhost:8000/api/v1/agent/query \
  -H "X-API-Key: dev-key-change-me-in-production" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the risk factors for patient pt-demo-001?", "patient_id": "pt-demo-001"}'
```

## Testing

```bash
pytest                    # all tests with coverage
pytest tests/unit/        # unit only (no OpenAI calls)
pytest tests/integration/ # integration
```

## AWS deployment

```bash
cd infrastructure/terraform
terraform init
terraform plan -var="environment=prod"
terraform apply

# Store secrets in SSM Parameter Store before deploying:
aws ssm put-parameter --name /medinsight/openai_api_key --value "sk-..." --type SecureString
aws ssm put-parameter --name /medinsight/api_keys --value "key1,key2" --type SecureString
aws ssm put-parameter --name /medinsight/encryption_key --value "<fernet-key>" --type SecureString

# CI/CD auto-deploys on push to main via GitHub Actions OIDC
# Set AWS_DEPLOY_ROLE_ARN and API_BASE_URL in GitHub repo secrets
```

## Security design

- **Encryption at rest**: Document content encrypted with Fernet (symmetric) before storage; KMS-managed keys in production.
- **Encryption in transit**: HTTPS enforced at ALB; HTTP → HTTPS redirect.
- **Auth**: API key header validated on every request; keys stored in SSM Parameter Store.
- **Audit trail**: Every read/write operation logged with timestamp, actor, resource, and outcome. Stored in DynamoDB + CloudTrail for S3 data-plane events.
- **Least privilege**: ECS task IAM role scoped to specific S3 prefixes and DynamoDB tables only.
- **No long-lived credentials**: GitHub Actions deploys via OIDC role assumption — no AWS keys in CI secrets.
- **Non-root container**: App runs as `appuser` inside Docker.
