# BOT-IMAGE

A Telegram bot for collecting and organizing photos into albums backed by Cloudflare KV storage.

## 🌟 Features

- **Simple Album Creation**: Start an album session with a single command
- **Photo Collection**: Send multiple photos to build your album
- **Title Management**: Set album titles using messages starting with `#`
- **Cloudflare KV Storage**: Reliable cloud storage for album metadata and file IDs
- **Auto-incrementing Album Codes**: Albums are automatically assigned codes (a01, a02, a03...)
- **Long Polling**: Works reliably without webhooks
- **Docker Support**: Production-ready containerized deployment
- **Zeabur Ready**: Optimized for easy deployment on Zeabur platform

## 📋 Requirements

- Python 3.10+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Cloudflare account with KV namespace configured
- Docker (for containerized deployment)

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd BOT-IMAGE
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables**
   ```bash
   export BOT_TOKEN="your_telegram_bot_token"
   export CF_ACCOUNT_ID="your_cloudflare_account_id"
   export CF_NAMESPACE_ID="your_kv_namespace_id"
   export CF_API_TOKEN="your_cloudflare_api_token"
   export WORKER_BASE_URL="https://your-worker.workers.dev"  # Optional
   ```

4. **Run the bot**
   ```bash
   python bot.py
   ```

### Docker Deployment

1. **Build the Docker image**
   ```bash
   docker build -t telegram-photo-bot .
   ```

2. **Run the container**
   ```bash
   docker run -d \
     -e BOT_TOKEN="your_telegram_bot_token" \
     -e CF_ACCOUNT_ID="your_cloudflare_account_id" \
     -e CF_NAMESPACE_ID="your_kv_namespace_id" \
     -e CF_API_TOKEN="your_cloudflare_api_token" \
     -e WORKER_BASE_URL="https://your-worker.workers.dev" \
     telegram-photo-bot
   ```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | Yes | Telegram Bot API token from BotFather |
| `CF_ACCOUNT_ID` | Yes | Your Cloudflare account ID |
| `CF_NAMESPACE_ID` | Yes | Cloudflare KV namespace ID for storage |
| `CF_API_TOKEN` | Yes | Cloudflare API token with KV write permissions |
| `WORKER_BASE_URL` | No | Base URL for album sharing (e.g., Cloudflare Worker endpoint) |

### Getting Cloudflare Credentials

1. **Account ID**: Found in the Cloudflare dashboard URL or Account overview
2. **KV Namespace**:
   - Go to Workers & Pages → KV
   - Create a new namespace
   - Copy the namespace ID
3. **API Token**:
   - Go to My Profile → API Tokens
   - Create token with "Edit Cloudflare Workers" template
   - Or create a custom token with `Account.Workers KV Storage` permissions

## 📦 Deployment to Zeabur

[Zeabur](https://zeabur.com) provides seamless deployment with automatic Docker builds.

### Step-by-step Guide

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Create a new project on Zeabur**
   - Go to [Zeabur Dashboard](https://dash.zeabur.com)
   - Click "Create New Project"
   - Connect your GitHub repository

3. **Configure environment variables**
   
   In the Zeabur dashboard, add the following environment variables:
   - `BOT_TOKEN`
   - `CF_ACCOUNT_ID`
   - `CF_NAMESPACE_ID`
   - `CF_API_TOKEN`
   - `WORKER_BASE_URL` (optional)

4. **Deploy**
   - Zeabur will automatically detect the Dockerfile
   - The service will build and deploy automatically
   - Monitor logs in the Zeabur dashboard

5. **Verify deployment**
   - Check the logs to ensure the bot started successfully
   - Send `/start` to your bot on Telegram to test

### Zeabur Configuration Tips

- **Auto-restart**: Zeabur automatically restarts your service if it crashes
- **Logs**: Access real-time logs from the service dashboard
- **Scaling**: Adjust resources in the service settings if needed
- **Updates**: Push to your repository to trigger automatic redeployment

## 📱 Usage

### Commands

- `/start` - Display welcome message and instructions
- `/start_album` - Begin a new album collection session
- `/end_album` - Save the current album to Cloudflare KV

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
  ]
}
```

- **Key**: Auto-incremented album code (a01, a02, a03...)
- **Value**: JSON object containing title and array of Telegram file IDs

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
├── Dockerfile         # Docker configuration
└── README.md          # This file
```

### Key Components

- **CloudflareKVClient**: Handles all KV API interactions
- **Session Management**: Tracks user album states using `context.user_data`
- **Command Handlers**: Process /start, /start_album, /end_album
- **Message Handlers**: Process title messages and photos
- **Error Handler**: Logs exceptions and prevents crashes

## 🧪 Testing

Test the bot locally before deployment:

1. Set environment variables
2. Run `python bot.py`
3. Send commands to your bot on Telegram
4. Verify albums are saved to Cloudflare KV

Check the KV namespace in your Cloudflare dashboard to see stored albums.

## 🐛 Troubleshooting

### Bot doesn't respond
- Verify `BOT_TOKEN` is correct
- Check if the bot is running (check logs)
- Ensure you've sent `/start` to the bot at least once

### Album not saving
- Verify Cloudflare credentials are correct
- Check API token has proper KV permissions
- Review bot logs for error messages

### Docker container exits
- Check environment variables are set
- Review container logs: `docker logs <container-id>`
- Ensure Cloudflare KV namespace exists

### Zeabur deployment issues
- Verify all environment variables are set in Zeabur dashboard
- Check build logs for errors
- Ensure Dockerfile is in repository root

## 📄 License

MIT License - feel free to use this project for any purpose.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🔗 Links

- [python-telegram-bot Documentation](https://docs.python-telegram-bot.org/)
- [Cloudflare KV Documentation](https://developers.cloudflare.com/kv/)
- [Zeabur Documentation](https://zeabur.com/docs)
- [Telegram Bot API](https://core.telegram.org/bots/api)

## 💡 Tips

- Use descriptive titles starting with # for better organization
- The bot stores only file IDs, not the actual photos (they remain on Telegram servers)
- You can use the `WORKER_BASE_URL` environment variable to point to a Cloudflare Worker that renders albums
- For production use, consider implementing rate limiting and user authentication
- Monitor your Cloudflare KV usage to stay within free tier limits

---

Built with ❤️ using Python, python-telegram-bot, and Cloudflare KV
