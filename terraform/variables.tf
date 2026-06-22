# ============================================================
# Global Variables — shared across AWS, Azure, and GCP configs
# ============================================================

variable "environment" {
  type        = string
  description = "Deployment environment — controls sizing, retention, and naming"
  default     = "production"

  validation {
    condition     = contains(["development", "staging", "production"], var.environment)
    error_message = "Environment must be exactly one of: development, staging, production."
  }
  # This validation block REJECTS the entire terraform plan/apply
  # if someone types "prod" instead of "production" — catches
  # human error before it becomes a deployment mistake
}

variable "project_name" {
  type        = string
  description = "Project identifier used as a prefix on every resource name"
  default     = "aiops-platform"
}

variable "aws_region" {
  type        = string
  description = "AWS region for the primary production cluster"
  default     = "us-east-1"
}

variable "azure_location" {
  type        = string
  description = "Azure region — westeurope chosen for GDPR EU data residency"
  default     = "westeurope"
}

variable "gcp_region" {
  type        = string
  description = "GCP region for ML workloads"
  default     = "europe-west1"
}

variable "gcp_project_id" {
  type        = string
  description = "GCP project ID — must exist before terraform apply runs"
  default     = "aiops-platform-demo"
}

variable "kubernetes_version" {
  type        = string
  description = "Kubernetes version — kept identical across all 3 clouds for consistency"
  default     = "1.28"
}

variable "node_instance_type_aws" {
  type        = string
  description = "EC2 instance type for AWS worker nodes"
  default     = "t3.large"
  # 2 vCPU, 8GB RAM — sufficient for the full observability stack
}

variable "node_count" {
  type        = number
  description = "Number of worker nodes per cluster"
  default     = 3
  # 3 nodes = one per availability zone, matching our HA requirement
}

# ── Compliance tags applied to EVERY resource ───────────────
# Required for ISO 27001 asset management and cost allocation
variable "common_tags" {
  type        = map(string)
  description = "Tags applied to all cloud resources for compliance and cost tracking"
  default = {
    Project    = "aiops-platform"
    ManagedBy  = "terraform"
    Owner      = "platform-team"
    Compliance = "iso27001"
  }
}
