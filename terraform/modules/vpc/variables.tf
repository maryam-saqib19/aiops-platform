# ============================================================
# Inputs this module accepts when called
# ============================================================

variable "project_name" {
  type = string
}

variable "environment" {
  type = string
}

variable "cidr_block" {
  type        = string
  description = "The IP address range for this VPC, e.g. 10.1.0.0/16"
}

variable "availability_zones" {
  type        = list(string)
  description = "List of AZs to spread subnets across, e.g. [us-east-1a, us-east-1b]"
}

variable "common_tags" {
  type    = map(string)
  default = {}
}

