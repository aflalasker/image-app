locals {
  app_name       = "image-app"
  short_name     = "ia"
  location       = "westeurope"
  short_location = "euwest"

  default_tags = {
    Project    = local.app_name
    Terraform  = "true"
    Repository = "https://github.com/aflalasker/image-app"
  }

  oauth2_redirect_uris = "http://localhost:8000/oauth2-redirect,https://${azurerm_container_app.api.ingress[0].fqdn}/oauth2-redirect"

  otel_exporter_otlp_endpoint = "http://${azurerm_container_app.otel.name}:${azurerm_container_app.otel.ingress[0].exposed_port}"

  env_vars = {
    "AZURE_TABLE_STORAGE_ACCOUNT_NAME" = azurerm_storage_account.shorturls.name
    "AZURE_STORAGE_ACCOUNT_TABLE_NAME" = azurerm_storage_table.shorturls.name
    "AZURE_STORAGE_ACCOUNT_TABLE_KEY"  = azurerm_storage_account.shorturls.primary_access_key

    "AZURE_GUEST_STORAGE_ACCOUNT_NAME" = azurerm_storage_account.guest_users_image_storage.name
    "AZURE_GUEST_STORAGE_ACCOUNT_KEY"  = azurerm_storage_account.guest_users_image_storage.primary_access_key

    "AZURE_REGISTERED_STORAGE_ACCOUNT_NAME" = azurerm_storage_account.registered_user_image_storage.name
    "AZURE_REGISTERED_STORAGE_ACCOUNT_KEY"  = azurerm_storage_account.registered_user_image_storage.primary_access_key

    "APP_CLIENT_ID"      = azuread_application_registration.image_api_app.client_id
    "OPEN_API_CLIENT_ID" = azuread_application_registration.image_api_app_swagger.client_id
    "TENANT_ID"          = var.tenant_id
    "SCOPE"              = "api://${azuread_application_registration.image_api_app.client_id}/${azuread_application_permission_scope.user_impersonation.value}"

    "OTEL_EXPORTER_OTLP_ENDPOINT" = local.otel_exporter_otlp_endpoint
    "ALLOWED_HOST"                = "*"
  }

  kql_queries = { for file in fileset(path.module, "kql/*.kql") : file => file("${path.module}/${file}") }
}
