# Alfred ClickUp Workflow - Announcement Messages

## For Alfred Forum (Share Your Workflows)

### Title: ClickUp Workflow for Alfred - Fast Task Creation & Search with Secure API Storage

### Post:
Hey Alfred community! 👋

I've created a new ClickUp workflow for Alfred that addresses many of the issues with existing workflows. After seeing several threads about broken ClickUp workflows, I built this from scratch for ClickUp 2.0.

**Key Features:**
- 🔐 Secure API key storage in macOS Keychain (no hardcoded credentials!)
- ⚡ Lightning-fast task creation with `cu <task title>`
- 🔍 Fuzzy search across all your tasks with `cus`, `cuo`, and `cul` commands
- 🏷️ Support for tags, priorities, lists, and due dates
- ✅ Quick task completion with Option+Enter
- 🎯 Works with modern ClickUp IDs (14+ characters)

**Download:** [ClickUp.alfredworkflow](link-here)
**GitHub:** https://github.com/four13co/alfred-clickup-four13

Configuration is simple - just run `cu:config` and follow the prompts. All sensitive data is stored securely in your Keychain.

Would love feedback from the community! This is actively maintained, so please report any issues on GitHub.

---

## For Reddit (r/clickup, r/macapps, r/productivity)

### Title: Just released an updated Alfred workflow for ClickUp - looking for testers!

Hey everyone,

If you're a ClickUp + Alfred user on macOS, I've just released a new workflow that fixes many issues with the older workflows that stopped working.

**What makes this different:**
- Actually works with ClickUp 2.0 API 
- Secure credential storage (Keychain, not plain text)
- Supports modern ClickUp IDs
- Fuzzy search that actually finds your tasks
- One-key shortcuts to complete tasks

I built this because the existing workflows were either broken or storing API keys insecurely. 

**Commands:**
- `cu task title` - Create a task
- `cus keyword` - Search all tasks
- `cu:config` - Easy setup wizard

GitHub: https://github.com/four13co/alfred-clickup-four13

Would love some beta testers to try it out and provide feedback!

---

## For GitHub Issues/Discussions (on old workflow repos)

### Title: Alternative workflow available for ClickUp 2.0

Hi everyone,

I noticed this workflow is no longer maintained and many users are reporting issues. I've created an updated workflow that works with ClickUp 2.0:

- ✅ Fixes the ID length validation issue
- ✅ Works with current ClickUp API
- ✅ Secure Keychain storage for API keys
- ✅ Actively maintained

You can find it here: https://github.com/four13co/alfred-clickup-four13

Not trying to step on any toes - just wanted to help fellow ClickUp users who rely on Alfred integration. Feel free to fork or contribute!

---

## For Twitter/X

### Tweet 1 (Main announcement):
🚀 Just released a new Alfred workflow for @clickup! 

Finally, a workflow that:
- Works with ClickUp 2.0 ✅
- Stores API keys securely 🔐
- Has fuzzy search that works 🔍
- Supports 14+ char IDs 📝

#Alfred #ClickUp #productivity #macOS

GitHub: [link]

### Tweet 2 (Reply thread):
Been frustrated with broken ClickUp workflows? This one actually works! 

Quick demo:
- `cu Buy groceries` → Creates task
- `cus project` → Searches all tasks
- `Option+Enter` → Completes task

Built by @four13digital

---

## For ClickUp Community/Forum

### Title: New Alfred Workflow for macOS Users - Beta Testers Wanted!

Hey ClickUp fam!

As a heavy ClickUp + Alfred user, I was frustrated when the existing workflows stopped working. So I built a new one from scratch!

**What it does:**
- Create tasks instantly from anywhere on your Mac
- Search tasks without opening ClickUp
- Complete tasks with a keyboard shortcut
- Secure API storage (no more plain text passwords!)

**Perfect for:**
- Developers who live in the terminal
- Anyone who wants to capture tasks quickly
- Power users who love keyboard shortcuts

Looking for beta testers to help make this rock solid. It's open source and free!

Download: https://github.com/four13co/alfred-clickup-four13

---

## For Hacker News (Show HN)

### Title: Show HN: Alfred Workflow for ClickUp with Secure Credential Storage

I built a new Alfred workflow for ClickUp after the existing ones broke with API changes. 

Key improvements:
- Uses macOS Keychain for API credentials (not plaintext)
- Handles modern ClickUp IDs (14+ characters) 
- Fuzzy search implementation for finding tasks
- Python 3.9+ for modern macOS compatibility

Technical details: Built with alfred-pyworkflow, uses ClickUp API v2, implements proper error handling and logging.

GitHub: https://github.com/four13co/alfred-clickup-four13

Feedback welcome, especially on the security implementation and UX flow.

---

## For Direct Messages/Emails

### Subject: New ClickUp Alfred Workflow - Looking for Feedback

Hi [Name],

I saw your post about issues with the ClickUp Alfred workflow. I've been working on an updated version that fixes those problems.

Quick highlights:
- Works with current ClickUp API
- Secure credential storage
- Fast fuzzy search
- Actively maintained

Would you be interested in testing it out? I'm looking for feedback before doing a wider release.

GitHub: https://github.com/four13co/alfred-clickup-four13

Thanks!
[Your name]

---

## Tips for Posting:

1. **Timing**: Post during peak hours (9-11 AM EST for US audiences)
2. **Engagement**: Respond quickly to questions and feedback
3. **Screenshots**: Include a GIF or screenshot showing the workflow in action
4. **Value First**: Focus on solving problems, not promoting
5. **Community Rules**: Read each community's rules before posting

## Follow-up Message Template:

Thanks for trying it out! If you run into any issues:
- Check the troubleshooting guide in the README
- Open an issue on GitHub
- The most common setup issue is the API key - make sure you're using a personal token, not the app token

Really appreciate the feedback - it helps make the workflow better for everyone!