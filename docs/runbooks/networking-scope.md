# Architecture Decision: Project 2 Network Infrastructure Scope

- Decision date: 24 November 2026
- Decision: Do not provision a dedicated VNet/subnet or Function App private endpoint for the current Project 2 baseline.
- Disposition: The Azure Network Infrastructure feature is closed as assessed / not required for the current public serverless architecture. No VNet or subnet deployment is claimed.

## 1. Current application flow

The portfolio is a public-facing website. Visitors use the Azure Static Web App and its browser frontend calls the shared HTTP-triggered Function App. The Function App uses Cosmos DB and sends telemetry to Application Insights. Project 2 adds monitoring, analytics, cost visibility and operational automation around this existing application.

A private inbound endpoint on the Function App would make the API inaccessible to ordinary public portfolio visitors unless an additional public ingress/proxy architecture were designed and operated. That is outside the current project scope.

## 2. Existing controls

The current environment uses these controls, verified during the Project 1 infrastructure reconciliation:

- Function App HTTPS-only is enabled.
- Cosmos DB local/key authentication is disabled; data access requires Microsoft Entra ID authorization.
- Cosmos DB has an IP firewall configuration (32 entries at the last inspection, including the Azure-datacenter exception).
- The Function App uses a managed identity for its Azure resource access.
- Terraform state is stored in separate private Project 1 and Project 2 containers in aniketterraformstate26.

The Cosmos DB Azure-datacenter exception is broader than a narrow workload allowlist. It is explicitly documented as a remaining network limitation; Entra ID authentication and Cosmos DB RBAC are still required. It should not be described as equivalent to private networking.

## 3. Why a dedicated VNet is not part of the baseline

A VNet is useful when an application must reach private endpoints, network-restricted storage or other private services, or when outbound traffic must be routed and filtered through a controlled subnet. It is not a prerequisite for every public Azure Functions application.

The shared Function App uses the Flex Consumption hosting model. Azure Functions supports regional VNet integration for outbound connectivity on Flex Consumption and supports private endpoints for supported hosting plans. Those options are available if a private networking requirement is introduced; they are not required merely to host the current public HTTP API.

The current design does not document a requirement for a private-only Cosmos DB endpoint, private-only storage, private upstream service or fixed-egress network policy. Provisioning a VNet without such a requirement would add resources and operational complexity without delivering a currently required application capability.

## 4. Revisit triggers

Reopen this decision before implementing any of the following:

- Cosmos DB public network access is disabled and access is moved to a private endpoint.
- Function host/runtime storage or another dependency becomes network-restricted.
- A private upstream service is introduced.
- A security requirement mandates all outbound Function App traffic to route through a VNet, NSGs or a NAT Gateway.
- The public API ingress architecture is redesigned to support private inbound connectivity.

At that point, design the VNet, dedicated integration subnet, private endpoints, DNS, routing and access rules together. Do not add only a VNet without the associated name resolution and service restrictions.

## 5. Verification and limitations

The current state is a public serverless architecture with HTTPS, managed identity, Cosmos DB firewall rules and Entra ID authorization. This document records an architecture scope decision, not a claim that a VNet, subnet, NSG, NAT Gateway or private endpoint was deployed.

Microsoft references:

- [Azure Functions networking options](https://learn.microsoft.com/azure/azure-functions/functions-networking-options)
- [Use private endpoints to integrate Azure Functions with a virtual network](https://learn.microsoft.com/azure/azure-functions/functions-create-vnet)
