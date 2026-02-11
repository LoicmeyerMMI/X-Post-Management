# X Post Management

Free desktop app to manage and schedule your X (Twitter) posts locally, without using the official API.

X Post Management lets you create, schedule, and manage posts directly from your computer.  
No API keys, no external servers, no subscriptions. Everything runs locally.

---

## Main features

- Create and publish posts with text and/or images
- Schedule posts in advance (works with X in English and French)
- Manage drafts
- View post history
- Delete tweets directly from the app
- Calendar view of your posts
- Profile page with follower growth tracking
- Guided setup on first launch
- Light and dark themes

---

## Why this project?

The official X API is expensive and restrictive for small creators and indie developers.  
X Post Management uses browser automation to interact with X like a real user, allowing you to post and schedule tweets without the official API.

- No API keys required
- No data sent to external servers
- Fully local and private

---

## Download

You can download the latest version from the **Releases** section of this repository.

---

## First-time setup

1. Launch `X Post Management.exe`
2. Follow the 4-step setup wizard:
   - **Welcome** – select your language (EN/FR)
   - **Credentials** – enter your X username (without @) and password
   - **Login** – connect to your X account via Google (opens a browser window)
   - **Profile** – import your profile picture and display name from X
3. Once finished, you can start composing and scheduling posts.

**Tip:**  
The app uses an integrated browser by default. You can change browser settings later in the Settings page if needed.

---

## Settings

The Settings page gives you access to:

- **Profile**  
  Import or refresh your profile picture and display name from X

- **Configuration**  
  Edit credentials, Chrome paths, and login settings  
  (click “Edit configuration”, use the (?) icon for help)

- **X connection**  
  Reconnect via Google if your session has expired

- **Browser mode**  
  - Invisible (default): runs in the background  
  - Visible: useful for solving captchas or logging in manually

- **Language**  
  Switch between French and English

- **Connection test**  
  Check if the app can log in to X

- **Check frequency**  
  How often scheduled posts are checked (default: 15s)

- **Retry attempts**  
  Number of retries if a post fails (default: 1)

- **Delete my data**  
  Remove stored credentials and reset the app

---

## Troubleshooting

**Login failed**
- Test the connection in Settings
- If X requests verification, switch to Visible browser mode and log in manually

**Post failed**
- The session may have expired (test the connection)
- A captcha may be required
- Temporary issue on X

**Scheduling fails**
- Make sure X is set to English or French
- Other languages are not supported yet

**Videos not supported**
- X blocks automated video uploads
- Only images are currently supported

---

## Security

All your data (credentials, posts, images) is stored locally on your computer.  
Nothing is sent to external servers. Only X receives your publications.

---

## Files created by the app

The application automatically creates these folders next to the executable:

- `data/` – database, profile picture, and uploaded images
- `logs/` – activity logs
- `.env` – configuration file (credentials and settings)

---

## Author

Developed by **Loïc Meyer**  
https://buymeacoffee.com/loicmeyer
