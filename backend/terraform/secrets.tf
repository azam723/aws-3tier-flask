# ==========================================
# RDS Credentials Secret
# ==========================================

resource "aws_secretsmanager_secret" "db_credentials" {
  name = "${var.project_name}/database"

  tags = {
    Name    = "${var.project_name}-database-secret"
    Project = var.project_name
  }
}


# ==========================================
# Secret Value
# ==========================================

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id

  secret_string = jsonencode({
    username = var.db_username
    password = var.db_password
    host     = aws_db_instance.postgres.address
    port     = aws_db_instance.postgres.port
    database = aws_db_instance.postgres.db_name
  })
}

# ==========================================
# Allow ECS to Read Database Secret
# ==========================================

resource "aws_iam_role_policy" "ecs_secrets" {
  name = "${var.project_name}-ecs-secrets"
  role = aws_iam_role.ecs_task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Action = [
          "secretsmanager:GetSecretValue"
        ]

        Resource = aws_secretsmanager_secret.db_credentials.arn
      }
    ]
  })
}
