resource "azurerm_application_insights" "portfolio" {
  name                = var.application_insights_name
  location            = var.location
  resource_group_name = var.resource_group_name
  application_type    = "web"
  retention_in_days   = 90
  sampling_percentage = 0

  workspace_id = "/subscriptions/8bb846b6-1057-42bb-a02a-7a64e6a34178/resourceGroups/DefaultResourceGroup-CID/providers/Microsoft.OperationalInsights/workspaces/DefaultWorkspace-8bb846b6-1057-42bb-a02a-7a64e6a34178-CID"
}

resource "azurerm_monitor_action_group" "portfolio_failures" {
  name                = var.action_group_name
  resource_group_name = var.resource_group_name
  short_name          = "PortFail"

  email_receiver {
    name                    = "Aniket"
    email_address           = "712aniket@gmail.com"
    use_common_alert_schema = false
  }
}

resource "azurerm_monitor_scheduled_query_rules_alert_v2" "api_failures" {
  name                = var.scheduled_query_alert_name
  resource_group_name = var.resource_group_name
  location            = var.location

  description             = "Detect failed requests from the Azure Cloud Resume Challenge Function App."
  enabled                 = true
  evaluation_frequency    = "PT5M"
  window_duration         = "PT5M"
  severity                = 2
  auto_mitigation_enabled = true
  skip_query_validation   = false
  tags                    = {}
  target_resource_types   = []

  scopes = [
    "/subscriptions/8bb846b6-1057-42BB-A02A-7A64E6A34178/resourceGroups/rg-portfolio/providers/microsoft.insights/components/aniket-portfolio-api"
  ]

  criteria {
    query = "requests | where toint(resultCode) >= 500 | where timestamp > ago(5m)"

    time_aggregation_method = "Count"
    operator                = "GreaterThan"
    threshold               = 0

    failing_periods {
      minimum_failing_periods_to_trigger_alert = 1
      number_of_evaluation_periods             = 1
    }
  }

  action {
    custom_properties = {}
    action_groups = [
      "/subscriptions/8BB846B6-1057-42BB-A02A-7A64E6A34178/resourceGroups/rg-portfolio/providers/microsoft.insights/actionGroups/ag-portfolio-failures"
    ]
  }
}

resource "azurerm_application_insights_standard_web_test" "api_health" {
  name                    = var.availability_test_name
  resource_group_name     = var.resource_group_name
  location                = var.location
  application_insights_id = azurerm_application_insights.portfolio.id

  enabled   = true
  frequency = 900
  geo_locations = [
    "apac-sg-sin-azr"
  ]
  retry_enabled = true
  timeout       = 120

  request {
    url                              = "https://aniket-portfolio-api.azurewebsites.net/api/health"
    http_verb                        = "GET"
    follow_redirects_enabled         = false
    parse_dependent_requests_enabled = false
  }

  validation_rules {
    expected_status_code        = 200
    ssl_check_enabled           = true
    ssl_cert_remaining_lifetime = 7
  }
}

resource "azurerm_monitor_metric_alert" "api_availability" {
  tags = {
    "hidden-link:/subscriptions/8bb846b6-1057-42bb-a02a-7a64e6a34178/resourceGroups/rg-portfolio/providers/Microsoft.Insights/components/aniket-portfolio-api"                          = "Resource"
    "hidden-link:/subscriptions/8bb846b6-1057-42bb-a02a-7a64e6a34178/resourceGroups/rg-portfolio/providers/Microsoft.Insights/webTests/portfolio-api-health-check-aniket-portfolio-api" = "Resource"
  }


  name                = var.availability_metric_alert_name
  resource_group_name = var.resource_group_name

  scopes = [
    "/subscriptions/8bb846b6-1057-42bb-a02a-7a64e6a34178/resourceGroups/rg-portfolio/providers/Microsoft.Insights/components/aniket-portfolio-api",
    "/subscriptions/8bb846b6-1057-42bb-a02a-7a64e6a34178/resourceGroups/rg-portfolio/providers/Microsoft.Insights/webTests/portfolio-api-health-check-aniket-portfolio-api"
  ]

  description   = "Automatically created alert rule for availability test \"portfolio-api-health-check-aniket-portfolio-api\""
  enabled       = true
  severity      = 1
  frequency     = "PT1M"
  window_size   = "PT5M"
  auto_mitigate = false

  application_insights_web_test_location_availability_criteria {
    web_test_id           = "/subscriptions/8bb846b6-1057-42bb-a02a-7a64e6a34178/resourceGroups/rg-portfolio/providers/Microsoft.Insights/webTests/portfolio-api-health-check-aniket-portfolio-api"
    component_id          = "/subscriptions/8bb846b6-1057-42bb-a02a-7a64e6a34178/resourceGroups/rg-portfolio/providers/Microsoft.Insights/components/aniket-portfolio-api"
    failed_location_count = 1
  }

  action {
    action_group_id = "/subscriptions/8bb846b6-1057-42bb-a02a-7a64e6a34178/resourceGroups/rg-portfolio/providers/Microsoft.Insights/actionGroups/ag-portfolio-failures"
  }
  lifecycle {
    ignore_changes = [
      scopes,
      tags,
      action,
      application_insights_web_test_location_availability_criteria
    ]
  }

}
