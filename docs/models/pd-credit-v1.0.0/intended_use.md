---
document_type: intended_use
title: Product Requirements and Intended-Use Statement
model_version: pd-credit-v1.0.0
status: complete
template_version: 1
---

# Intended-Use Statement — pd-credit-v1.0.0

> Portfolio simulation. This model is not credit advice, not a production lending decision
> engine, and not represented as compliant with any specific regulation.

## Business purpose

Estimate the probability that a consumer instalment loan defaults within the observation window so that portfolio risk can be ranked and monitored. Portfolio simulation only; not used for any real lending decision.

## Intended use

Rank-ordering and monitoring of PD on the synthetic/licensed loan-performance dataset inside ModelGuard.

## Out-of-scope uses

Credit decisions, pricing, collections prioritisation, any real borrower, and any regulatory reporting.

## Users and decisions

Data scientist (develops), model risk reviewer (approves/rejects), risk leader (reads the executive summary). No automated decision is taken.
