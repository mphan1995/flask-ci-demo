variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Project prefix"
  type        = string
  default     = "flask-ci"
}

variable "eks_cluster_version" {
  description = "EKS version"
  type        = string
  default     = "1.29"
}

variable "node_instance_types" {
  type        = list(string)
  default     = ["t3.medium"]
}

variable "desired_size" { default = 2 }
variable "min_size"     { default = 1 }
variable "max_size"     { default = 3 }
