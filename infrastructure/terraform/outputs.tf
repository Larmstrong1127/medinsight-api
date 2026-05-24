output "api_url" {
  description = "Public URL of the load balancer"
  value       = module.ecs.alb_dns_name
}

output "ecr_repository_url" {
  description = "ECR repository URL for Docker pushes"
  value       = aws_ecr_repository.api.repository_url
}

output "documents_bucket" {
  description = "S3 bucket for encrypted document storage"
  value       = module.storage.documents_bucket
}

output "kms_key_arn" {
  description = "KMS key ARN used for encryption"
  value       = module.security.kms_key_arn
  sensitive   = true
}
