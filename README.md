# BOT-IMAGE 📸

A comprehensive Discord and Telegram bot application for managing and distributing photo collections with integrated Cloudflare Worker support. Features production-ready Docker deployment and automated GitHub Actions CI/CD pipeline.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation & Deployment](#installation--deployment)
- [Configuration](#configuration)
- [Usage](#usage)
- [CI/CD Pipeline](#cicd-pipeline)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Introduction

**BOT-IMAGE** is a feature-rich bot application designed to streamline photo collection management and distribution across Discord and Telegram platforms. It leverages Cloudflare Workers and KV storage for reliable, scalable cloud operations.

### Key Capabilities

- **Multi-Platform Support**: Works with both Discord and Telegram bots
- **Album Management**: Create, organize, and publish photo albums with auto-incrementing codes
- **Cloud Storage Integration**: Cloudflare KV for metadata and file organization
- **Web Gallery**: Cloudflare Worker-powered web interface for album browsing
- **File Distribution**: Support for photos, videos, and attachable files
- **Category System**: Organize albums by customizable categories
- **Password Protection**: Optional password-protected albums
- **Channel Integration**: Forward files to Telegram channels for direct linking
- **Long Polling**: Reliable bot operation without webhooks
- **Docker Ready**: Production-grade containerized deployment

### Tech Stack

- **Backend**: Python 3.10 with python-telegram-bot library
- **Cloud Storage**: Cloudflare KV
- **Web Runtime**: Cloudflare Workers (JavaScript)
- **Containerization**: Docker & Docker Compose
- **CI/CD**: GitHub Actions
- **Image Registry**: GitHub Container Registry (GHCR)

---

## Features

✨ **Core Features:**

- **Simple Album Creation** - Start album sessions with a single command (`/start_album`)
- **Photo Collection** - Upload multiple photos to build comprehensive albums
- **Title Management** - Set album titles using text messages
- **Category Navigation** - Switch between album categories via inline keyboard (`/nav`)
- **Password Protection** - Secure albums with optional passwords (`/set_pass`)
- **Auto-incrementing Codes** - Albums automatically assigned codes (a01, a02, a03...)
- **Cloudflare KV Storage** - Reliable, fast cloud storage for album metadata
- **File Forwarding** - Forward videos and documents to Telegram channels for persistent links
- **Album Deletion** - Remove published albums with confirmation (`/delete`)
- **User Whitelist** - Admin controls for allowed users (`/allow`, `/list_users`)
- **Docker Support** - Production-ready containerized deployment
- **GitHub Actions** - Automated Docker image builds and GHCR publishing
- **Cloudflare Worker Gallery** - Web-based album gallery with pagination and search

---

## Project Structure

```
BOT-IMAGE/
├── bot.py                    # Main Telegram/Discord bot implementation (Python)
├── _worker.js               # Cloudflare Worker script for web gallery
├── Dockerfile               # Docker container configuration
├── requirements.txt         # Python dependencies
├── README.md                # This documentation
├── .gitignore               # Git ignore patterns
├── .github/
│   └── workflows/
│       └── docker-build.yml # GitHub Actions CI/CD pipeline
└── KV_WRITE_ANALYSIS.md     # Cloudflare KV integration notes
```

### File Descriptions

| File | Purpose |
|------|---------|
| **bot.py** | Main application handling Telegram/Discord commands and message processing |
| **_worker.js** | Cloudflare Worker script that renders the web-based album gallery with pagination, search, and category filtering |
| **Dockerfile** | Docker configuration (Python 3.10-slim base image) for containerized deployment |
| **requirements.txt** | Python package dependencies (python-telegram-bot, requests) |
| **docker-build.yml** | GitHub Actions workflow for automatic Docker image building and GHCR publishing |

---

## Prerequisites

### For Local Development

| Requirement | Minimum Version | Purpose |
|-------------|-----------------|---------|
| **Python** | 3.10+ | Required to run bot.py directly |
| **pip** | Latest | Python package manager for installing dependencies |
| **Git** | Any | Version control and repository cloning |

### For Docker Deployment

| Requirement | Minimum Version | Purpose |
|-------------|-----------------|---------|
| **Docker** | 24.0+ | Container runtime and image management |
| **Docker Compose** | 2.0+ | Multi-container orchestration (optional) |

### For Telegram Bot

| Requirement | How to Obtain |
|-------------|---------------|
| **Telegram Account** | — | Required to use Telegram API |
| **Bot Token** | Create via [@BotFather](https://t.me/botfather) using `/newbot` command |

### For Discord Bot (Future Expansion)

| Requirement | How to Obtain |
|-------------|---------------|
| **Discord Account** | — | Required for Discord bot operations |
| **Developer Portal Access** | [Discord Developers](https://discord.com/developers/applications) | Create bot application and generate token |

### For Cloudflare Integration

| Requirement | How to Obtain |
|-------------|---------------|
| **Cloudflare Account** | Sign up at [cloudflare.com](https://cloudflare.com) | Required for KV storage and Workers |
| **KV Namespace** | Cloudflare Dashboard → Workers & Pages → KV | Create namespace for album data storage |
| **Account ID** | Visible in Cloudflare Dashboard URL | Used in API requests |
| **API Token** | My Profile → API Tokens | Create token with `Account.Workers KV Storage` permissions |

### For GitHub Actions & GHCR

| Requirement | Details |
|-------------|---------|
| **GitHub Repository** | Push access to your GitHub repository |
| **GITHUB_TOKEN** | Automatically provided by GitHub Actions |
| **GHCR Access** | Automatically available for GitHub users |

### Network Requirements

- **Outbound HTTPS** to `api.telegram.org` (Telegram API)
- **Outbound HTTPS** to Cloudflare API endpoints (`api.cloudflare.com`)
- **Outbound HTTPS** to Discord API (if using Discord bot)
- Container resources: Minimum 512 MB RAM for Python runtime

---

## Installation & Deployment

### Method 1: Local Python Execution

**Best for:** Development, testing, or single-instance deployments

**Steps:**

1. **Clone the repository**
   ```bash
   git clone https://github.com/tyr-eamon/BOT-IMAGE.git
   cd BOT-IMAGE
   ```

2. **Create a Python virtual environment** (recommended)
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Upgrade pip and install dependencies**
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Create environment configuration file**
   ```bash
   cat > .env << 'EOF'
   # Telegram Bot Configuration
   BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN

   # Cloudflare Configuration
   CF_ACCOUNT_ID=your_cloudflare_account_id
   CF_NAMESPACE_ID=your_kv_namespace_id
   CF_API_TOKEN=your_cloudflare_api_token

   # Worker Configuration
   WORKER_BASE_URL=https://your-worker.workers.dev

   # Telegram Channel Configuration (Optional)
   CHANNEL_ID=0
   CHANNEL_LINK_PREFIX=

   # Album Categories (Optional)
   CATEGORIES=Popular Cosplay,Video Cosplay,Explore Categories,Best Cosplayer
   EOF
   ```

5. **Load environment variables**
   ```bash
   # Option A: Export variables
   export $(grep -v '^#' .env | xargs)

   # Option B: Use direnv (recommended for development)
   direnv allow
   ```

6. **Run the bot**
   ```bash
   python bot.py
   ```

   Output should show: `Bot running...`

**Managing the process in production (local):**
- Use `systemd` service file
- Use `supervisord` for process management
- Use `tmux` or `screen` for session management
- Keep the terminal open or redirect to a log file:
  ```bash
  python bot.py > bot.log 2>&1 &
  ```

---

### Method 2: Docker Container Deployment

**Best for:** Consistent environments, production deployments, cloud platforms

#### Option A: Build and Run Locally

1. **Build Docker image from repository**
   ```bash
   docker build -t bot-image:local .
   ```

2. **Create environment file**
   ```bash
   cat > .env << 'EOF'
   BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
   CF_ACCOUNT_ID=your_cloudflare_account_id
   CF_NAMESPACE_ID=your_kv_namespace_id
   CF_API_TOKEN=your_cloudflare_api_token
   WORKER_BASE_URL=https://your-worker.workers.dev
   CHANNEL_ID=0
   CHANNEL_LINK_PREFIX=
   CATEGORIES=Popular Cosplay,Video Cosplay,Explore Categories
   EOF
   ```

3. **Run container**
   ```bash
   docker run -d \
     --name bot-image \
     --restart unless-stopped \
     --env-file .env \
     bot-image:local
   ```

4. **Verify container is running**
   ```bash
   docker ps
   docker logs -f bot-image
   ```

#### Option B: Use Pre-built GHCR Image

1. **Authenticate with GitHub Container Registry** (if private)
   ```bash
   echo "$GHCR_TOKEN" | docker login ghcr.io -u YOUR_USERNAME --password-stdin
   ```

2. **Pull the latest published image**
   ```bash
   # Latest version
   docker pull ghcr.io/tyr-eamon/bot-image:latest

   # Or pin to specific commit
   docker pull ghcr.io/tyr-eamon/bot-image:COMMIT_SHA
   ```

3. **Run the pulled image**
   ```bash
   docker run -d \
     --name bot-image \
     --restart unless-stopped \
     --env-file .env \
     ghcr.io/tyr-eamon/bot-image:latest
   ```

#### Docker Container Management

```bash
# View logs
docker logs -f bot-image

# Stop container
docker stop bot-image

# Remove container
docker rm bot-image

# Restart container
docker restart bot-image

# View container resource usage
docker stats bot-image
```

---

### Method 3: Docker Compose Deployment

**Best for:** Multi-service deployments, simplified management

1. **Create docker-compose.yml**
   ```yaml
   version: '3.8'

   services:
     bot-image:
       image: ghcr.io/tyr-eamon/bot-image:latest
       container_name: bot-image
       restart: unless-stopped
       env_file:
         - .env
       logging:
         driver: json-file
         options:
           max-size: "10m"
           max-file: "3"
   ```

2. **Start services**
   ```bash
   docker compose up -d
   ```

3. **Manage services**
   ```bash
   # View logs
   docker compose logs -f bot-image

   # Stop services
   docker compose down

   # Rebuild and restart
   docker compose up -d --build
   ```

---

### Method 4: Cloudflare Worker Deployment

**Best for:** Serverless web gallery, minimal infrastructure, automatic scaling

The `_worker.js` file provides a complete web-based photo gallery interface for browsing albums published to Cloudflare KV.

#### Prerequisites for Worker Deployment

1. Cloudflare account with Workers enabled
2. KV namespace created and bound to the Worker
3. `wrangler` CLI installed: `npm install -g wrangler`

#### Deployment Steps

1. **Install Wrangler CLI** (if not already installed)
   ```bash
   npm install -g wrangler
   ```

2. **Create wrangler.toml in repository root**
   ```toml
   name = "bot-image-worker"
   main = "_worker.js"
   compatibility_date = "2024-01-01"
   type = "service"

   [env.production]
   routes = [
     { pattern = "your-domain.com/*", zone_name = "your-domain.com" }
   ]
   
   kv_namespaces = [
     { binding = "ALBUMS", id = "YOUR_KV_NAMESPACE_ID" }
   ]

   [env.production.vars]
   CATEGORIES = "Popular Cosplay,Video Cosplay,Explore Categories"
   BOT_TOKEN = "YOUR_BOT_TOKEN"
   ```

3. **Authenticate with Cloudflare**
   ```bash
   wrangler login
   ```

4. **Deploy to Cloudflare Workers**
   ```bash
   wrangler deploy --env production
   ```

5. **Access your gallery**
   ```
   https://your-worker.workers.dev/list
   ```

#### Worker Configuration

Environment variables in Cloudflare Dashboard:

| Variable | Required | Description |
|----------|----------|-------------|
| `ALBUMS` | ✅ | KV Namespace binding to store albums |
| `BOT_TOKEN` | ✅ | Telegram bot token (for file proxying) |
| `CATEGORIES` | Optional | Comma-separated category list for sidebar navigation |

#### Worker Features

- **Gallery Listing** - Browse all albums with pagination
- **Category Filtering** - Filter albums by category
- **Search** - Search albums by title
- **Album Details** - View album photos, metadata, and files
- **File Proxy** - Proxy Telegram files through Worker
- **Responsive Design** - Mobile-optimized interface
- **Dark Mode** - Eye-friendly dark theme
- **Password Protection** - Optional password-protected albums

---

## Configuration

### Environment Variables Reference

**Telegram Bot Setup:**

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `BOT_TOKEN` | ✅ | `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11` | Telegram Bot API token from [@BotFather](https://t.me/botfather) |

**Cloudflare Configuration:**

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `CF_ACCOUNT_ID` | ✅ | `abcd1234efgh5678ijkl` | Your Cloudflare account ID |
| `CF_NAMESPACE_ID` | ✅ | `1234567890abcdef` | KV namespace ID for storing albums |
| `CF_API_TOKEN` | ✅ | `v1.0123456789abcdef...` | Cloudflare API token with KV permissions |

**Worker Configuration:**

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `WORKER_BASE_URL` | Optional | `https://example.workers.dev` | Base URL of your Cloudflare Worker for album links |

**Telegram Channel Configuration:**

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CHANNEL_ID` | Optional | `0` | Telegram channel ID for forwarding files (must include `-100` prefix). Set to `0` to disable |
| `CHANNEL_LINK_PREFIX` | Optional | (empty) | URL prefix for channel links (e.g., `https://t.me/c/1234567890` - without `-100` suffix) |

**Album Categories:**

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CATEGORIES` | Optional | `Popular Cosplay,Video Cosplay,...` | Comma-separated list of album categories for the `/nav` command |

### Sample .env File

```dotenv
# Telegram Bot
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# Cloudflare
CF_ACCOUNT_ID=abcd1234efgh5678ijklmnopqrst
CF_NAMESPACE_ID=1234567890abcdef1234567890abcdef
CF_API_TOKEN=v1.0123456789abcdef0123456789abcdef0123456789

# Worker
WORKER_BASE_URL=https://bot-gallery.example.workers.dev

# Channel (Optional)
CHANNEL_ID=-1001234567890
CHANNEL_LINK_PREFIX=https://t.me/c/1234567890

# Categories (Optional)
CATEGORIES=Popular Cosplay,Video Cosplay,Explore Categories,Best Cosplayer,Level Cosplay,Top Cosplay
```

### Obtaining Credentials

#### Telegram Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow prompts to create your bot
4. Copy the API token provided (format: `123456:ABC-DEF...`)

#### Cloudflare Account ID

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Right sidebar shows **Account ID** under your profile
3. Or visible in dashboard URL: `dash.cloudflare.com/ACCOUNT_ID/...`

#### Cloudflare KV Namespace

1. Dashboard → Workers & Pages → KV
2. Click **Create Namespace**
3. Enter namespace name (e.g., `bot-albums`)
4. Copy the **Namespace ID**

#### Cloudflare API Token

1. Dashboard → My Profile → API Tokens
2. Click **Create Token**
3. Choose **Edit Cloudflare Workers** template (recommended) or **Custom Token**
4. Ensure permissions include `Account.Workers KV Storage`
5. Create and copy the token

#### Discord Bot Token (Future)

1. Visit [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application**
3. Go to **Bot** section → **Add Bot**
4. Under TOKEN, click **Copy**
5. Set as `DISCORD_BOT_TOKEN` environment variable

---

## Usage

### Starting the Bot

#### Local Python
```bash
python bot.py
```

#### Docker
```bash
docker run -d --name bot-image --env-file .env ghcr.io/tyr-eamon/bot-image:latest
docker logs -f bot-image
```

#### Docker Compose
```bash
docker compose up -d
docker compose logs -f bot-image
```

### Bot Commands

| Command | Parameters | Description | Owner Only |
|---------|-----------|-------------|-----------|
| `/start` | — | Display welcome message and available commands | No |
| `/start_album` | — | Begin a new album collection session | No |
| `/end_album` | — | Save and publish the current album to Cloudflare KV | No |
| `/nav` | — | Display category selection keyboard | No |
| `/set_pass` | `<password>` | Set a password for the current album | No |
| `/delete` | `<album_code>` | Delete a published album (confirmation required) | No |
| `/allow` | `<user_id>` | Add a user ID to whitelist (admin only) | ✅ |
| `/list_users` | — | Display all whitelisted user IDs (admin only) | ✅ |

### Workflow Example: Creating and Publishing an Album

#### Step 1: Start the Bot
```
👤 User: /start
🤖 Bot: 
  📸 Bot Ready (Channel Mode)
  🔹 /start_album - Start new album
  🔹 Direct message - Set title
  🔹 /nav - Select category
  🔹 /set_pass <password> - Set password
  🔹 /end_album - Publish album
  🔸 /delete <code> - Delete album
  🔸 /allow <id> - Add whitelist user
```

#### Step 2: Create Album
```
👤 User: /start_album
🤖 Bot: 🟦 Album session started! Default category: Popular Cosplay
        Please send the title directly.
```

#### Step 3: Set Album Title
```
👤 User: Summer Vacation 2024
🤖 Bot: ✅ Title set to: Summer Vacation 2024
        (/nav to change category, or send photos directly)
```

#### Step 4: Change Category (Optional)
```
👤 User: /nav
🤖 Bot: 👇 Current category: Popular Cosplay
        [Inline keyboard with category buttons]

👤 User: [Clicks "Video Cosplay"]
🤖 Bot: ✅ Category set to: Video Cosplay
```

#### Step 5: Upload Photos
```
👤 User: [Sends photo 1]
🤖 Bot: 📷 Photo added! Total photos: 1

👤 User: [Sends photo 2]
🤖 Bot: 📷 Photo added! Total photos: 2

👤 User: [Sends video]
🤖 Bot: ✈️ Forwarded to channel: video.mp4
        (or 📄 Added locally if channel not configured)
```

#### Step 6: Set Password (Optional)
```
👤 User: /set_pass MySecretPass123
🤖 Bot: 🔒 Password set to: MySecretPass123
```

#### Step 7: Publish Album
```
👤 User: /end_album
🤖 Bot: 🎉 Album published successfully!
        Code: a01
        Title: Summer Vacation 2024
        Category: Video Cosplay
        Photos: 2
        URL: https://your-worker.workers.dev/a01
```

#### Step 8: Access Album (Web)
Visit: `https://your-worker.workers.dev/a01`
- View all photos
- Download attachments
- Password prompt if protected
- Navigation to previous/next album

### Album Data Structure

Albums are stored in Cloudflare KV with the following JSON structure:

```json
{
  "title": "Summer Vacation 2024",
  "category": "Popular Cosplay",
  "files": [
    "AgACAgIAAxkBAAIC...",
    "AgACAgIAAxkBAAID..."
  ],
  "attachments": [
    {
      "file_name": "vacation_video.mp4",
      "tg_link": "https://t.me/c/1234567890/123",
      "type": "tg_link"
    }
  ],
  "zip": {
    "file_name": "photos.zip",
    "tg_link": "https://t.me/c/1234567890/124",
    "type": "tg_link"
  },
  "password": "MySecretPass123"
}
```

**Field Descriptions:**

- **title**: Album display name
- **category**: Album category for organization
- **files**: Array of Telegram photo file IDs (for image previews)
- **attachments**: Array of attached files (videos, documents, archives)
- **zip**: Reference to primary archive file (if present)
- **password**: Optional password for viewing (stored in plaintext)

---

## CI/CD Pipeline

### GitHub Actions Workflow

The repository includes an automated CI/CD pipeline in `.github/workflows/docker-build.yml` that:

1. **Triggers on:**
   - Every push to `main` branch
   - Manual trigger via GitHub Actions UI (workflow_dispatch)

2. **Builds:**
   - Docker image from Dockerfile
   - Uses Docker Buildx for multi-platform support

3. **Authenticates:**
   - Logs into GitHub Container Registry (GHCR)
   - Uses `GITHUB_TOKEN` (automatically provided)

4. **Publishes:**
   - Tags: `ghcr.io/tyr-eamon/bot-image:latest`
   - Tags: `ghcr.io/tyr-eamon/bot-image:<commit-sha>`

### Triggering Builds

#### Automatic Trigger
```bash
git add .
git commit -m "feat: update bot features"
git push origin main
```
→ Workflow automatically starts

#### Manual Trigger
1. Go to GitHub repository → **Actions** tab
2. Select **Docker Build and Push** workflow
3. Click **Run workflow**
4. Select branch and click **Run workflow**

### Verifying Build Status

```bash
# View in GitHub
- Navigate to repository → Actions tab
- Check latest "Docker Build and Push" run
- Click on job to view build logs

# Pull and verify image locally
docker pull ghcr.io/tyr-eamon/bot-image:latest
docker inspect ghcr.io/tyr-eamon/bot-image:latest
```

### Docker Image Management

```bash
# List available tags
docker search ghcr.io/tyr-eamon/bot-image --no-trunc

# Pull specific version
docker pull ghcr.io/tyr-eamon/bot-image:abc1234567890

# Use in production
docker run -d \
  --name bot \
  --env-file .env \
  ghcr.io/tyr-eamon/bot-image:latest
```

---

## Troubleshooting

### Bot Does Not Respond

**Symptoms:** Bot is running but doesn't respond to commands

**Solutions:**

1. **Verify bot token is correct**
   ```bash
   # Check if token is set
   echo $BOT_TOKEN
   
   # Test token validity
   curl https://api.telegram.org/bot$BOT_TOKEN/getMe
   ```

2. **Ensure bot is started in Telegram**
   - Send `/start` to your bot in Telegram
   - Wait for bot to respond

3. **Check if process is running**
   ```bash
   # Local: View output
   python bot.py
   
   # Docker: View logs
   docker logs -f bot-image
   
   # Docker Compose: View logs
   docker compose logs -f bot-image
   ```

4. **Verify network connectivity**
   - Container must have outbound HTTPS to `api.telegram.org`
   - Check firewall rules and docker networking

### Album Not Saving / Cloudflare Issues

**Symptoms:** `/end_album` fails or albums don't appear in KV

**Solutions:**

1. **Verify Cloudflare credentials**
   ```bash
   echo "Account ID: $CF_ACCOUNT_ID"
   echo "Namespace ID: $CF_NAMESPACE_ID"
   echo "API Token: ${CF_API_TOKEN:0:20}..."  # Show first 20 chars
   ```

2. **Test Cloudflare API access**
   ```bash
   curl -H "Authorization: Bearer $CF_API_TOKEN" \
     https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/storage/kv/namespaces
   ```

3. **Verify API token permissions**
   - Log into Cloudflare Dashboard
   - Go to My Profile → API Tokens → Token used
   - Ensure it has `Account.Workers KV Storage` permissions

4. **Check KV namespace exists**
   - Dashboard → Workers & Pages → KV
   - Verify namespace is listed and not in error state

5. **Check logs for errors**
   ```bash
   docker logs bot-image 2>&1 | grep -i "cloudflare\|error\|exception"
   ```

### Channel Forwarding Problems

**Symptoms:** Videos/files not forwarded to channel, or links broken

**Solutions:**

1. **Verify channel ID format**
   - Channel ID must start with `-100`
   - Example: `-1001234567890` (not `1001234567890`)

2. **Verify channel link prefix**
   - Format: `https://t.me/c/1234567890` (without `-100`)
   - Example: If channel ID is `-1001234567890`, prefix is `https://t.me/c/1234567890`

3. **Check bot permissions in channel**
   - Make bot an admin in the target channel
   - Ensure bot has "Post Messages" and "Edit Messages" permissions

4. **Test manual forward**
   ```bash
   # Send test message to channel
   # Check if bot can access it
   docker logs bot-image | grep -i "forward"
   ```

### Docker Container Exits Immediately

**Symptoms:** `docker ps` shows container is not running, `docker logs` shows traceback

**Solutions:**

1. **Verify all required variables are set**
   ```bash
   cat .env | grep -E "BOT_TOKEN|CF_ACCOUNT_ID|CF_NAMESPACE_ID|CF_API_TOKEN"
   ```

2. **Check environment variables are loaded**
   ```bash
   docker run -d \
     --name test-bot \
     --env BOT_TOKEN=test \
     --env CF_ACCOUNT_ID=test \
     --env CF_NAMESPACE_ID=test \
     --env CF_API_TOKEN=test \
     ghcr.io/tyr-eamon/bot-image:latest
   
   docker logs test-bot
   ```

3. **View full error message**
   ```bash
   docker logs container-id
   
   # Or increase log verbosity
   docker logs --tail 50 container-id
   ```

4. **Check image integrity**
   ```bash
   docker inspect ghcr.io/tyr-eamon/bot-image:latest
   
   # Try running interactively
   docker run -it --env-file .env ghcr.io/tyr-eamon/bot-image:latest
   ```

### GHCR Pull/Push Issues

**Symptoms:** Authentication errors, image not found

**Solutions:**

1. **Check GitHub authentication**
   ```bash
   # Log in to GHCR
   echo $GITHUB_TOKEN | docker login ghcr.io -u username --password-stdin
   
   # Or use PAT with read/write packages scope
   cat > ~/.docker/config.json << EOF
   {
     "auths": {
       "ghcr.io": {
         "auth": "$(echo -n username:token | base64)"
       }
     }
   }
   EOF
   ```

2. **Use specific commit tag if latest is cached**
   ```bash
   docker pull ghcr.io/tyr-eamon/bot-image:abc1234567890def
   ```

3. **Clear local image cache**
   ```bash
   docker rmi ghcr.io/tyr-eamon/bot-image:latest
   docker pull ghcr.io/tyr-eamon/bot-image:latest
   ```

### GitHub Actions Workflow Failures

**Symptoms:** Build fails in Actions tab, image not pushed to GHCR

**Solutions:**

1. **View workflow logs**
   - GitHub → Actions tab
   - Click failed job
   - Expand step logs to see errors

2. **Common issues:**
   - **Docker build fails**: Check Dockerfile syntax, missing files
   - **GHCR auth fails**: Verify `GITHUB_TOKEN` has package write permissions
   - **Dependencies missing**: Check `requirements.txt` is correct

3. **Re-run failed workflow**
   - Go to workflow run
   - Click "Re-run failed jobs"
   - Or manually trigger via "Run workflow"

### Cloudflare Worker Deployment Issues

**Symptoms:** Worker deployment fails, 404 errors, gallery not loading

**Solutions:**

1. **Verify Wrangler configuration**
   ```bash
   # Check wrangler.toml
   cat wrangler.toml
   
   # Validate configuration
   wrangler publish --dry-run
   ```

2. **Verify KV binding**
   ```bash
   # In wrangler.toml, ensure binding matches code:
   kv_namespaces = [
     { binding = "ALBUMS", id = "YOUR_KV_NAMESPACE_ID" }
   ]
   
   # In _worker.js:
   # env.ALBUMS.get(code)  // Must match binding name
   ```

3. **Check environment variables**
   - Dashboard → Workers → Your Worker → Settings → Variables
   - Ensure `CATEGORIES` and `BOT_TOKEN` are set
   - Verify `ALBUMS` KV binding is configured

4. **View Worker logs**
   ```bash
   wrangler tail --env production
   ```

5. **Debug locally**
   ```bash
   wrangler dev --env production
   # Access http://localhost:8787 for testing
   ```

### Common Environment Variable Mistakes

| Mistake | Impact | Fix |
|---------|--------|-----|
| Missing `-100` in channel ID | Channel forwarding fails | Set `CHANNEL_ID=-1001234567890` |
| Wrong API token permissions | KV operations fail | Regenerate with KV storage permissions |
| Incomplete worker base URL | Links to albums broken | Use `https://your-worker.workers.dev` format |
| Empty `CATEGORIES` | `/nav` shows no options | Set `CATEGORIES=Cat1,Cat2,Cat3` |

---

## License

This project is licensed under the **MIT License** - see the LICENSE file for details.

You are free to:
- ✅ Use this project for any purpose (commercial or personal)
- ✅ Modify and distribute the code
- ✅ Include this in your own projects

With the condition that you include the original license and copyright notice.

---

## Additional Resources

### Documentation & APIs
- [python-telegram-bot Documentation](https://docs.python-telegram-bot.org/)
- [Telegram Bot API Reference](https://core.telegram.org/bots/api)
- [Cloudflare KV Documentation](https://developers.cloudflare.com/kv/)
- [Cloudflare Workers Documentation](https://developers.cloudflare.com/workers/)
- [Discord Developer Portal](https://discord.com/developers/applications)

### Tools & Services
- [BotFather (Telegram Bot Creator)](https://t.me/botfather)
- [Cloudflare Dashboard](https://dash.cloudflare.com)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Container Registry Docs](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)

### Related Projects
- [python-telegram-bot GitHub](https://github.com/python-telegram-bot/python-telegram-bot)
- [Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/)

---

## Tips for Production Deployment

1. **Enable user authentication**
   - Use whitelist feature (`/allow <user_id>`) for trusted users only
   - Consider adding PIN or two-factor authentication

2. **Monitor resource usage**
   - Set `docker stats` monitoring alerts
   - Monitor Cloudflare KV storage limits (free tier: 1GB)
   - Check Telegram rate limiting (30 requests/second per account)

3. **Backup important data**
   - Regularly export albums from Cloudflare KV
   - Maintain database snapshots
   - Document important channel IDs and configuration

4. **Optimize file storage**
   - Regularly clean up old albums with `/delete`
   - Use `.zip` files instead of multiple individual files
   - Consider file size limits for channel forwarding

5. **Security best practices**
   - Rotate API tokens periodically
   - Use strong passwords for password-protected albums
   - Keep environment variables in `.env` and `.gitignore`
   - Don't commit credentials to version control

6. **Logging & monitoring**
   - Redirect logs to external service (CloudWatch, Datadog, etc.)
   - Set up alerts for bot crashes or API errors
   - Monitor Cloudflare Worker request logs

7. **Performance tuning**
   - Use Docker resource limits:
     ```bash
     docker run -m 512m -c 1024 ...
     ```
   - Enable Docker healthcheck:
     ```bash
     docker run --health-cmd="curl -f http://localhost" ...
     ```

---

**Built with ❤️ using Python, python-telegram-bot, Cloudflare Workers, and Docker**
