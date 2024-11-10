<!-- BEGIN_TF_DOCS -->

# Module documentation
Below is the documentation for the terraform generated using Terraform-docs.

## Requirements

No requirements.
## Providers

| Name | Version |
|------|---------|
| <a name="provider_azurerm"></a> [azurerm](#provider\_azurerm) | n/a |
## Resources

| Name | Type |
|------|------|
| [azurerm_container_app_custom_domain.custom_domain](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/container_app_custom_domain) | resource |
| [azurerm_dns_cname_record.cert_verification](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/dns_cname_record) | resource |
| [azurerm_dns_txt_record.asuid](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/dns_txt_record) | resource |
## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_container_app_dns_config"></a> [container\_app\_dns\_config](#input\_container\_app\_dns\_config) | The DNS configuration for the container app | <pre>object({<br/>    container_app_id              = string<br/>    container_app_name            = string<br/>    container_environment_name    = string<br/>    service_name                  = string<br/>    custom_domain_verification_id = string<br/>    fqdn                          = string<br/>  })</pre> | n/a | yes |
| <a name="input_dns_zone_name"></a> [dns\_zone\_name](#input\_dns\_zone\_name) | The DNS zone name to attach the reconrds | `string` | n/a | yes |
| <a name="input_resource_group_name"></a> [resource\_group\_name](#input\_resource\_group\_name) | The name of the resource group | `string` | n/a | yes |
| <a name="input_tags"></a> [tags](#input\_tags) | Tags to apply to the resources | `map(string)` | n/a | yes |
## Outputs

| Name | Description |
|------|-------------|
| <a name="output_fqdn"></a> [fqdn](#output\_fqdn) | The FQDN of the container app |
<!-- END_TF_DOCS -->