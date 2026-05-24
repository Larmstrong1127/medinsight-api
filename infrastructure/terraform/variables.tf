variable "project" {
  description = "Project name used as a prefix for all resources"
  type        = string
  default     = "medinsight"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "prod"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "desired_count" {
  description = "Number of ECS tasks to run"
  type        = number
  default     = 2
}
