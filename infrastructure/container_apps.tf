resource "azurerm_container_app_environment" "image_app_environment" {
  name                       = "cae-${local.short_name}-${var.env}-${local.short_location}-app"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  tags                       = merge(local.default_tags, { "domain_name" = "${var.env}.${var.dns_zone_name}" })

  provisioner "local-exec" {
    command = "az containerapp env certificate delete -g ${self.resource_group_name} --name ${self.name} --certificate api.${self.tags["domain_name"]} --yes"
    when    = destroy
  }

  provisioner "local-exec" {
    command = "az containerapp env certificate delete -g ${self.resource_group_name} --name ${self.name} --certificate fe.${self.tags["domain_name"]} --yes"
    when    = destroy
  }
}

resource "azurerm_container_app" "frontend" {
  name                         = "capp-${local.short_name}-${var.env}-${local.short_location}-frontend"
  container_app_environment_id = azurerm_container_app_environment.image_app_environment.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"
  tags                         = local.default_tags

  template {
    container {
      name  = "frontend"
      image = "${azurerm_container_registry.main.login_server}/frontend:latest"

      env {
        name  = "BACKEND_API_URL"
        value = "https://api.${var.env}.${var.dns_zone_name}"
      }

      env {
        name  = "OTEL_EXPORTER_OTLP_ENDPOINT"
        value = local.otel_exporter_otlp_endpoint
      }
      cpu    = 0.25
      memory = "0.5Gi"
    }
  }

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.app_identity.id]
  }

  ingress {
    allow_insecure_connections = false
    external_enabled           = true
    target_port                = 8501
    transport                  = "auto"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  registry {
    server   = azurerm_container_registry.main.login_server
    identity = azurerm_user_assigned_identity.app_identity.id
  }
}

resource "azurerm_container_app" "api" {
  name                         = "capp-${local.short_name}-${var.env}-${local.short_location}-api"
  container_app_environment_id = azurerm_container_app_environment.image_app_environment.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"
  tags                         = merge(local.default_tags, { "domain_name" = var.dns_zone_name })

  template {
    container {
      name  = "api"
      image = "${azurerm_container_registry.main.login_server}/image-api-app:latest"

      dynamic "env" {
        for_each = local.env_vars
        content {
          name  = env.key
          value = env.value
        }
      }

      readiness_probe {
        path                    = "/health/liveness"
        port                    = 8000
        transport               = "HTTP"
        interval_seconds        = 30
        timeout                 = 5
        failure_count_threshold = 3
      }

      liveness_probe {
        path                    = "/health/liveness"
        port                    = 8000
        transport               = "HTTP"
        initial_delay           = 30
        interval_seconds        = 10
        timeout                 = 5
        failure_count_threshold = 3
      }

      cpu    = 0.25
      memory = "0.5Gi"
    }
  }

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.app_identity.id]
  }

  ingress {
    allow_insecure_connections = false
    external_enabled           = true
    target_port                = 8000
    transport                  = "auto"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  registry {
    server   = azurerm_container_registry.main.login_server
    identity = azurerm_user_assigned_identity.app_identity.id
  }
}

resource "azurerm_container_app" "otel" {
  name                         = "capp-${local.short_name}-${var.env}-${local.short_location}-otel"
  container_app_environment_id = azurerm_container_app_environment.image_app_environment.id
  resource_group_name          = azurerm_resource_group.main.name
  revision_mode                = "Single"
  tags                         = local.default_tags

  template {
    container {
      name  = "otel-collector"
      image = "${azurerm_container_registry.main.login_server}/otel-col:latest"

      env {
        name  = "APPLICATIONINSIGHTS_CONNECTION_STRING"
        value = azurerm_application_insights.main.connection_string
      }
      cpu    = 0.25
      memory = "0.5Gi"
    }
  }

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.app_identity.id]
  }

  ingress {
    allow_insecure_connections = false
    external_enabled           = false
    target_port                = 4317
    exposed_port               = 4317
    transport                  = "tcp"

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }

  registry {
    server   = azurerm_container_registry.main.login_server
    identity = azurerm_user_assigned_identity.app_identity.id
  }
}

####################### Container App Custom DNS #######################
module "api" {
  source              = "./modules/container_apps_custom_dns"
  dns_zone_name       = azurerm_dns_zone.env_dns.name
  resource_group_name = azurerm_resource_group.main.name
  container_app_dns_config = {
    container_app_id              = azurerm_container_app.api.id
    container_app_name            = azurerm_container_app.api.name
    container_environment_name    = azurerm_container_app_environment.image_app_environment.name
    service_name                  = "api"
    custom_domain_verification_id = azurerm_container_app.api.custom_domain_verification_id
    fqdn                          = azurerm_container_app.api.ingress[0].fqdn
  }
  tags = local.default_tags
}

module "frontend" {
  source              = "./modules/container_apps_custom_dns"
  dns_zone_name       = azurerm_dns_zone.env_dns.name
  resource_group_name = azurerm_resource_group.main.name
  container_app_dns_config = {
    container_app_id              = azurerm_container_app.frontend.id
    container_app_name            = azurerm_container_app.frontend.name
    container_environment_name    = azurerm_container_app_environment.image_app_environment.name
    service_name                  = "fe"
    custom_domain_verification_id = azurerm_container_app.frontend.custom_domain_verification_id
    fqdn                          = azurerm_container_app.frontend.ingress[0].fqdn
  }
  tags = local.default_tags
}
