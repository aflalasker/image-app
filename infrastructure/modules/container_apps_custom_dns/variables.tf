variable "dns_zone_name" {
  description = "The DNS zone name to attach the reconrds"
  type        = string
}

variable "resource_group_name" {
  description = "The name of the resource group"
  type        = string
}

variable "container_app_dns_config" {
  description = "The DNS configuration for the container app"
  type = object({
    container_app_id              = string
    container_app_name            = string
    container_environment_name    = string
    service_name                  = string
    custom_domain_verification_id = string
    fqdn                          = string
  })
}

variable "tags" {
  description = "Tags to apply to the resources"
  type        = map(string)
}
