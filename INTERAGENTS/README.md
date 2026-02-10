# INTERAGENTS

This ZIP is a **project planning template** for an inter-agent code generator (Python-only MVP).

## Contents
- `INTERAGENTS_PLAN.json`: sequence/parallel plan + mandatory PRE-FLIGHT contract.
- `CHANTIERS/`: one folder per chantier with:
  - `OUTPUTS/`
  - `INTERAGENTS_prompt_CXX.md`

## Q/A policy
Agents ask **the orchestrator** first. The orchestrator escalates to the user only if not 100% sure.
