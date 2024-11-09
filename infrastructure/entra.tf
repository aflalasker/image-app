data "azuread_client_config" "current" {}

data "azuread_application_published_app_ids" "well_known" {}

data "azuread_service_principal" "msgraph" {
  client_id = data.azuread_application_published_app_ids.well_known.result["MicrosoftGraph"]
}

resource "azuread_application_registration" "image_api_app" {
  display_name                   = "app-reg-${local.short_name}-${var.env}-api"
  description                    = "The AAD Application for the ${var.env} ${local.app_name} API"
  requested_access_token_version = 2
  sign_in_audience               = "AzureADandPersonalMicrosoftAccount"
}

resource "azuread_application_identifier_uri" "image_api_app_uri" {
  application_id = azuread_application_registration.image_api_app.id
  identifier_uri = "api://${azuread_application_registration.image_api_app.client_id}"
}

resource "azuread_application_permission_scope" "user_impersonation" {
  application_id = azuread_application_registration.image_api_app.id
  scope_id       = uuidv5("oid", "app-reg-${local.short_name}-${var.env}-api")
  value          = "user_impersonation"

  admin_consent_description  = "Allow the application to access the Image App on behalf of the signed-in user."
  admin_consent_display_name = "Access the Image App on behalf of the signed-in user"
}

resource "azuread_application_api_access" "image_api_app_msgraph_access" {
  application_id = azuread_application_registration.image_api_app.id
  api_client_id  = data.azuread_application_published_app_ids.well_known.result["MicrosoftGraph"]

  role_ids = [
    data.azuread_service_principal.msgraph.app_role_ids["Group.Read.All"],
    data.azuread_service_principal.msgraph.app_role_ids["User.Read.All"],
  ]

  scope_ids = [
    data.azuread_service_principal.msgraph.oauth2_permission_scope_ids["User.ReadWrite"],
  ]
}

resource "azuread_application_owner" "image_api_app_owner" {
  application_id  = azuread_application_registration.image_api_app.id
  owner_object_id = data.azuread_client_config.current.object_id
}

resource "azuread_service_principal" "image_api_app_sp" {
  client_id                    = azuread_application_registration.image_api_app.client_id
  app_role_assignment_required = false
  owners                       = [data.azuread_client_config.current.object_id]
}

#################### Swagger App ####################

resource "azuread_application_registration" "image_api_app_swagger" {
  display_name                   = "app-reg-${local.short_name}-${var.env}-swagger"
  description                    = "The AAD Application for the ${local.app_name} api Swagger"
  requested_access_token_version = 2
  sign_in_audience               = "AzureADandPersonalMicrosoftAccount"
}

resource "azuread_application_identifier_uri" "image_api_app_swagger_uri" {
  application_id = azuread_application_registration.image_api_app_swagger.id
  identifier_uri = "api://${azuread_application_registration.image_api_app_swagger.client_id}"
}

resource "azuread_application_redirect_uris" "spa_redirect_uris" {
  application_id = azuread_application_registration.image_api_app_swagger.id
  type           = "SPA"
  redirect_uris  = split(",", local.oauth2_redirect_uris)
}

resource "azuread_application_api_access" "image_api_app_swagger_msgraph_access" {
  application_id = azuread_application_registration.image_api_app_swagger.id
  api_client_id  = data.azuread_application_published_app_ids.well_known.result["MicrosoftGraph"]

  role_ids = [
    data.azuread_service_principal.msgraph.app_role_ids["Group.Read.All"],
    data.azuread_service_principal.msgraph.app_role_ids["User.Read.All"],
  ]

  scope_ids = [
    data.azuread_service_principal.msgraph.oauth2_permission_scope_ids["User.ReadWrite"],
  ]
}

resource "azuread_application_api_access" "image_api_app_swagger_user_impersonation_access" {
  application_id = azuread_application_registration.image_api_app_swagger.id
  api_client_id  = azuread_application_registration.image_api_app.client_id

  role_ids = [
    azuread_application_permission_scope.user_impersonation.scope_id,
  ]

  scope_ids = [
    azuread_application_permission_scope.user_impersonation.scope_id
  ]
}

resource "azuread_application_owner" "image_api_app_swagger_owner" {
  application_id  = azuread_application_registration.image_api_app_swagger.id
  owner_object_id = data.azuread_client_config.current.object_id
}

resource "azuread_service_principal" "image_api_app_swagger_sp" {
  client_id                    = azuread_application_registration.image_api_app_swagger.client_id
  app_role_assignment_required = false
  owners                       = [data.azuread_client_config.current.object_id]
}
