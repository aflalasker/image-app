output "fqdn" {
  value       = azurerm_container_app_custom_domain.custom_domain.name
  description = "The FQDN of the container app"
}
