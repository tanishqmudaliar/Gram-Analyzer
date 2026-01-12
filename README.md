# GramAnalyzer 📊

> A powerful Instagram analytics application that helps you track followers, unfollowers, engagement, and much more.

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue)](https://www.typescriptlang.org/)

## ✨ Features

### 📈 Comprehensive Analytics

- **Who Doesn't Follow Back** - Identify users you follow who don't follow you back
- **Who You Don't Follow Back** - See followers you haven't reciprocated
- **Mutual Friends** - View accounts where both parties follow each other
- **New Followers** - Track recent followers since your last sync
- **Lost Followers (Unfollowers)** - Discover who unfollowed you
- **Story Viewers** - Identify consistent story viewers and engagement patterns
- **Ghost Followers** - Find inactive followers who never engage with your content

### 🎯 Key Highlights

- Real-time sync with Instagram data
- Detailed user profiles with engagement metrics
- Historical tracking of follower changes
- Clean, intuitive UI with dark mode support
- Mobile-first design with native Android/iOS apps
- Privacy-focused with local data storage

## 🛠️ Tech Stack

### Frontend

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **State Management**: Zustand
- **Mobile**: Capacitor.js (Android & iOS support)

### Backend

- **Framework**: FastAPI (Python)
- **Instagram API**: Instagrapi (Private API)
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **Authentication**: Session-based with secure token management

## 📁 Project Structure

```
gramAnalyzer/
├── web/                       # Next.js frontend application
│   ├── src/
│   │   ├── app/              # Next.js 14 app router pages
│   │   │   ├── page.tsx      # Landing page
│   │   │   ├── login/        # Authentication flow
│   │   │   └── dashboard/    # Main analytics dashboard
│   │   ├── components/        # React components
│   │   │   ├── ui/           # shadcn/ui components
│   │   │   └── dashboard/    # Dashboard-specific components
│   │   ├── lib/              # Utilities & API client
│   │   │   ├── api.ts        # API client wrapper
│   │   │   └── utils.ts      # Helper functions
│   │   └── store/            # Zustand state management
│   │       └── authStore.ts  # Authentication state
│   ├── android/              # Capacitor Android project
│   ├── ios/                  # Capacitor iOS project
│   ├── public/               # Static assets
│   └── capacitor.config.ts   # Capacitor configuration
├── api/                       # Python FastAPI backend
│   ├── app/
│   │   ├── routes/           # API endpoint routes
│   │   │   ├── auth.py       # Authentication endpoints
│   │   │   └── analytics.py  # Analytics endpoints
│   │   ├── services/
│   │   │   ├── instagram_service.py    # Instagram API wrapper
│   │   │   └── analytics_service.py    # Analytics logic
│   │   ├── models/           # Database models
│   │   ├── database.py       # Database configuration
│   │   └── main.py           # FastAPI application entry
│   ├── requirements.txt      # Python dependencies
│   └── .env.example          # Environment variables template
├── package.json              # Root workspace scripts
└── README.md                 # This file
```

## 🚀 Getting Started

### Prerequisites

Ensure you have the following installed:

- **Node.js** 18.0 or higher ([Download](https://nodejs.org/))
- **Python** 3.10 or higher ([Download](https://www.python.org/))
- **npm** or **yarn** package manager
- **Android Studio** (for building Android APK)
- **Xcode** (for building iOS app - macOS only)

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/tanishqmudaliar/gramanalyzer.git
cd gramanalyzer
```

#### 2. Install All Dependencies

```bash
# Install all project dependencies (recommended)
npm run install:all
```

Or install manually:

```bash
# Install root dependencies
npm install

# Install frontend dependencies
cd web && npm install

# Install backend dependencies
cd ../api && pip install -r requirements.txt
```

#### 3. Configure Environment Variables

**Backend Configuration:**

```bash
cd api
cp .env.example .env
```

Edit `api/.env` with your settings:

```env
# Database
DATABASE_URL=sqlite:///./gramanalyzer.db

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
```

**Frontend Configuration (Optional):**

The frontend is pre-configured to use `http://localhost:8000` for development. To change this:

```bash
cd web
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

### 🎬 Running the Application

#### Development Mode

**Start Both Frontend and Backend:**

```bash
npm run dev
```

This will start:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

**Or run separately:**

```bash
# Terminal 1 - Frontend
npm run dev:web

# Terminal 2 - Backend
npm run dev:api
```

#### Production Mode

**Backend:**

```bash
npm run start:api
```

**Frontend:**

```bash
cd web
npm run build
npm start
```

## 📱 Building Mobile Apps

### Android

1. **Build and sync:**

   ```bash
   npm run build:android
   ```

2. **Open in Android Studio:**

   ```bash
   npm run android:open
   ```

3. **Build APK:**
   - In Android Studio: `Build → Build Bundle(s) / APK(s) → Build APK(s)`
   - Or use command line: `cd web/android && ./gradlew assembleDebug`

### iOS (macOS only)

1. **Build and sync:**

   ```bash
   cd web
   npm run build
   npx cap sync ios
   ```

2. **Open in Xcode:**

   ```bash
   npx cap open ios
   ```

3. **Build in Xcode:**
   - Select your device/simulator
   - Click the Play button or `Product → Run`

## 🔌 API Documentation

### Authentication Endpoints

| Method | Endpoint                     | Description                        |
| ------ | ---------------------------- | ---------------------------------- |
| POST   | `/api/auth/login`            | Login with Instagram credentials   |
| POST   | `/api/auth/verify-2fa`       | Complete two-factor authentication |
| POST   | `/api/auth/verify-challenge` | Complete security challenge        |
| POST   | `/api/auth/logout`           | Logout and clear session           |
| GET    | `/api/auth/status`           | Check authentication status        |

### Analytics Endpoints

| Method | Endpoint                            | Description                            |
| ------ | ----------------------------------- | -------------------------------------- |
| GET    | `/api/analytics/overview`           | Get analytics summary                  |
| GET    | `/api/analytics/detailed`           | Get detailed analytics with user lists |
| GET    | `/api/analytics/not-following-back` | Users who don't follow back            |
| GET    | `/api/analytics/not-followed-back`  | Followers you don't follow back        |
| GET    | `/api/analytics/mutual`             | Mutual followers                       |
| GET    | `/api/analytics/new-followers`      | New followers since last sync          |
| GET    | `/api/analytics/lost-followers`     | Recent unfollowers                     |
| GET    | `/api/analytics/story-viewers`      | Consistent story viewers               |
| GET    | `/api/analytics/ghost-followers`    | Inactive followers                     |
| POST   | `/api/analytics/sync`               | Start data synchronization             |
| GET    | `/api/analytics/sync/status`        | Get sync progress                      |

### Interactive API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation.

## 🎯 Usage Guide

### First Time Setup

1. **Launch the application** and navigate to the login page
2. **Enter your Instagram credentials** (username and password)
3. **Complete 2FA** if enabled on your account
4. **Wait for initial sync** - this may take a few minutes for large accounts
5. **Explore your analytics** on the dashboard

### Understanding the Metrics

- **Not Following Back**: Accounts you follow that don't follow you
- **Not Followed Back**: Your followers that you don't follow
- **Mutual Friends**: Accounts with reciprocal follows
- **New Followers**: Accounts that followed you since last sync
- **Lost Followers**: Accounts that unfollowed you since last sync
- **Story Viewers**: Accounts that consistently view your stories
- **Ghost Followers**: Followers with zero engagement on your content

### Best Practices

- **Sync once per day** to avoid rate limiting
- **Large accounts** (10k+ followers) may take 5-10 minutes to sync
- **Don't spam actions** (mass unfollows/follows)
- Use during **off-peak hours** for faster syncing

## ⚠️ Important Considerations

### Rate Limiting

Instagram implements strict rate limits to prevent automated activity:

- **Sync frequency**: Once per day recommended
- **Large accounts**: 10k+ followers may take several minutes
- **Delay between requests**: Automatic delays are built-in
- **API limits**: Respect Instagram's usage policies

### Account Safety

- **Use at your own risk** - This uses Instagram's private API
- **Secondary account recommended** for initial testing
- **No aggressive automation** - Don't use for mass actions
- **Session security** - Logout when done on shared devices

### Privacy & Security

- ✅ **Passwords never stored** - Only session tokens are kept
- ✅ **Local encryption** - Session tokens are encrypted
- ✅ **No third-party sharing** - All data stays on your device/server
- ✅ **Open source** - Review the code yourself

## 🚢 Deployment

### Backend Deployment

#### Railway / Render / Fly.io

1. Connect your Git repository
2. Set environment variables from `.env.example`
3. Set root directory to `api`
4. Deploy

#### Docker (Optional)

```dockerfile
# Create Dockerfile in api/
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Deployment

#### Vercel (Recommended)

1. Connect your repository
2. Set framework preset to "Next.js"
3. Set root directory to `web`
4. Add environment variable: `NEXT_PUBLIC_API_URL=https://your-api-url.com`
5. Deploy

#### Netlify / Cloudflare Pages

Similar process - point to `web` directory and set the API URL.

## 🐛 Troubleshooting

### "Challenge Required" Error

**Cause**: Instagram detected unusual activity.

**Solutions**:

- Wait 2-4 hours before retrying
- Complete the challenge in the official Instagram app
- Try logging in from the Instagram website first

### "Rate Limited" Error

**Cause**: Too many requests in a short time.

**Solutions**:

- Wait 10-15 minutes
- Reduce sync frequency
- Try again during off-peak hours

### Session Expired

**Cause**: Instagram session token expired.

**Solution**: Simply login again to refresh your session.

### Sync Taking Too Long

**Cause**: Large account with many followers.

**Expected behavior**:

- 1k-5k followers: ~1-2 minutes
- 5k-10k followers: ~2-5 minutes
- 10k+ followers: ~5-15 minutes

**Tips**: The progress indicator shows current status - be patient!

### Build Errors

**Frontend**:

```bash
cd web
rm -rf node_modules .next
npm install
npm run build
```

**Backend**:

```bash
cd api
pip install --upgrade -r requirements.txt
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines

- Follow existing code style
- Write meaningful commit messages
- Test your changes thoroughly
- Update documentation as needed

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚖️ Disclaimer

**Important**: This project is for educational purposes only.

- Using automation tools with Instagram may violate their [Terms of Service](https://help.instagram.com/581066165581870)
- The developers are **not responsible** for any account restrictions, bans, or other consequences
- Use this application **at your own risk**
- We recommend using a secondary/test account initially
- This project is not affiliated with, endorsed by, or connected to Instagram or Meta

## 🙏 Acknowledgments

- [Instagrapi](https://github.com/adw0rd/instagrapi) - Instagram Private API wrapper
- [Next.js](https://nextjs.org/) - React framework
- [FastAPI](https://fastapi.tiangolo.com/) - Python web framework
- [shadcn/ui](https://ui.shadcn.com/) - UI component library
- [Capacitor](https://capacitorjs.com/) - Cross-platform native runtime

## 📧 Support

If you encounter issues or have questions:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Search [existing issues](https://github.com/tanishqmudaliar/gramanalyzer/issues)
3. Create a [new issue](https://github.com/tanishqmudaliar/gramanalyzer/issues/new) with:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots if applicable

## 🗺️ Roadmap

- [ ] Export analytics data (CSV/JSON)
- [ ] Historical follower tracking charts
- [ ] Engagement rate calculations
- [ ] Browser extension support
- [ ] Multiple account management
- [ ] Custom notification settings
- [ ] Advanced filtering and search
- [ ] Competitor analysis features

---

**Made with ❤️ by [Tanishq Mudaliar](https://github.com/tanishqmudaliar)**

If you find this project helpful, please consider giving it a ⭐️ on GitHub!
