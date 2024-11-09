output "swagger_url" {
  value       = "https://${azurerm_container_app.api.ingress[0].fqdn}/docs"
  description = "The URL for the Swagger documentation"
}

output "frontend_url" {
  value       = "https://${azurerm_container_app.frontend.ingress[0].fqdn}"
  description = "The URL for the frontend"
}

output "app_client_id" {
  value       = azuread_application_registration.image_api_app.client_id
  description = "The client ID for the application"
}

output "swagger_client_id" {
  value       = azuread_application_registration.image_api_app_swagger.client_id
  description = "The client ID for the Swagger application"
}