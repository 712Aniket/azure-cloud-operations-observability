variable "resource_group_name" {
  description = "Existing Azure resource group"
  type        = string
  default     = "rg-portfolio"
}

variable "location" {
  description = "Azure resource location"
  type        = string
  default     = "centralindia"
}

variable "application_insights_name" {
  description = "Existing Application Insights component"
  type        = string
  default     = "aniket-portfolio-api"
}

variable "action_group_name" {
  description = "Existing monitoring Action Group"
  type        = string
  default     = "ag-portfolio-failures"
}

variable "scheduled_query_alert_name" {
  description = "Existing API failure alert"
  type        = string
  default     = "alert-portfolio-api-failures"
}

variable "availability_test_name" {
  description = "Existing availability web test"
  type        = string
  default     = "portfolio-api-health-check-aniket-portfolio-api"
}

variable "availability_metric_alert_name" {
  description = "Existing availability metric alert"
  type        = string
  default     = "portfolio-api-health-check-aniket-portfolio-api"
}

variable "workbook_id" {
  description = "Existing Azure Monitor Workbook resource ID"
  type        = string
  default     = "28236c19-2756-48f5-8e4e-a176a4a8210d"
}
