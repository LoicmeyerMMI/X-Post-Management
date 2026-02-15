# X Post Management

Desktop application to manage and schedule your X (Twitter) posts locally and securely.

## Features

- Create and publish posts with text and/or images
- Schedule posts in advance (uses X native scheduling)
- Manage your drafts
- View publication history
- Delete tweets directly from the app
- Calendar view of your posts
- **My Profile** page: followers/following stats, bio, growth chart, follower variations
- Google account connection for login
- Auto-detect Chrome installation
- Persistent preferences (language, theme) across sessions
- Bilingual interface (English / French)
- Light and dark theme

## Download

Download the latest `X Post Management.exe` from the releases.

## First Use

On first launch, a **Setup Wizard** guides you through 4 steps:

1. **Welcome** — Choose your language (EN/FR) and click **Get started**
2. **Credentials** — Enter your X username (without @) and password. These are saved locally in a `.env` file — nothing is sent to any server besides X itself.
3. **Google Connection** — Connect with Google (same email as your X account). A browser window opens for authentication. The wizard waits until the connection is confirmed.
4. **Import Profile** — Click **Import Profile** to fetch your profile picture, display name, bio and follower counts from X.

Once complete, you're ready to compose, schedule and manage your posts.

> **Tip:** Leave Chrome profile and Chrome path empty (default) to use the built-in Chromium browser.

## Configuration Options

Configuration is stored in a `.env` file (created automatically by the Setup Wizard). You can also edit it manually or via **Settings > Configuration** in the app.

| Key | Description | Default |
|-----|-------------|---------|
| `X_USERNAME` | Your X username (without @) | |
| `X_PASSWORD` | Your X password | |
| `CHROME_PROFILE_DIR` | Path to Chrome profile directory | empty (uses temp) |
| `CHROME_PATH` | Path to Chrome executable | empty (uses Playwright Chromium) |
| `HEADLESS` | `true` for invisible browser, `false` to see it | `true` |
| `CHECK_INTERVAL_SECONDS` | Check frequency for scheduled posts (seconds) | `15` |
| `MAX_RETRIES` | Number of retries on failure | `1` |

## Troubleshooting

- **Connection failed**: Test connection in Settings. If X requires verification, set `HEADLESS=false` and log in manually.
- **Post failed**: Make sure the image is under 5 MB.
- **Videos not supported**: X blocks automated video uploads. Only images are accepted.
- **Google login**: Use the "Connect to Google" button in Settings to authenticate with your Google account (same email as your X account).

## Security

All your data (credentials, posts, images) is stored locally on your computer. Nothing is sent to external servers - only X receives your posts.

## Files Created

The app creates these files next to the executable:

```
data/
  posts.db            - SQLite database (posts + followers history)
  profile_info.json   - Cached profile information
  profile_picture.jpg - Profile picture
  preferences.json    - UI preferences (language, theme)
  uploads/            - Uploaded images
logs/
  app.log             - Activity logs
.env                  - Configuration file
```

## Development

**Requirements:**
- Python 3.10+
- Node.js 18+

**Setup:**
```bash
pip install -r requirements.txt
playwright install chromium
cd ui && npm install && npm run build && cd ..
python server/app.py
```

**Build executable:**
```bash
cd ui && npm run build && cd ..
pyinstaller "X Post Manager.spec" --distpath dist --clean
```

## Tech Stack

- **Backend**: Flask, SQLite, Playwright (browser automation)
- **Frontend**: React, TypeScript, Vite, TailwindCSS, Recharts
- **Desktop**: pywebview (EdgeChromium) / PyInstaller
- **Scheduling**: APScheduler

## License

MIT

## Author

Developed by **Loic Meyer**

https://buymeacoffee.com/loicmeyer
