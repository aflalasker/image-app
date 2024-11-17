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

  provisioner "local-exec" {
    command = "./${path.module}/certificate_provisioner.sh ${var.resource_group_name} ${var.container_app_dns_config.container_environment_name} ${var.container_app_dns_config.service_name}.${var.dns_zone_name} --hostname ${var.container_app_dns_config.service_name}.${var.dns_zone_name} --validation-method CNAME"
    when    = create
  }
  provisioner "local-exec" {
    command = "az containerapp hostname bind -n ${var.container_app_dns_config.container_app_name} -g ${var.resource_group_name} --hostname ${var.container_app_dns_config.service_name}.${var.dns_zone_name} --certificate ${var.container_app_dns_config.service_name}.${var.dns_zone_name} --environment ${var.container_app_dns_config.container_environment_name}"
    when    = create
  }

  depends_on = [azurerm_dns_txt_record.asuid]

  lifecycle {
    ignore_changes = [certificate_binding_type, container_app_environment_certificate_id]
  }
}
