# Chitti Game Bot

A Telegram bot that brings the exciting **Chitti Game** to your group chats! This is a strategic multiplayer card game where players compete to collect matching emoji cards.

## 🎮 Game Overview

**Chitti Game** is a fast-paced card matching game where the objective is simple: **collect all cards of the same emoji type before your opponents do!**

### How It Works
- 4-8 players participate in each game
- Each player receives N cards (where N = number of players)
- Cards feature 8 different emoji types: 🍎 🍉 🍒 🍓 🍊 🍋 🍍 🥝
- Players take turns passing cards to each other
- First player to collect all matching cards wins the round!

## ✨ Features

- **Multi-group Support**: Play in multiple Telegram groups simultaneously
- **Private Game Sessions**: All gameplay happens via private messages for strategy
- **Smart Turn Management**: Randomized turn orders and intelligent player management
- **Admin Controls**: Game hosts and group admins have special privileges
- **Voting System**: Democratic game ending with voting mechanism
- **Real-time Updates**: Live game status and player mentions
- **Comprehensive Help**: Built-in tutorials and rule explanations

## 🚀 Quick Start

### For Players

1. **Start the bot**: Send `/start` to the bot in private chat
2. **Join a group**: Add the bot to your Telegram group
3. **Create a game**: Use `/game` in the group
4. **Players join**: Others use `/join` to participate
5. **Start playing**: Host uses `/begin` to start the match

### Game Commands

| Command | Description | Where to Use |
|---------|-------------|--------------|
| `/game` | Create a new game session | Group chat |
| `/join` | Join the active game | Group chat |
| `/begin` | Start the game (host only) | Group chat |
| `/lock` | Declare win when you have matching cards | Private chat |
| `/stop` | End the current game | Group chat |
| `/help` | Show help and commands | Any chat |

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.8 or higher
- MongoDB database
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Telegram API credentials

### Environment Variables

Create a `.env` file based on `sample.env`:

```env
API_ID=your_telegram_api_id
API_HASH=your_telegram_api_hash
BOT_TOKEN=your_bot_token
MONGO_URL=your_mongodb_connection_string
OWNER_ID=your_telegram_user_id
LOGGER_ID=your_log_group_id
```

### Local Installation

1. **Clone the repository**:
   ```bash
   git clonehttps://github.com/MaybeChiku/chitti-game-bot
   cd chitti-game-bot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp sample.env .env
   # Edit .env with your credentials
   ```

4. **Run the bot**:
   ```bash
   python -m src
   ```

### Docker Deployment

1. **Build the image**:
   ```bash
   docker build -t chitti-bot .
   ```

2. **Run the container**:
   ```bash
   docker run -d --env-file .env chitti-bot
   ```

### Heroku Deployment

1. **Prepare for Heroku**:
   ```bash
   heroku create your-app-name
   heroku config:set API_ID=your_api_id
   heroku config:set API_HASH=your_api_hash
   # Set other environment variables...
   ```

2. **Deploy**:
   ```bash
   git push heroku main
   ```

## 📋 Game Rules

### Setup
- **Players**: 4-8 players required
- **Cards**: Each player gets N cards (N = number of players)
- **Types**: Cards from 8 emoji types are distributed randomly

### Gameplay
1. **Turn Order**: Players take turns in random order
2. **Card Passing**: On your turn, select ONE card to pass to the next player
3. **Receiving Cards**: You'll receive cards from other players
4. **Winning Condition**: First to collect all cards of ONE emoji type wins



## 🔧 Key Components

### Game Management
- **ChittiGame Class**: Handles individual game sessions
- **GameManager**: Manages multiple concurrent games
- **Turn System**: Smart turn advancement and player management

### Database
- **MongoDB**: Stores user data, chat information, and game sessions
- **Collections**: Users, chats, and games are stored separately
- **Async Operations**: All database operations are asynchronous

### Security Features
- **Game Hashing**: Unique hash system prevents button reuse across games
- **Admin Validation**: Proper permission checking for admin commands
- **Rate Limiting**: Prevents command spamming
- **Input Validation**: Comprehensive input validation and error handling

## 🤝 Contributing

Contributions are welcome! Please fork the repository, create a feature branch for your changes, test thoroughly, and submit a pull request.

## 📝 License

This project is open source. Feel free to use, modify, and distribute according to your needs.

## 🐛 Bug Reports & Support

- **Issues**: Report bugs via GitHub Issues
- **Feature Requests**: Suggest new features in Issues
- **Support**: Join our [Support Group](https://t.me/DebugAngels)

## 🎉 Acknowledgments

- Built with [pyrofork](https://github.com/pyrofork/pyrofork) – A modern fork of the Pyrogram Telegram Bot API framework
- Database powered by [MongoDB](https://www.mongodb.com/)
- Deployed on [Heroku](https://www.heroku.com/) and [Docker](https://www.docker.com/)

---

**This project is open source and available for use and modification.**