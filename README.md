# Claude Code Skills

Personal collection of custom Claude Code skills for enhancing development workflow.

## What are Skills?

Skills are reusable, context-aware prompts that guide Claude Code in handling specific tasks. They provide structured workflows, best practices, and domain-specific knowledge.

## Available Skills

### [meeting-summary](skills/meeting-summary/)
智能会议总结助手 - 将会议录音/内容整理成结构化会议纪要。

**Usage:**
- 会议录音文件（音频或视频）
- 会议逐字稿/转录文本
- 会议笔记或草稿
- 需要整理的会议记录

## Installation

To use these skills in Claude Code:

1. Clone this repository to your local machine
2. Install skills using Claude Code's skill management system

## Development

Adding a new skill:

1. Create a new directory under `skills/`
2. Create a `SKILL.md` file with the following format:

```yaml
---
name: skill-name
description: Brief description of what this skill does
---

# Skill Title

## Usage
When to use this skill...

## Workflow
Step-by-step instructions...
```

3. Test the skill thoroughly before committing

## License

MIT
