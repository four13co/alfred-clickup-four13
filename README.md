# ClickUp Alfred Workflow

**Streamline your ClickUp task management directly from Alfred**

[![Production Release](https://github.com/four13co/alfred-clickup-four13/actions/workflows/production-release.yml/badge.svg)](https://github.com/four13co/alfred-clickup-four13/actions/workflows/production-release.yml)
[![Beta Release](https://github.com/four13co/alfred-clickup-four13/actions/workflows/beta-release.yml/badge.svg?branch=beta)](https://github.com/four13co/alfred-clickup-four13/actions/workflows/beta-release.yml)
[![Version](https://img.shields.io/badge/version-1.13-blue.svg)](https://github.com/four13co/alfred-clickup-four13/releases/latest)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://python.org)
[![Alfred](https://img.shields.io/badge/alfred-5%2B-purple.svg)](https://alfredapp.com)
[![License](https://img.shields.io/badge/license-GPL%20v2.0-red.svg)](LICENSE)

*Created by [Greg Flint](https://github.com/gregflint) • [Four13 Digital](https://github.com/four13co)*

## Overview

This Alfred workflow provides powerful integration with ClickUp 2.0, enabling you to:
- Create tasks with natural language
- Search across tasks, documents, chats, lists, folders, and spaces
- Manage your entire ClickUp workspace from Alfred
- Configure exactly what you want to search with granular toggles

Built with Python 3.9+ for maximum compatibility with modern macOS systems and featuring enhanced search capabilities across all ClickUp entity types.

![ClickUp Workflow Demo](docs/ClickUp.gif)

## ✨ Features

### 🎯 **Quick Task Creation** (`cu`)
Create ClickUp tasks with natural language parsing:
```
cu Clean the kitchen :Before my wife gets angry #Housework @h4 !1 +Personal
```
- **Title**: `Clean the kitchen`
- **Description**: `:Before my wife gets angry` 
- **Tags**: `#Housework` (with autocomplete)
- **Due Date**: `@h4` (4 hours from now)
- **Priority**: `!1` (Urgent: 1=Urgent, 2=High, 3=Normal, 4=Low)
- **List**: `+Personal` (with autocomplete)

### 🔍 **Universal Search**
- **`cus <search>`** - Search across your entire ClickUp workspace
  - Tasks with status and priority indicators
  - Documents (when enabled)
  - Chat channels and DMs (when enabled)
  - Lists with task counts (when enabled)
  - Folders with parent space info (when enabled)
  - Spaces (when enabled)
- **`cuo [search]`** - Show tasks due today or overdue
- **`cul [search]`** - Show tasks created via Alfred (filtered by default tag)

### ⚙️ **Smart Configuration** (`cu:config`)
- Secure API key storage in macOS Keychain
- Workspace, Space, Folder, and List configuration
- Toggle individual search entity types on/off
- Adjust search scope for performance vs. comprehensiveness
- Default settings for due dates, tags, and notifications
- Configuration validation with real-time API testing

### 🛡️ **Security & Privacy**
- API keys stored securely in macOS Keychain
- No sensitive data stored in plain text
- Full control over your ClickUp access

## 🚀 Installation

### Requirements
- **macOS 10.15+** (Catalina or later)
- **Alfred 4+** with [Powerpack](https://www.alfredapp.com/powerpack/)
- **ClickUp 2.0** account
- **Python 3.9+** (included with macOS)

### Quick Install

#### Stable Release
1. **Download** the [latest stable release](https://github.com/four13co/alfred-clickup-four13/releases/latest)
2. **Double-click** the `.alfredworkflow` file to install
3. **Configure** your ClickUp credentials (see setup below)

#### Beta Release (New Features)
1. **Download** the [latest beta release](https://github.com/four13co/alfred-clickup-four13/releases)
2. Look for releases marked "Pre-release"
3. **Test** new features and report feedback

## ⚡ Quick Start

### 1. Get Your ClickUp API Key
1. Open ClickUp → Profile Icon (bottom left) → **Apps**
2. Click **Generate API Key**
3. Copy your API key (treat it like a password!)

### 2. Configure the Workflow
Type `cu:config` in Alfred and set up:

| Setting | Description | Example |
|---------|-------------|---------|
| **API Key** | Your ClickUp API token | `pk_12345_abc...` |
| **Workspace ID** | ClickUp Workspace ID | `2181159` |
| **Space ID** | Space for tags/priorities | `2288348` |
| **List ID** | Default list for new tasks | `4696187` |
| **Default Tag** | Auto-added to all tasks | `alfred-created` |

### 3. Find Your IDs
**Workspace ID**: Go to any task → URL shows `https://app.clickup.com/2181159/...` → Use `2181159`

**Space ID**: Click Space icon → URL shows `https://app.clickup.com/.../s/2288348` → Use `2288348`

**List ID**: Hover over a List → Click ⋯ → Click 🔗 → URL shows `https://app.clickup.com/.../li/4646883` → Use `4646883`

### 4. Start Creating Tasks!
```
cu Review Q4 budget :Need to finish by Friday #finance @fri !2
```

## 📚 Usage Guide

### Task Creation (`cu`)

**Basic Syntax:**
```
cu <Title> [:<Description>] [#<Tag>] [@<Due Date>] [!<Priority>] [+<List>]
```

**Due Date Options:**
- `@m30` - 30 minutes from now
- `@h2` - 2 hours from now  
- `@d3` - 3 days from now
- `@w1` - 1 week from now
- `@n2` - 2 months from now (shorter months will adjust to last day of month if encountered)
- `@y1` - 1 year from now (currently just adds 365 days)
- `@today` or `@tod` - Today
- `@tomorrow` or `@tom` - Tomorrow
- `@monday` or `@mon` - Next Monday
- `@2024-12-31` - Specific date
- `@2024-12-31 14.00` - Specific date and time
- `@14.00` - Today at 2 PM

**Priority Levels:**
- `!1` - 🔴 Urgent
- `!2` - 🟡 High  
- `!3` - 🟢 Normal (default)
- `!4` - 🔵 Low

**Examples:**
```bash
# Simple task
cu Call mom

# Task with description and tag
cu Review proposal :Check the new client requirements #work

# Complex task with all options
cu Deploy website :Final review and testing #dev @fri !1 +Projects

# Multiple tags
cu Plan vacation #personal #travel @w2 !3
```

### Universal Search

**Search All ClickUp Items (`cus`)**
```bash
cus budget          # Find all items containing "budget"
cus shopify         # Search tasks, docs, chats, lists, folders, spaces
cus [Open]          # Filter by task status
```

**Visual Indicators:**
- **[Open/Closed]** - Task status with priority-based icons:
  - 🔴 Urgent priority
  - 🟡 High priority  
  - 🟢 Normal priority
  - 🔵 Low priority
- **[Doc]** - ClickUp Documents
- **[Chat]** - Chat channels
- **[DM]** - Direct messages
- **[List]** - Lists with task count
- **[Folder]** - Folders with parent space
- **[Space]** - ClickUp Spaces

**Open Tasks (`cuo`)**
```bash
cuo                 # Show all due/overdue tasks
cuo urgent          # Filter overdue tasks
```

**Alfred-Created Tasks (`cul`)**
```bash
cul                 # Show all tasks created via Alfred
cul review          # Filter Alfred tasks
```

### Keyboard Shortcuts
- **Enter** → Open task in ClickUp (web)
- **⌥ + Enter** → Close/complete task
- **⌥ + Enter** (creation) → Create task and open in ClickUp

## 🔧 Advanced Configuration

### Search Entity Types
Configure exactly what you want to search with individual toggles:

1. Type `cu:config` → Select "Configure Search Types"
2. Toggle each entity type on/off:
   - ✓ **Tasks** - Always enabled (core functionality)
   - ○/✓ **Documents** - Search ClickUp Docs by title
   - ○/✓ **Chat Channels** - Search chat channels and DMs
   - ○/✓ **Lists** - Search all lists with task counts
   - ○/✓ **Folders** - Search folders across all spaces
   - ○/✓ **Spaces** - Search workspace spaces

Click any toggle to enable/disable that search type.

### Search Scope
Control the breadth of task searches for better performance:
- **Performance (List)** - Search only your default list - fastest
- **Balanced (Folder)** - Search your entire folder - moderate speed
- **Comprehensive (Space)** - Search your entire space - slowest
- **Auto** - Starts narrow and expands automatically if few results found

Configure via `cu:config` → "Set Search Scope"

### Default Settings
- **Default Due Date**: Set automatic due date (e.g., `h2` for 2 hours)
- **Default Tag**: Auto-added to every task for easy filtering
- **Notifications**: Toggle desktop notifications on task creation

### API Rate Limits
- Tags cached for 10 minutes
- Lists cached for 2 hours
- Automatic cache invalidation on errors

## 🛠️ Technical Details

### Architecture
- **Python 3.9+** for modern macOS compatibility
- **alfred-pyworkflow** library for Alfred integration
- **ClickUp API v2 & v3** hybrid approach for maximum functionality
- **Secure keychain storage** for credentials
- **Intelligent caching** for tags and lists
- **Client-side filtering** for entities without native search

### File Structure
```
alfred-clickup-four13/
├── main.py              # Main workflow entry point
├── createTask.py        # Task creation logic
├── getTasks.py          # Task search and retrieval
├── closeTask.py         # Task completion
├── config.py            # Configuration interface
├── configStore.py       # Settings storage
├── fuzzy.py             # Fuzzy search functionality
├── workflow/            # Alfred workflow library
├── info.plist           # Alfred workflow configuration
└── *.png               # UI icons
```

### Customization
All workflow behavior can be customized through:
- Alfred workflow variables
- ClickUp configuration settings
- Python script modifications

## 🐛 Troubleshooting

### Common Issues

**"We are missing some settings"**
- Run `cu:config` and set up all required fields
- Use `cu:config validate` to test your configuration

**"Error connecting to ClickUp"**
- Check your internet connection
- Verify your API key is correct
- Ensure your Workspace/Space/List IDs are valid

**Tasks not appearing in search**
- Check your hierarchy limit settings
- Verify you have access to the configured Workspace
- Clear cache with `cu:config cache`

### Debug Mode
Enable debug logging by editing Python files:
```python
DEBUG = 2  # 0=Off, 1=Some, 2=All
```

View logs in Alfred's debug console (Alfred → Workflows → ClickUp → Debug).

## 🤝 Contributing

We welcome contributions! Here's how to help:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request to the `beta` branch

### Development Workflow
- **Feature branches** → PR to `beta` → Test → PR to `main`
- **Beta releases** automatically created from `beta` branch
- **Production releases** automatically created from `main` branch
- All PRs automatically validated by CI/CD pipeline

### Development Setup
```bash
git clone https://github.com/four13co/alfred-clickup-four13.git
cd alfred-clickup-four13
# Edit Python files with your favorite editor
# Test with: /usr/bin/python3 main.py "test input"
```

## 📝 Changelog

### v1.14 (2025-09-26) - Beta
- **📅 Enhanced Due Date Autocomplete**: for much faster due date options
- **📅 Added Month Relative Dates**: e.g., `@n1` for 1 month etc.
- **📅 Added Date related Icons**: for better visual cues

### v1.13 (2025-08-02) - Beta
- **🔍 Universal Search**: Search across all ClickUp entity types
- **🎛️ Toggle Configuration**: Individual on/off switches for each search type
- **📁 Enhanced Search**: Added Lists, Folders, and Spaces search
- **💬 Chat Integration**: Search chat channels and direct messages
- **📄 Document Search**: Search ClickUp Docs by title (v3 API)
- **⚡ Performance Options**: Configurable search scope for speed
- **🏷️ Visual Indicators**: Clear prefixes for different entity types
- **🔧 CI/CD Pipeline**: Automated beta and production releases

### v1.0.0 (2025-07-30)
- **🚀 Python 3.9+ Migration**: Complete upgrade from Python 2.7
- **⚡ Modern Compatibility**: Works with latest macOS versions  
- **🔧 Library Updates**: Migrated to alfred-pyworkflow
- **🛡️ Enhanced Security**: Improved keychain integration
- **📚 Documentation**: Comprehensive setup and usage guides
- **🎨 UI Improvements**: Refined user experience

### Previous Versions
See [releases](https://github.com/four13co/alfred-clickup-four13/releases) for complete history.

## 📄 License

This project is licensed under the GNU General Public License v2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Original Concept**: Based on alfred-clickup-msk by Michael Schmidt-Korth
- **Alfred Workflow Library**: Built with alfred-pyworkflow by Thomas Harr
- **ClickUp Team**: For providing an excellent API
- **Alfred Team**: For creating the amazing Alfred app

## 📞 Support

**Need Help?**
- 📖 Check the [Wiki](https://github.com/four13co/alfred-clickup-four13/wiki)
- 🐛 Report issues: [GitHub Issues](https://github.com/four13co/alfred-clickup-four13/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/four13co/alfred-clickup-four13/discussions)

**Four13 Digital**
- 🌐 Website: [four13.digital](https://four13.digital)
- 💼 GitHub: [@four13co](https://github.com/four13co)
- 👨‍💻 Author: [Greg Flint](https://github.com/gregflint)

---

**⚡ Made with ❤️ by Four13 Digital**

*Streamline your workflow. Amplify your productivity.*