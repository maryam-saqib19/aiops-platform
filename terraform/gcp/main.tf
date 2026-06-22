# ============================================================
# GCP Provider Configuration and GKE Cluster
# GCP = ML/analytics workloads, GPU availability for training
# ============================================================

terraform {
  required_providers {
    google = { source = "hashicorp/google", version = "~> 5.0" }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ── Variables ────────────────────────────────────────────────
variable "project_id" {
  type    = string
  default = "aiops-platform-demo"
}

variable "region" {
  type    = string
  default = "europe-west1"
}

variable "environment" {
  type    = string
  default = "production"
}

variable "project_name" {
  type    = string
  default = "aiops-platform"
}

variable "kubernetes_version" {
  type    = string
  default = "1.28"
}

locals {
  resource_prefix = "${var.project_name}-${var.environment}"
}

resource "google_compute_network" "main" {
  name                    = "${local.resource_prefix}-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "main" {
  name          = "${local.resource_prefix}-subnet"
  ip_cidr_range = "10.3.0.0/22"
  region        = var.region
  network       = google_compute_network.main.id

  secondary_ip_range {
    range_name    = "pods"
    ip_cidr_range = "10.3.64.0/18"
  }
  secondary_ip_range {
    range_name    = "services"
    ip_cidr_range = "10.3.128.0/20"
  }
}

resource "google_container_cluster" "main" {
  name     = "${local.resource_prefix}-gke"
  location = var.region

  remove_default_node_pool = true
  initial_node_count       = 1

  network    = google_compute_network.main.self_link
  subnetwork = google_compute_subnetwork.main.self_link

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  # Workload Identity — pods authenticate to GCP APIs WITHOUT
  # any downloaded service account key file sitting on disk
  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  enable_shielded_nodes = true

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }
}

# ── Standard node pool for application workloads ─────────────
resource "google_container_node_pool" "app_nodes" {
  name     = "app-pool"
  cluster  = google_container_cluster.main.name
  location = var.region

  autoscaling {
    min_node_count = 2
    max_node_count = 8
  }

  node_config {
    machine_type = "e2-standard-4"
    disk_size_gb = 50
    image_type   = "COS_CONTAINERD"
    # Container-Optimised OS — minimal attack surface

    workload_metadata_config { mode = "GKE_METADATA" }
  }
}

# ── GPU node pool — only for ML training jobs ─────────────────
resource "google_container_node_pool" "ml_nodes" {
  name     = "ml-gpu-pool"
  cluster  = google_container_cluster.main.name
  location = var.region

  autoscaling {
    min_node_count = 0
    # Scales to ZERO when no ML training is running — saves cost
    max_node_count = 4
  }

  node_config {
    machine_type = "n1-standard-4"
    disk_size_gb = 100

    guest_accelerator {
      type  = "nvidia-tesla-t4"
      count = 1
    }

    workload_metadata_config { mode = "GKE_METADATA" }
  }
}

output "cluster_name" { value = google_container_cluster.main.name }
