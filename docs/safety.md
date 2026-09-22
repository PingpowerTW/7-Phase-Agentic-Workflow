# Safety & Guardrails Policy

This document defines the safety boundaries and human gate policies for autonomous and assisted AI loops in this repository.

## Path Denylist
The loop must NEVER auto-edit the following paths without explicit human approval:
```
**/.env
**/.env.*
**/secrets/**
**/credentials/**
**/*_key*
**/*_secret*
**/.terraform/**
**/k8s/production/**
**/migrations/**
**/auth/**
**/payments/**
**/billing/**
```

## Max Files Limit
Single-run modifications are capped at **8 files**. Any task exceeding this threshold automatically halts and escalates to a human maintainer.

## Auto-Merge Policy
**Default: NO auto-merge.**
Only explicit documentation (`docs/**`, `*.md`) and isolated unit test additions may be auto-merged if tests pass.

## Human Escalation Gates
Human intervention is strictly required for:
1. Touching any path in the Path Denylist.
2. Changes touching > 8 files.
3. Third failed fix attempt on the same item.
4. Token budget extension requests when hitting the daily cap.
