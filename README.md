# ocr-school-bot

> **Old project** — built for a school Discord community (got 96% on the A-level project!). May use outdated library versions (discord-py-slash-command).

A Discord bot for school servers. Handles member onboarding (name verification via DM), homework mention alerts, reporting, slash commands, and more.

## Features

- Member join flow: DMs new members to collect their real name, sends an approval request to moderators
- Banned word detection with mod alerts
- Slash commands: `/ping`, `/report`, `/rockpaperscissors`
- SQLite-backed school guild config

## Setup

1. Install dependencies: `pip install discord.py discord-py-slash-command python-dotenv regex`
2. Copy `.env.example` to `.env`:
   ```
   DISCORD_TOKEN=your_token_here
   ```
3. Run `python main.py`
