# ==========================================
# ECR Repository
# ==========================================

resource "aws_ecr_repository" "flask" {
  name                 = "${var.project_name}-flask"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name    = "${var.project_name}-flask"
    Project = var.project_name
  }
}


# ==========================================
# ECR Lifecycle Policy
# Keep only the latest 3 images
# ==========================================

resource "aws_ecr_lifecycle_policy" "flask" {
  repository = aws_ecr_repository.flask.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1

        description = "Keep only the latest 3 images"

        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 3
        }

        action = {
          type = "expire"
        }
      }
    ]
  })
}
