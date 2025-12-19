# GramAnalyzer

Instagram Analytics App - See who doesn't follow you back, track unfollowers, story viewers, and more.

## Features

- **Who Doesn't Follow Back** - See people you follow who don't follow you
- **Who You Don't Follow Back** - See followers you haven't followed back
- **Mutual Friends** - People who follow each other
- **New Followers** - Track who started following you
- **Lost Followers** - Track who unfollowed you (unfollowers)
- **Story Viewers** - See who consistently views your stories
- **Ghost Followers** - Identify followers who never engage

## Tech Stack

- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, shadcn/ui
- **Mobile**: Capacitor.js (Android/iOS)
- **Backend**: Python FastAPI
- **Instagram API**: Instagrapi (Instagram Private API)
- **Database**: SQLite (development) / PostgreSQL (production)

## Project Structure

```
gramAnalyzer/
├── web/                    # Next.js frontend + Capacitor
│   ├── src/
│   │   ├── app/           # Next.js app router pages
│   │   ├── components/    # React components
│   │   ├── lib/           # Utilities and API client
│   │   └── store/         # Zustand state management
│   ├── android/           # Capacitor Android project
│   └── capacitor.config.ts
├── api/                    # Python FastAPI backend
│   ├── app/
│   │   ├── routes/        # API endpoints
│   │   ├── instagram_service.py
│   │   ├── analytics_service.py
│   │   └── main.py
│   └── requirements.txt
└── package.json            # Root package scripts
```

## Prerequisites

- Node.js 18+
- Python 3.10+
- Android Studio (for building APK)

## Quick Start

### 1. Install Dependencies

```bash
# Install all dependencies
npm run install:all

# Or manually:
cd web && npm install
cd ../api && pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# API configuration
cp api/.env.example api/.env
# Edit api/.env with your settings

# Frontend configuration (optional)
# web/.env.local already configured for localhost
```

### 3. Start Development Servers

```bash
# Start both frontend and backend
npm run dev

# Or separately:
npm run dev:web    # Frontend on http://localhost:3000
npm run dev:api    # Backend on http://localhost:8000
```

### 4. Build for Android

```bash
# Build and sync with Android
npm run build:android

# Open in Android Studio
npm run android:open
```

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login with Instagram credentials
- `POST /api/auth/verify-2fa` - Complete 2FA verification
- `POST /api/auth/verify-challenge` - Complete security challenge

### Analytics
- `GET /api/analytics/overview` - Get analytics summary
- `GET /api/analytics/detailed` - Get detailed analytics with user lists
- `GET /api/analytics/not-following-back` - List of non-followers
- `GET /api/analytics/not-followed-back` - List you don't follow back
- `GET /api/analytics/mutual` - List of mutual friends
- `GET /api/analytics/new-followers` - New followers since last sync
- `GET /api/analytics/lost-followers` - Unfollowers since last sync
- `GET /api/analytics/story-viewers` - Consistent story viewers
- `GET /api/analytics/ghost-followers` - Ghost followers
- `POST /api/analytics/sync` - Start data sync
- `GET /api/analytics/sync/status` - Get sync progress

## Important Notes

### Rate Limiting
- Instagram has rate limits. The app includes delays between requests.
- Don't sync too frequently (once per day is recommended)
- Large accounts (10k+ followers) may take several minutes to sync

### Account Safety
- Use at your own risk - this uses Instagram's private API
- Consider using a secondary account for testing
- Don't use aggressive settings or frequent syncing

### Privacy
- Your Instagram password is never stored
- Session tokens are stored locally and encrypted
- All data processing happens on your device/server

## Development

### Frontend Development
```bash
cd web
npm run dev
```

### Backend Development
```bash
cd api
py -m uvicorn app.main:app --reload
```

### Building for Production

**Web (Vercel/Static)**:
```bash
cd web
npm run build
```

**Android APK**:
1. Build the web app: `npm run build:android`
2. Open Android Studio: `npm run android:open`
3. Build > Build Bundle(s) / APK(s) > Build APK(s)

## Deployment

### Backend (Railway/Render)
1. Connect your repository
2. Set environment variables from `.env`
3. Deploy the `api` directory
4. Install headless browser dependencies if needed

### Frontend (Vercel)
1. Connect your repository
2. Set `NEXT_PUBLIC_API_URL` to your backend URL
3. Deploy the `web` directory

## Troubleshooting

### "Challenge Required" Error
Instagram detected unusual activity. Wait a few hours and try again, or complete the challenge manually in the Instagram app.

### "Rate Limited" Error
Too many requests. Wait 5-10 minutes before trying again.

### Session Expired
Login again to refresh your session.

### Sync Taking Too Long
Large accounts take longer. The progress indicator shows current status.

## License

MIT License - Use responsibly and at your own risk.

## Disclaimer

This project is for educational purposes. Using automation tools with Instagram may violate their Terms of Service. The developers are not responsible for any account restrictions or bans that may occur from using this application.
