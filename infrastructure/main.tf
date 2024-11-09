
resource "azurerm_resource_group" "main" {
  name     = "rg-${local.short_name}-${var.env}-${local.short_location}"
  location = local.location
  tags     = local.default_tags
}

resource "azurerm_container_registry" "main" {
  name                = "acr${local.short_name}${var.env}${local.short_location}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "Standard"
  admin_enabled       = true
  tags                = local.default_tags

  provisioner "local-exec" {
    command = "az acr import --name ${self.name} --source assessmentacr.azurecr.io/otel-col:latest --image otel-col:latest"
    when    = create
  }

  provisioner "local-exec" {
    command = "az acr import --name ${self.name} --source assessmentacr.azurecr.io/image-api-app:latest --image image-api-app:latest"
    when    = create
  }

  provisioner "local-exec" {
    command = "az acr import --name ${self.name} --source assessmentacr.azurecr.io/frontend:latest --image frontend:latest"
    when    = create
  }
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "law-${local.short_name}-${var.env}-${local.short_location}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = local.default_tags
}

resource "azurerm_application_insights" "main" {
  name                = "ai-${local.short_name}-${var.env}-${local.short_location}-app"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  application_type    = "web"
  workspace_id        = azurerm_log_analytics_workspace.main.id
  retention_in_days   = 30
  tags                = local.default_tags
}

resource "azurerm_application_insights_analytics_item" "kql" {
  for_each                = local.kql_queries
  name                    = "kql-${local.short_name}-${var.env}-${local.short_location}-${split(".", split("/", each.key)[1])[0]}"
  application_insights_id = azurerm_application_insights.main.id
  content                 = each.value
  scope                   = "shared"
  type                    = "query"
}

resource "azurerm_user_assigned_identity" "app_identity" {
  name                = "id-${local.short_name}-${var.env}-${local.short_location}-app"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.default_tags
}
