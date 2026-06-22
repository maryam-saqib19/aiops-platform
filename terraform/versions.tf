# ============================================================
# Terraform and Provider Version Constraints
# Locking versions ensures the same code produces the same
# infrastructure every time, on every machine, forever
# ============================================================

terraform {
  required_version = ">= 1.6.0"
  # Any Terraform CLI version from 1.6.0 upward

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
      # ~> 5.0 means "5.x but never 6.0" — protects against breaking changes
    }
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # ── Remote state backend ─────────────────────────────────
  # COMMENTED OUT for local development and exam demonstration
  # In real enterprise deployment, uncomment this so multiple
  # engineers share one state file stored safely in S3, with
  # DynamoDB providing locking to prevent two people running
  # terraform apply at the exact same time
  #
  # backend "s3" {
  #   bucket         = "aiops-platform-terraform-state"
  #   key            = "global/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-state-lock"
  # }
}
