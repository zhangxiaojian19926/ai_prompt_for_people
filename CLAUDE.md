# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Directory Purpose

This `prompt/` directory is a data workspace for storing and organizing prompt engineering data as part of the broader `bigmodel_learn` curriculum (an AI/LLM learning repository).

## Key File

- **prompt_jsonl.xlsx** - The primary data file containing prompt data, likely in JSONL format converted to Excel for easier viewing and editing

## Context

This directory is one of three in the parent `bigmodel_learn` repository:
- `1.datawhale_learn/` - "Hello-Agents" tutorial (AI Agent learning materials)
- `2.vibe_coding/` - "Vibe Coding" guide (AI-assisted programming methodology)
- `prompt/` - This directory (prompt data storage workspace)

## Working with Prompts

When working with the Excel file:
- The file contains prompt data in JSONL format converted to Excel
- Use appropriate tools (like Python with pandas/openpyxl) for programmatic access
- Consider format conversions between JSONL and Excel as needed

## Configuration

- `.claude/settings.local.json` contains Claude Code permissions
- Currently allows Bash tool to use `find` command for file searching
