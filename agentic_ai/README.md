# RetailMind - Agentic AI

## Overview

The `agentic_ai` module is the Agentic AI orchestration layer of RetailMind.

It handles:

- Shopping intent understanding
- Shopping mission extraction
- Customer profile retrieval
- Personalized recommendation retrieval
- Product ranking
- Bundle creation
- Recommendation explanation
- Quality checking
- Re-planning when required
- API-based integration with the rest of the system

---

## Architecture

```text
User
 |
 v
Supervisor Agent
 |
 v
Intent + Shopping Mission
 |
 v
Required Tools
 |
 +---- Profile Tool
 |
 +---- Recommendation Tool
 |
 +---- Product Tool
 |
 v
Ranking
 |
 v
Bundle (when required)
 |
 v
Explanation
 |
 v
Quality Check
 |
 +------ FAIL ------> Re-plan
 |
 +------ PASS ------> Final Response