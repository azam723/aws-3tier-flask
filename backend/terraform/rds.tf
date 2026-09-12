# ==========================================
# RDS Subnet Group
# ==========================================

resource "aws_db_subnet_group" "postgres" {
  name = "${var.project_name}-postgres"

  subnet_ids = [
    aws_subnet.private_a.id,
    aws_subnet.private_b.id
  ]

  tags = {
    Name    = "${var.project_name}-postgres-subnet-group"
    Project = var.project_name
  }
}


# ==========================================
# PostgreSQL RDS
# ==========================================

resource "aws_db_instance" "postgres" {
  identifier = "${var.project_name}-postgres"

  engine         = "postgres"
  instance_class = "db.t3.micro"

  allocated_storage = 20
  storage_type      = "gp3"

  db_name  = "appdb"
  username = var.db_username
  password = var.db_password

  port = 5432

  db_subnet_group_name   = aws_db_subnet_group.postgres.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  publicly_accessible = false

  # Cost-conscious configuration
  multi_az = false

  backup_retention_period = 0

  deletion_protection = false
  skip_final_snapshot = true

  apply_immediately = true

  tags = {
    Name    = "${var.project_name}-postgres"
    Project = var.project_name
  }
}
