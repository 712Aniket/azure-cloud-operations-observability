terraform {
  backend "azurerm" {
    resource_group_name  = "rg-portfolio"
    storage_account_name = "aniketportfolio07"
    container_name       = "terraform-state"
    key                  = "project2.tfstate"

    use_azuread_auth = true
    use_oidc         = true
  }
}
