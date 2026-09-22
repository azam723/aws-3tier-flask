# AWS 3-Tier Flask Application

![AWS](https://img.shields.io/badge/AWS-ECS%20Fargate-orange?logo=amazonaws&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-IaC-844FBA?logo=terraform&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-container-2496ED?logo=docker&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-Python-000000?logo=flask&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)
![OIDC](https://img.shields.io/badge/Auth-GitHub%20OIDC-4B32C3)

A hands-on AWS project: a Flask REST API designed, provisioned, containerized, and deployed on a traditional 3-tier architecture VPC networking, ECS Fargate, RDS PostgreSQL, and S3 with Terraform for infrastructure and keyless GitHub Actions CI/CD via OIDC.

---

## Architecture

<img width="1536" height="1024" alt="ChatGPT Image Sep 18, 2026, 11_44_30 PM" src="https://github.com/user-attachments/assets/4ddc521a-33ff-44a1-a302-0885424a2810" />

```text
Internet → ALB (public) → ECS Fargate (private) → RDS PostgreSQL (private)
                                                 → Amazon S3
```

ECS and RDS sit in private subnets with no public IPs; the ALB is the only public entry point, and outbound traffic from private subnets routes through a NAT Gateway.

## Why this project

Most fresher cloud projects deploy a single service in isolation. This one connects the full stack a real application needs — networking, compute, database, object storage, secrets, and CI/CD — and does it with the same security posture a production system would need: private compute, no long-lived AWS credentials in CI, and secrets pulled from Secrets Manager rather than hardcoded.

## What was built

| Layer | Components |
|---|---|
| **Networking** | VPC (`10.0.0.0/16`), public + private subnets across 2 AZs, NAT Gateway, security-group chaining (ALB → ECS → RDS) |
| **Compute** | ECS Fargate running a containerized Flask API (Gunicorn), no public IP on tasks |
| **Data** | RDS PostgreSQL (private, not internet-accessible) + Amazon S3 (private, `BucketOwnerEnforced`) |
| **Secrets & IAM** | Credentials in AWS Secrets Manager, IAM task roles instead of access keys |
| **CI/CD** | GitHub Actions → OIDC → ECR → ECS rolling deployment |
| **Observability** | CloudWatch Logs, ECS Exec for live debugging |

## API

```text
GET  /health              → checks DB connectivity, used by ALB health check
GET  /api/users           → list users
POST /api/users           → create user
POST /api/files           → upload to S3
GET  /api/files           → list files
DELETE /api/files/<name>  → delete from S3
```

## CI/CD pipeline

```text
git push → GitHub Actions → OIDC auth to AWS → Docker build → ECR push (tag: git-sha)
    → ECS task definition updated → rolling deployment → ALB /health check
```

Each image is tagged with the Git commit SHA (not `latest`), so any running deployment is traceable back to an exact commit. Authentication uses GitHub OIDC — the workflow assumes a scoped IAM role restricted to this repo and the `main` branch, so no AWS access keys are stored in GitHub at all.

## Repository structure

```text
aws-3tier-flask/
├── backend/
│   ├── app.py
│   ├── init_db.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── terraform/
│       ├── vpc.tf
│       ├── nat.tf
│       ├── security-groups.tf
│       ├── rds.tf
│       ├── secrets.tf
│       ├── ecr.tf
│       ├── alb.tf
│       ├── ecs.tf
│       ├── s3.tf
│       └── github-oidc.tf
├── .github/workflows/deploy.yml
└── README.md
```

## Security

- ECS tasks and RDS run in private subnets with no public IPs
- RDS accepts traffic only from the ECS security group — no internet access
- S3 Block Public Access enabled; access only via IAM task role
- Database credentials in Secrets Manager, never in code, Dockerfile, or the repo
- GitHub OIDC instead of long-lived AWS access keys, scoped to this repo/branch
- ECR image scanning enabled

## Key engineering decisions

- **Single NAT Gateway** — a deliberate cost-vs-availability trade-off for a learning project; production would use one per AZ.
- **Git-SHA image tags** — avoids `latest` so every deployment is traceable to a source commit.
- **Terraform + CI/CD separation** — Terraform owns infrastructure; GitHub Actions owns application deployments. The ECS service ignores externally created task-definition revisions so Terraform never rolls the app back to an older image.

## Testing performed

- **App:** health check, user CRUD, duplicate-email handling
- **Data:** RDS connectivity, schema init, S3 upload → list → delete lifecycle
- **Infra:** ALB → ECS → RDS/S3 connectivity, NAT outbound routing, ECS Exec debugging
- **CI/CD:** OIDC auth, ECR push, rolling ECS deployment, post-deploy `/health` verification — confirmed end-to-end with a live `200 healthy` response

## Cost & teardown

Primary cost drivers: **NAT Gateway** (charges even at low traffic), RDS, ECS Fargate, ALB, and CloudWatch Logs. For a learning environment, destroy after testing:

```bash
cd backend/terraform
terraform destroy
```

Verify no NAT Gateway, Elastic IP, RDS, ECS, ALB, or CloudWatch resources remain afterward.

## Future improvements

1. HTTPS via ACM + Route 53 custom domain
2. ECS autoscaling and Multi-AZ RDS/NAT for real high availability
3. Remote Terraform state with locking
4. Blue/green deployments, CloudWatch alarms, SNS notifications
5. Terraform and container security scanning in CI

## Author

**M A Azam Khan**
GitHub: [@azam723](https://github.com/azam723)
