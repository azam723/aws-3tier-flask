# AWS 3-Tier Flask Application

A hands-on AWS cloud and DevOps project where I designed, provisioned, containerized, deployed, tested, and automated a Flask application running on AWS.

The project was built from scratch using **Terraform and AWS**, with **GitHub Actions CI/CD using GitHub OIDC** for keyless authentication.

The application uses a traditional 3-tier architecture:

```text
Internet
    |
    v
Application Load Balancer
    |
    v
ECS Fargate
    |
    +------------------+
    |                  |
    v                  v
RDS PostgreSQL       Amazon S3
```

The application runs inside a VPC with public and private subnets. ECS and RDS are kept in private subnets, while the ALB provides the public entry point.

---

## Project Overview

This project was implemented as a practical hands-on exercise to understand how the different parts of a cloud application work together rather than deploying a single service in isolation.

I built and connected:

* AWS networking
* Private and public subnets
* NAT Gateway
* Security groups
* Application Load Balancer
* ECS Fargate
* Amazon ECR
* RDS PostgreSQL
* Amazon S3
* Secrets Manager
* IAM roles
* CloudWatch Logs
* ECS Exec
* Terraform
* GitHub Actions
* GitHub OIDC

The final result is a containerized Flask API that communicates with PostgreSQL and S3 while running on ECS Fargate in private subnets.

---
## Architecture Diagram
<img width="1312" height="1199" alt="aws-3tier-architecture" src="https://github.com/user-attachments/assets/0a87a966-9c6e-426d-8e11-6af6752ed00a" />


## Architecture

```text
                           Internet
                              |
                              v
                  +-----------------------+
                  | Application Load      |
                  | Balancer              |
                  | HTTP :80              |
                  +-----------+-----------+
                              |
                              | TCP :5000
                              v
                 +------------------------+
                 | ECS Fargate            |
                 | Flask API              |
                 | Private Subnets        |
                 +-----------+------------+
                             |
                  +----------+----------+
                  |                     |
                  v                     v
        +------------------+    +------------------+
        | RDS PostgreSQL   |    | Amazon S3        |
        | Private Subnet   |    | Private Bucket   |
        +------------------+    +------------------+

                 Private Subnets
                       |
                       | outbound traffic
                       v
                 +-------------+
                 | NAT Gateway |
                 +------+------+
                        |
                        v
                 Internet Gateway
                        |
                     Internet
```

### CI/CD Architecture

```text
Developer
    |
    | git push
    v
GitHub Repository
    |
    v
GitHub Actions
    |
    | OIDC
    v
AWS IAM Role
    |
    +--------------------+
    |                    |
    v                    v
Docker Build          AWS APIs
    |
    v
Amazon ECR
    |
    | image:<git-sha>
    v
ECS Task Definition
    |
    v
ECS Fargate Service
    |
    v
ALB Health Check
    |
    v
Application Healthy
```

---

## What I Built

### 1. AWS Networking

Created a VPC with CIDR:

```text
10.0.0.0/16
```

The VPC contains:

```text
Public:
10.0.1.0/24
10.0.2.0/24

Private:
10.0.11.0/24
10.0.12.0/24
```

The subnets are distributed across two Availability Zones.

The public subnets contain the Application Load Balancer and NAT Gateway.

The private subnets contain the ECS tasks and RDS database.

Private subnets do not assign public IP addresses to ECS tasks.

---

## 2. NAT Gateway

A NAT Gateway was configured so resources in private subnets can initiate outbound internet connections without becoming publicly reachable.

For cost control during the project, a **single NAT Gateway** was used rather than one NAT Gateway per Availability Zone.

This is a deliberate cost-versus-high-availability trade-off.

---

## 3. Security Groups

Network access was restricted between application tiers.

```text
Internet
   |
   | HTTP/HTTPS
   v
ALB Security Group
   |
   | TCP 5000
   v
ECS Security Group
   |
   | TCP 5432
   v
RDS Security Group
```

The RDS security group does not allow unrestricted internet access.

PostgreSQL traffic is permitted only from the ECS security group.

---

## 4. Flask Application

The backend is a Python Flask REST API.

The application provides:

### Health

```text
GET /health
```

The health endpoint checks database connectivity.

Example:

```json
{
  "status": "healthy",
  "service": "flask-api",
  "database": "connected"
}
```

This endpoint is also used by the ALB target group health check.

### Users

```text
GET  /api/users
POST /api/users
```

The API stores user information in PostgreSQL.

I tested:

* Reading users
* Creating users
* Duplicate email handling
* Database connectivity

### Files

```text
POST   /api/files
GET    /api/files
DELETE /api/files/<filename>
```

Files are stored in the private S3 bucket.

I tested the complete file lifecycle:

```text
Upload
  ↓
List
  ↓
Delete
  ↓
List again
```

---

## 5. PostgreSQL with Amazon RDS

The application database runs on Amazon RDS PostgreSQL.

The database is:

* In private subnets
* Not publicly accessible
* Protected by a dedicated security group
* Accessible from ECS on TCP port 5432

The database schema was initialized from the ECS container.

The initialization script creates the `users` table and inserts sample data.

I verified database connectivity through the running ECS application rather than connecting the database directly to the public internet.

---

## 6. Amazon S3

A private S3 bucket was created for application file storage.

Public access is blocked using S3 Block Public Access.

Object ownership is configured using:

```text
BucketOwnerEnforced
```

The ECS task accesses S3 through its IAM task role.

The application supports:

```text
ListBucket
GetObject
PutObject
DeleteObject
```

No AWS access keys are stored inside the Flask application.

---

## 7. Secrets Manager

Database credentials are stored in AWS Secrets Manager.

The ECS task retrieves:

```text
DB_USER
DB_PASSWORD
DB_HOST
DB_PORT
DB_NAME
```

The credentials are injected into the container as secrets.

This keeps database credentials out of:

* Source code
* Dockerfile
* GitHub repository
* Container image

---

## 8. ECS Fargate

The Flask application is containerized and deployed to Amazon ECS using Fargate.

The ECS service runs in private subnets with:

```text
Launch type: FARGATE
CPU: 256
Memory: 512 MB
Container port: 5000
```

The ECS task does not receive a public IP address.

Traffic reaches the container through the Application Load Balancer.

---

## 9. Amazon ECR

The Docker image is stored in Amazon ECR.

Instead of relying on `latest`, CI/CD creates images using the Git commit SHA.

Example:

```text
flask-3tier-flask:<git-sha>
```

This makes deployments traceable to a specific Git commit.

The ECR repository also has image scanning enabled.

A lifecycle policy keeps only a small number of recent images to reduce unnecessary storage.

---

## 10. Application Load Balancer

The Application Load Balancer is the public entry point for the application.

Traffic flow:

```text
Internet
   |
   v
ALB :80
   |
   v
ECS :5000
```

The target group uses:

```text
/health
```

as its health check endpoint.

The ALB only sends traffic to healthy ECS tasks.

---

## 11. CloudWatch Logging

ECS container logs are sent to Amazon CloudWatch Logs.

The application uses Gunicorn to run Flask:

```text
Gunicorn
    |
    v
Flask
```

Application errors are logged using Python's application logger.

This made it possible to inspect application behavior without logging into the container directly.

---

## 12. ECS Exec

ECS Exec was enabled for troubleshooting.

I used ECS Exec to access the running Flask container and execute the database initialization script:

```text
python init_db.py
```

The command successfully initialized the PostgreSQL database.

This also demonstrated how ECS Exec can be used for operational troubleshooting without exposing SSH access to the container.

---

# Infrastructure as Code

The AWS infrastructure was created using Terraform.

Terraform manages:

```text
VPC
Subnets
Route Tables
Internet Gateway
NAT Gateway
Elastic IP
Security Groups
RDS
Secrets Manager
ECR
ALB
ECS
S3
IAM
CloudWatch
GitHub OIDC
```

Terraform validation was performed using:

```bash
terraform validate
```

Infrastructure changes were reviewed with:

```bash
terraform plan
```

and applied using:

```bash
terraform apply
```

---

# GitHub Actions CI/CD

After manually validating the application and AWS infrastructure, I implemented automated deployment using GitHub Actions.

The pipeline is triggered whenever code is pushed to `main`.

```text
git push
   |
   v
GitHub Actions
   |
   v
AWS OIDC Authentication
   |
   v
ECR Login
   |
   v
Docker Build
   |
   v
Docker Push
   |
   v
ECS Task Definition Update
   |
   v
ECS Deployment
   |
   v
Service Stability Check
   |
   v
ALB /health
```

The deployment was successfully tested end-to-end.

---

# GitHub OIDC Authentication

The GitHub Actions workflow does not use long-lived AWS access keys.

Instead, GitHub Actions obtains temporary AWS credentials through OpenID Connect.

The workflow uses:

```yaml
permissions:
  id-token: write
  contents: read
```

The AWS IAM trust policy restricts access to the project's GitHub repository and `main` branch.

This was implemented so that the CI/CD pipeline can authenticate to AWS without storing an AWS access key or secret access key in GitHub.

---

# Deployment Strategy

Each deployment creates an ECR image tagged with the Git commit SHA.

The pipeline retrieves the current ECS task definition and updates the Flask container image while preserving the existing:

* IAM roles
* Secrets Manager configuration
* S3 configuration
* CloudWatch logging
* Port configuration
* CPU/memory settings

A new ECS task definition revision is registered and the ECS service is updated.

The workflow waits for the ECS service to become stable before completing successfully.

---

# Testing Performed

The application was tested at multiple layers.

### Application

* Flask application syntax
* Gunicorn startup
* `/health`
* `/api/users`
* User creation
* Duplicate user handling

### Database

* PostgreSQL connectivity
* Database initialization
* User table creation
* Insert/query operations

### S3

* File upload
* File listing
* File deletion
* Private bucket access through IAM

### ECS

* Fargate task startup
* Container health
* ECS Exec
* CloudWatch logs

### Networking

* ALB → ECS connectivity
* ECS → RDS connectivity
* ECS → S3 access
* Private subnet outbound connectivity through NAT Gateway

### CI/CD

* GitHub OIDC authentication
* AWS IAM role assumption
* Docker image build
* ECR push
* ECS task definition revision
* ECS rolling deployment
* ECS service stability
* ALB health verification

The final CI/CD deployment completed successfully and the public `/health` endpoint returned:

```json
{
  "status": "healthy",
  "service": "flask-api",
  "database": "connected"
}
```

---

# Repository Structure

```text
aws-3tier-flask/
│
├── backend/
│   ├── app.py
│   ├── init_db.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .dockerignore
│   │
│   └── terraform/
│       ├── provider.tf
│       ├── variables.tf
│       ├── vpc.tf
│       ├── nat.tf
│       ├── security-groups.tf
│       ├── rds.tf
│       ├── secrets.tf
│       ├── ecr.tf
│       ├── alb.tf
│       ├── ecs.tf
│       ├── s3.tf
│       ├── outputs.tf
│       └── github-oidc.tf
│
├── .github/
│   └── workflows/
│       └── deploy.yml
│
├── .gitignore
└── README.md
```

---

# Technology Stack

### Application

* Python
* Flask
* Gunicorn
* PostgreSQL
* Boto3

### Containers

* Docker
* Amazon ECR
* Amazon ECS Fargate

### AWS

* VPC
* EC2 networking components
* Application Load Balancer
* RDS PostgreSQL
* S3
* Secrets Manager
* IAM
* CloudWatch

### DevOps

* Terraform
* Git
* GitHub
* GitHub Actions
* GitHub OIDC

---

# Key Engineering Decisions

### Private ECS tasks

ECS tasks run without public IP addresses.

This reduces direct exposure of the application containers and forces application traffic through the ALB.

### Single NAT Gateway

A single NAT Gateway was intentionally used to reduce project cost.

A production high-availability design would normally use NAT Gateway infrastructure per Availability Zone.

### Git SHA image tags

Images are tagged using Git commit SHAs instead of relying on `latest`.

This makes it possible to identify exactly which source revision is running.

### OIDC instead of AWS access keys

GitHub Actions uses OIDC to assume an AWS IAM role.

This avoids maintaining long-lived AWS credentials inside GitHub.

### Terraform and CI/CD separation

Terraform manages the infrastructure.

GitHub Actions manages application image deployments to ECS.

The ECS service ignores externally created task-definition revisions so Terraform does not accidentally roll the service back to an older application image.

---

# Security

Security controls implemented in this project include:

* Private ECS tasks
* Private RDS database
* Restricted security groups
* S3 Block Public Access
* IAM roles instead of application access keys
* Secrets Manager for database credentials
* GitHub OIDC
* Repository/branch-restricted AWS trust policy
* ECR image scanning
* No credentials committed to Git
* Terraform sensitive variables excluded from version control

---

# Cost Awareness

This project intentionally uses several AWS services that can generate charges.

The most important resources to monitor are:

* NAT Gateway
* RDS
* ECS Fargate
* Application Load Balancer
* ECR storage
* CloudWatch Logs
* Secrets Manager

The NAT Gateway is particularly important because it can generate charges even when application traffic is low.

For a temporary learning environment, the infrastructure should be destroyed after testing.

```bash
cd backend/terraform
terraform destroy
```

After destruction, verify that the following resources are no longer running:

```text
NAT Gateway
Elastic IP
RDS
ECS
ALB
ECR
CloudWatch
Secrets Manager
S3
IAM resources
```

---

# Lessons Learned

Building this project hands-on provided practical experience with:

* Designing AWS network architecture
* Understanding public vs private subnets
* Configuring routing and NAT
* Connecting ECS to RDS securely
* Using IAM roles for AWS service access
* Injecting secrets into containers
* Containerizing a Flask application
* Deploying containers with ECS Fargate
* Using ALB health checks
* Troubleshooting containers with ECS Exec
* Working with Terraform state and lifecycle behavior
* Building GitHub Actions workflows
* Using GitHub OIDC with AWS
* Implementing automated ECS deployments
* Debugging real deployment and infrastructure issues
* Balancing AWS architecture with cloud cost

---

# Future Improvements

Possible improvements for a more production-oriented version include:

* HTTPS using ACM
* Route 53 custom domain
* AWS WAF
* ECS autoscaling
* Multi-AZ NAT Gateway
* RDS Multi-AZ
* VPC endpoints
* Remote Terraform state
* Terraform state locking
* Separate development and production environments
* Automated integration tests
* Blue/green deployments
* CloudWatch alarms
* SNS notifications
* ECR immutable tags
* Container security scanning
* Terraform security scanning
* Branch protection

---

# Project Status

```text
[x] Flask REST API
[x] Dockerized application
[x] AWS VPC
[x] Public/private subnet architecture
[x] NAT Gateway
[x] Security groups
[x] Application Load Balancer
[x] ECS Fargate
[x] RDS PostgreSQL
[x] S3 integration
[x] Secrets Manager
[x] ECR
[x] CloudWatch logging
[x] ECS Exec
[x] Terraform infrastructure
[x] GitHub OIDC
[x] GitHub Actions CI/CD
[x] Automated ECS deployment
[x] Application health verification
[x] End-to-end deployment testing
```

---

## Final Result

The completed project demonstrates a full cloud application lifecycle:

```text
Source Code
    |
    v
Docker
    |
    v
Amazon ECR
    |
    v
ECS Fargate
    |
    +--------> RDS PostgreSQL
    |
    +--------> Amazon S3
    |
    v
Application Load Balancer
    |
    v
Internet


Infrastructure is provisioned using Terraform and application deployments are automated through GitHub Actions using AWS OIDC.

The project was built and validated hands-on, including infrastructure provisioning, application deployment, database initialization, S3 operations, ECS troubleshooting, CI/CD implementation, and end-to-end health verification.

## Author

M A Azam Khan

GitHub: [@azam723](https://github.com/azam723)
