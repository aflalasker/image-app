variable "env" {
  description = "The environment name to use for the deployment"
  type        = string
}

variable "tenant_id" {
  description = "The Azure tenant ID"
  type        = string
}

variable "subscription_id" {
  description = "The Azure subscription ID"
  type        = string
}

variable "source_acr_server_name" {
  description = "The Azure Container Registry to use as the source to copy the images from to the ACR in the target environment"
  type        = string
}
