resource "azurerm_storage_account" "shorturls" {
  name                     = "sa${local.short_name}${var.env}${local.short_location}urls"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  tags                     = local.default_tags
}

resource "azurerm_storage_table" "shorturls" {
  name                 = "shorturls"
  storage_account_name = azurerm_storage_account.shorturls.name
}

resource "azurerm_storage_account" "registered_user_image_storage" {
  name                     = "sa${local.short_name}${var.env}${local.short_location}ruimg"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  tags                     = local.default_tags
}

resource "azurerm_storage_account" "guest_users_image_storage" {
  name                     = "sa${local.short_name}${local.location}guimg"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  tags                     = local.default_tags
}
