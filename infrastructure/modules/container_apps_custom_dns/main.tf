locals {
  default_tags = merge(var.tags, { "module" = "container_apps_custom_dns" })
}

resource "azurerm_dns_txt_record" "asuid" {
  name                = "asuid.${var.container_app_dns_config.service_name}"
  resource_group_name = var.resource_group_name
  zone_name           = var.dns_zone_name
  ttl                 = 300
  tags                = local.default_tags

  record {
    value = var.container_app_dns_config.custom_domain_verification_id
  }
}

resource "azurerm_dns_cname_record" "cert_verification" {
  name                = var.container_app_dns_config.service_name
  zone_name           = var.dns_zone_name
  resource_group_name = var.resource_group_name
  ttl                 = 300
  record              = var.container_app_dns_config.fqdn
  tags                = local.default_tags
}

resource "azurerm_container_app_custom_domain" "custom_domain" {
  name             = "${var.container_app_dns_config.service_name}.${var.dns_zone_name}"
  container_app_id = var.container_app_dns_config.container_app_id
  depends_on       = [azurerm_dns_txt_record.asuid]

  lifecycle {
    ignore_changes = [certificate_binding_type, container_app_environment_certificate_id]
  }
}
