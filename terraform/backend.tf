terraform {
  backend "azurerm" {
    resource_group_name  = "rg-portfolio"
    storage_account_name = "aniketterraformstate26"
    container_name       = "project2-tfstate"
    key                  = "project2.tfstate"

    use_azuread_auth = true
    use_oidc         = true
  }
}
