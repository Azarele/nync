# ⚡ Nync: The Pain-Aware Scheduler

Stop maximizing convenience. Start minimizing pain.

Nync is a **team scheduling platform** that treats meeting fairness as a first-class problem. Instead of just finding a free slot, Nync calculates the *pain* — the real human cost of inconvenient times — and optimizes meetings to distribute burden fairly across your team.

## Features

### 🛡️ **Teams & Roster Management**
- Create teams and invite colleagues via shareable invite codes
- Add "ghost members" (people not yet on Nync) to visualize their availability
- Custom working hours per person — the pain engine bends around your actual schedule
- Support for external guests who vote without needing an account

### 📊 **The Pain Board**
- Leaderboard of "martyrs" — who has suffered the most across all meetings
- Pain is calculated based on:
  - **Local time of day** (3am = 10 pain, 9am = 0 pain)
  - **Custom work hours** (flexibility for global teams)
  - **Weekends** (+8 penalty)
  - **Calendar conflicts** (+25 penalty)
- Vote on proposed meeting times and see results in real-time

### 🗺️ **The Scheduler & Heatmap**
- Visual UTC heatmap: every hour × every team member
- Colour-coded pain levels (green → red)
- Click to propose a meeting time
- Live calendar conflict detection (Google Calendar & Outlook)

### ⚖️ **Karma-Aware Scheduling (Paid Tiers)**
- Auto-find the top 3 best meeting times across 24–168 hours
- Considers *historical pain* — protects repeat martyrs
- Displays **fairness gap** (burden distribution) on each suggestion
- Integrates with Google Calendar & Outlook for real-time availability

### 🔌 **Integrations**
- **Google Calendar**: Sign in to read availability, book Google Meet
- **Outlook / Microsoft Teams**: Connect account, book Teams calls
- **Webhooks**: Post meeting notifications to Discord or Slack
- **Guest Voting Links**: Share meeting polls with external attendees

## Getting Started

### Prerequisites
- Python 3.9+
- Streamlit
- Supabase (PostgreSQL + auth)
- Google OAuth credentials (for Google Calendar)
- Microsoft Azure credentials (for Outlook/Teams)
- Stripe account (for payment processing)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Azarele/nync.git
   cd nync
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up secrets:**
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```
   Edit `.streamlit/secrets.toml` with your API keys and credentials (see below).

5. **Run the app:**
   ```bash
   streamlit run app.py
   ```
   The app will open at `http://localhost:8501`

## Configuration

### Secrets (.streamlit/secrets.toml)

All credentials are stored in `.streamlit/secrets.toml` (never commit this file). Use the provided `secrets.toml.example` as a template:

```toml
[supabase]
url = "your-supabase-url"
key = "your-supabase-anon-key"

[google]
client_id = "your-google-client-id"
client_secret = "your-google-client-secret"

[microsoft]
client_id = "your-microsoft-client-id"
client_secret = "your-microsoft-client-secret"
authority = "https://login.microsoftonline.com/common"
redirect_uri = "http://localhost:8501"

[stripe]
api_key = "your-stripe-secret-key"
publishable_key = "your-stripe-publishable-key"
price_squad = "price_1Smm9VIlTLkLyuizLNG57F1g"
price_guild = "price_1SmmATIlTLkLyuizW9PcnZrN"
price_empire = "price_1SmmB0IlTLkLyuiz6xySQvqd"
```

### Environment Setup

- **Supabase**: Create a project and enable Auth (Google + Email/Password providers)
- **Google OAuth**: Create a web application credential in Google Cloud Console
- **Microsoft Azure**: Register an app with Calendar.ReadWrite offline_access permissions
- **Stripe**: Set up products and price IDs for Squad, Guild, and Empire tiers

## Architecture

```
nync/
├── app.py                  # Main Streamlit app, navigation & auth
├── db.py                   # Supabase client
├── auth_utils.py           # Authentication & user management
├── calendar_utils.py       # Google Calendar & Outlook API integration
├── team_utils.py           # Team management & roster helpers
├── billing_utils.py        # Stripe & subscription logic
├── email_utils.py          # Email notifications
├── cron_worker.py          # Background token refresh
├── async_calendar_utils.py # Async calendar fetching
├── requirements.txt        # Python dependencies
├── .streamlit/
│   ├── config.toml        # Streamlit configuration
│   └── secrets.toml.example # Secrets template (NEVER commit secrets.toml)
└── modules/
    ├── app.py             # Dashboard layout
    ├── login.py           # Login & sign-up pages
    ├── team.py            # Team management UI
    ├── scheduler.py       # Heatmap & meeting proposal
    ├── martyr_board.py    # Pain leaderboard & voting
    ├── pricing.py         # Subscription tier page
    ├── settings.py        # User preferences
    ├── guide.py           # Help documentation
    ├── guest_vote.py      # Guest voting interface
    ├── onboarding.py      # First-run flow
    ├── legal.py           # Privacy & terms
    └── cookie_consent.py  # GDPR compliance
```

## Key Concepts

### Pain Score Algorithm

For each proposed meeting slot, pain is calculated per team member:

```
pain = base_pain + conflict_penalty + weekend_bonus

base_pain:
  - 0 if during work hours
  - +1 if 1 hour before/after
  - +3 if 2 hours before/after
  - +5 if 3+ hours before/after
  - +10 if deep night

conflict_penalty = +25 if calendar conflict exists
weekend_bonus = +8 if Saturday/Sunday
```

### Fairness Gap

The **fairness gap** is the spread between the most and least burdened team members for a given slot. Lower gap = better distribution of pain.

Slots are ranked: **No conflicts** > **Smallest fairness gap** > **Lowest total pain**

## Development

### Running Tests
```bash
pytest tests/
```

### Code Structure
- All UI modules live in `modules/`
- Database queries use Supabase Python client
- Async operations (calendar syncing) use `nest_asyncio`
- Caching is applied strategically via `@st.cache_data` and `@st.cache_resource`

### Contributing
1. Fork the repo
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make changes and run syntax checks: `python3 -m py_compile <file>`
4. Commit with descriptive messages
5. Push and open a pull request

## Deployment

### Streamlit Cloud
```bash
git push origin main  # Push to GitHub
# Then deploy via https://share.streamlit.io
```

### Docker
```bash
docker build -t nync .
docker run -p 8501:8501 nync
```

### Production Checklist
- [ ] All secrets configured in production environment
- [ ] Supabase Row-Level Security (RLS) policies enforced
- [ ] HTTPS enabled
- [ ] Email sender configured
- [ ] Webhook URLs tested
- [ ] Stripe webhooks configured

## Performance Notes

- Timezone selection uses a curated 80-timezone list (not all 593 pytz zones) for fast rendering
- Calendar conflicts cached per team per day to avoid repeated API calls
- Pain scores cached with 10-minute TTL
- Historical karma loaded once per suggestion calculation
- Guest votes checked for duplicates to prevent DB constraint errors

## License

MIT License — See LICENSE file for details.

## Support

- **Issues**: Report bugs on GitHub Issues
- **Questions**: Check the **Guide** tab in the app or open a discussion
- **Feedback**: Email support or message on our Discord

---

**Made with ⚡ by the Nync team.**  
Stop maximizing convenience. Start minimizing pain.
