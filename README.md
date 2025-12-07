# BOT-IMAGE

A Telegram bot for collecting and organizing photos into albums backed by Cloudflare KV storage. The project ships with a production-ready Docker image and an automated GitHub Actions pipeline that publishes images to GHCR (`ghcr.io/tyr-eamon/bot-image`).

## 🌟 Features

- **Simple Album Creation**: Start an album session with a single command
- **Photo Collection**: Send multiple photos to build your album
- **Title Management**: Set album titles using messages starting with `#`
- **Cloudflare KV Storage**: Reliable cloud storage for album metadata and file IDs
- **Auto-incrementing Album Codes**: Albums are automatically assigned codes (a01, a02, a03...)
- **Long Polling**: Works reliably without webhooks
- **Docker Support**: Production-ready containerized deployment
- **Zeabur Ready**: Optimized for easy deployment on the Zeabur platform

## ✅ Prerequisites

| Requirement | Why it is needed |
|-------------|------------------|
| **Python 3.10+** | Required for local development and running the bot directly. |
| **pip** | Installs Python dependencies from `requirements.txt`. |
| **Git** | Clones this repository. |
| **Docker 24+ & Docker Compose v2** | Build, run, and orchestrate containers. |
| **Telegram Account & Bot Token** | Obtain via [@BotFather](https://t.me/botfather) to interact with the Telegram Bot API. |
| **Cloudflare Account with KV namespace** | Stores album metadata and file IDs. |
| **Access to GitHub Container Registry (GHCR)** | Pull the published image `ghcr.io/tyr-eamon/bot-image`. |
| **Optional – Discord Developer Portal access** | Only if you plan to adapt the bot for Discord in your fork. |

Environment preparation tips:
- Ensure outbound HTTPS access to `api.telegram.org` and Cloudflare API endpoints.
- When using Docker, allocate enough memory for Python (at least 512 MB).
- Install `direnv` or use a `.env` file loader if you prefer not to export variables manually.

## 🚀 Installation & Deployment Steps

### 1. Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/tyr-eamon/BOT-IMAGE.git
   cd BOT-IMAGE
   ```
2. **(Optional) Create and activate a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. **Install dependencies**
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
4. **Create a `.env` (or export variables manually)**
   ```bash
   cat <<'EOF' > .env
   BOT_TOKEN=123456:ABC
   CF_ACCOUNT_ID=your_cf_account_id
   CF_NAMESPACE_ID=your_kv_namespace_id
   CF_API_TOKEN=your_cf_api_token
   WORKER_BASE_URL=https://your-worker.workers.dev
   CHANNEL_ID=-1001234567890
   CHANNEL_LINK_PREFIX=https://t.me/c/1234567890
   CATEGORIES=Popular Cosplay,Video Cosplay,Explore Categories
   EOF
   ```
5. **Export the variables (if you are not using a loader)**
   ```bash
   export $(grep -v '^#' .env | xargs)
   ```
6. **Run the bot locally**
   ```bash
   python bot.py
   ```

### 2. Build a Docker image locally
```bash
docker build -t bot-image:local .
```

### 3. Run the container with environment variables
```bash
docker run -d \
  --name bot-image \
  --env-file .env \
  bot-image:local
```
Use `--restart unless-stopped` in production so the bot restarts automatically.

### 4. Deploy using the pre-built GHCR image
1. **Authenticate (if needed)**
   ```bash
   echo "$GHCR_TOKEN" | docker login ghcr.io -u <github-username> --password-stdin
   ```
2. **Pull the image**
   ```bash
   docker pull ghcr.io/tyr-eamon/bot-image:latest
   # or pin to commits:
   docker pull ghcr.io/tyr-eamon/bot-image:<commit-sha>
   ```
3. **Run the image**
   ```bash
   docker run -d \
     --name bot-image \
     --env-file .env \
     ghcr.io/tyr-eamon/bot-image:latest
   ```

### 5. Deploy to Zeabur
1. Push your repository to GitHub.
2. Create a Zeabur project and connect this repository.
3. Add the required environment variables in the Zeabur dashboard (`BOT_TOKEN`, `CF_ACCOUNT_ID`, `CF_NAMESPACE_ID`, `CF_API_TOKEN`, `WORKER_BASE_URL`, optional channel settings).
4. Zeabur will detect the Dockerfile, build, and deploy automatically.
5. Monitor logs directly from the Zeabur control panel.

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BOT_TOKEN` | ✅ | — | Telegram Bot API token from BotFather. |
| `CF_ACCOUNT_ID` | ✅ | — | Cloudflare account ID used for KV operations. |
| `CF_NAMESPACE_ID` | ✅ | — | Cloudflare KV namespace ID where albums are stored. |
| `CF_API_TOKEN` | ✅ | — | Cloudflare API token with `Account.Workers KV Storage` permissions. |
| `WORKER_BASE_URL` | Optional | `https://example.workers.dev` | URL prefix used when sharing album links. |
| `CHANNEL_ID` | Optional | `0` | Telegram channel ID (include `-100`). Enables forwarding large files to a private channel. |
| `CHANNEL_LINK_PREFIX` | Optional | `""` | Prefix used to create shareable channel links (e.g., `https://t.me/c/1234567890`). |
| `CATEGORIES` | Optional | `Popular Cosplay,…` | Comma-separated list of categories displayed by `/nav`. |

### Sample `.env`
```dotenv
BOT_TOKEN=123456:ABC
CF_ACCOUNT_ID=abcd1234
CF_NAMESPACE_ID=1234abcd5678efgh
CF_API_TOKEN=cf_api_token_with_kv_rights
WORKER_BASE_URL=https://your-worker.workers.dev
CHANNEL_ID=-1001234567890
CHANNEL_LINK_PREFIX=https://t.me/c/1234567890
CATEGORIES=Popular Cosplay,Video Cosplay,Explore Categories
```

### Bot Credentials

- **Telegram**: Use [@BotFather](https://t.me/botfather) → `/newbot`, follow the prompts, and copy the API token into `BOT_TOKEN`.
- **Discord (optional/future work)**: If you adapt this Docker image for Discord, create an application in the [Discord Developer Portal](https://discord.com/developers/applications), generate a bot token, and expose it via a new environment variable in your fork (e.g., `DISCORD_BOT_TOKEN`).

### Cloudflare Credentials
1. **Account ID**: Visible in the Cloudflare dashboard URL or the account overview.
2. **KV Namespace**: Navigate to *Workers & Pages → KV*, create a namespace, and copy its ID into `CF_NAMESPACE_ID`.
3. **API Token**: Go to *My Profile → API Tokens* and create a token using the "Edit Cloudflare Workers" template or add `Account.Workers KV Storage` permissions.

## ▶️ Running the Bot

### Local Python process
```bash
python bot.py
```
Logs are printed to stdout; keep the terminal open or use a process manager (e.g., `systemd`, `supervisord`).

### Docker
```bash
docker run -d \
  --name bot-image \
  --restart unless-stopped \
  --env-file .env \
  ghcr.io/tyr-eamon/bot-image:latest
```
Inspect logs with `docker logs -f bot-image`.

### Docker Compose (optional)
```yaml
services:
  bot-image:
    image: ghcr.io/tyr-eamon/bot-image:latest
    restart: unless-stopped
    env_file:
      - .env
    logging:
      driver: json-file
      options:
        max-size: "10m"
```
Run with:
```bash
docker compose up -d
```

## 🔄 GitHub Actions Workflow

The workflow defined in `.github/workflows/docker-build.yml`:
- Triggers on every push to `main` or via manual `workflow_dispatch`.
- Uses Docker Buildx to build the image from the repository root.
- Logs in to GHCR with the GitHub-provided `GITHUB_TOKEN`.
- Pushes two tags: `ghcr.io/tyr-eamon/bot-image:latest` and `ghcr.io/tyr-eamon/bot-image:<commit-sha>`.

This means every merge to `main` produces a fresh, versioned container image you can deploy immediately.

## 📱 Usage

### Commands

- `/start` - Display welcome message and instructions
- `/start_album` - Begin a new album collection session
- `/end_album` - Save the current album to Cloudflare KV
- `/nav` - Switch categories via inline keyboard
- `/set_pass <password>` - Store a password for the current album
- `/delete <code>` - Remove a published album (confirmation required)
- `/allow <user_id>` / `/list_users` - Manage allowed user IDs (owner only)

### Workflow Example

1. **Start the bot**
   ```
   User: /start
   Bot: 🤖 Welcome to the Photo Collection Bot!...
   ```
2. **Create a new album**
   ```
   User: /start_album
   Bot: 📸 Album session started!
   ```
3. **Set album title**
   ```
   User: #Summer Vacation 2024
   Bot: ✅ Title set to: Summer Vacation 2024. Now send photos...
   ```
4. **Upload photos**
   ```
   User: [sends photo]
   Bot: 📷 Photo added! Total photos in album: 1.

   User: [sends another photo]
   Bot: 📷 Photo added! Total photos in album: 2.
   ```
5. **Save the album**
   ```
   User: /end_album
   Bot: ✅ Album saved successfully!
        Code: a01
        Title: Summer Vacation 2024
        Photos stored: 2
   ```

## 🗂️ Album Storage Format

Albums are stored in Cloudflare KV with the following structure:
```json
{
  "title": "Summer Vacation 2024",
  "files": [
    "AgACAgIAAxkBAAIC...",
    "AgACAgIAAxkBAAID..."
  ],
  "attachments": [],
  "category": "Popular Cosplay",
  "zip": null,
  "password": null
}
```
- **Key**: Auto-incremented album code (a01, a02, a03...)
- **Value**: JSON object containing title, category, photos, attachments, and password metadata

## 🏗️ Architecture
```
┌─────────────────┐
│  Telegram User  │
└────────┬────────┘
         │ Commands & Photos
         ▼
┌─────────────────┐
│   Bot (Python)  │
│  Long Polling   │
└────────┬────────┘
         │ HTTP API
         ▼
┌─────────────────┐
│ Cloudflare KV   │
│    Storage      │
└─────────────────┘
```

## 🛠️ Development

### Project Structure
```
BOT-IMAGE/
├── bot.py              # Main bot implementation
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker configuration
└── README.md           # Documentation
```

### Key Components
- **CloudflareKVClient**: Handles all KV API interactions
- **Session Management**: Tracks user album states using `context.user_data`
- **Command Handlers**: Process `/start`, `/start_album`, `/end_album`, `/nav`, `/set_pass`, `/delete`
- **Message Handlers**: Process titles, photos, documents, and videos
- **Error Handler**: Logs exceptions and prevents crashes

## 🧪 Testing

1. Set environment variables (or `.env`).
2. Run `python bot.py`.
3. Send commands to your bot on Telegram.
4. Verify albums are saved to Cloudflare KV.
5. Inspect the KV namespace in Cloudflare for stored records.

## 🐛 Troubleshooting

### Bot does not respond
- Double-check that `BOT_TOKEN` is correct and the bot has been started via `/start` in Telegram.
- Ensure the process is running: `python bot.py` locally or `docker ps` for containers.
- Inspect logs:
  - Local: `python bot.py` output.
  - Docker: `docker logs -f bot-image`.
  - Docker Compose: `docker compose logs -f bot-image`.

### Album not saving / Cloudflare issues
- Verify `CF_ACCOUNT_ID`, `CF_NAMESPACE_ID`, and `CF_API_TOKEN`.
- Confirm the API token has `Account.Workers KV Storage` permissions.
- Ensure the Cloudflare account has an existing KV namespace and it is bound to the token.

### Channel forwarding problems
- Set `CHANNEL_ID` with the `-100` prefix and grant the bot admin rights in the target channel.
- Provide a valid `CHANNEL_LINK_PREFIX` (e.g., `https://t.me/c/<channel_id_without_-100>`).

### Docker container exits immediately
- Confirm all required environment variables are provided via `--env` or `--env-file`.
- Run `docker logs <container-id>` to view the Python traceback.
- Ensure outbound internet access is allowed for the container.

### GHCR pull/push issues
- Run `docker login ghcr.io` using a Personal Access Token with `read:packages` / `write:packages` scopes.
- Pull a pinned commit tag if you suspect `latest` is cached: `docker pull ghcr.io/tyr-eamon/bot-image:<commit-sha>`.

### GitHub Actions workflow failures
- Open the **Actions** tab in GitHub, inspect the latest "Docker Build and Push" run, and read the logs for build errors.
- Fix linting or dependency issues locally, push, and the workflow will rebuild/publish automatically.

### Zeabur deployment issues
- Confirm the Dockerfile is in the repository root.
- Ensure every environment variable is set in the Zeabur dashboard.
- Review build and runtime logs from Zeabur to diagnose environment problems.

## 📄 License

MIT License - feel free to use this project for any purpose.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🔗 Helpful Links

- [python-telegram-bot Documentation](https://docs.python-telegram-bot.org/)
- [Cloudflare KV Documentation](https://developers.cloudflare.com/kv/)
- [Zeabur Documentation](https://zeabur.com/docs)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [GitHub Container Registry Docs](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)

## 💡 Tips

- Use descriptive titles starting with `#` for better organization.
- The bot stores only Telegram file IDs, not the actual photos; media stays on Telegram servers.
- Configure `WORKER_BASE_URL` to point to a Cloudflare Worker that renders albums.
- Add rate limiting and user authentication if you expose the bot publicly.
- Monitor Cloudflare KV usage to stay within the free tier limits.

---

Built with ❤️ using Python, python-telegram-bot, and Cloudflare KV.
