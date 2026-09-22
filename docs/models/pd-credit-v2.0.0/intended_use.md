---
document_type: intended_use
title: Product Requirements and Intended-Use Statement
model_version: pd-credit-v2.0.0
status: complete
template_version: 1
---

# Intended-Use Statement — pd-credit-v2.0.0

> Portfolio simulation. This model is not credit advice, not a production lending decision
> engine, and not represented as compliant with any specific regulation.

## Business purpose

Estimate the probability that a credit-card holder defaults on next month's payment from six months of billing and repayment history, so that portfolio risk can be ranked and monitored. Portfolio simulation on the public UCI 350 dataset; not used for any real lending decision.

## Intended use

Rank-ordering and monitoring of next-month default probability on the UCI 350 credit-card dataset.

## Out-of-scope uses

Credit decisions, pricing, collections prioritisation, any real borrower, and any regulatory reporting.

## Users and decisions

Data scientist (develops), model risk reviewer (approves/rejects), risk leader (reads the executive summary). No automated decision is taken.
