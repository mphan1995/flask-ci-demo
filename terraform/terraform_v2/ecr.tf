resource "aws_ecr_repository" "flask_app" {
  name                 = "${var.project}-app"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration { scan_on_push = true }

  tags = { Project = var.project }
}
