output "ecr_repo_url"     { value = aws_ecr_repository.flask_app.repository_url }
output "eks_cluster_name" { value = module.eks.cluster_name }
output "kubectl_howto" {
  value = "aws eks update-kubeconfig --region ${var.region} --name ${module.eks.cluster_name}"
}
