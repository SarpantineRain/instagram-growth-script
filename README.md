# Instagram Growth Script

A Selenium-based Python bot that browses Instagram hashtag search results, optional location feeds, and your home feed, then likes posts and follows authors it has not seen before. It keeps local history files so it does not repeat the same posts or accounts.

> **Warning:** This script automates actions on Instagram (likes and follows) at a scale that Instagram's Terms of Use and Community Guidelines prohibit. Using it can get the account it runs on temporarily restricted, action-blocked, or permanently banned. Use it only on accounts you are willing to lose, at low volumes, and at your own risk. The author takes no responsibility for account actions, data loss, or any other consequences.

## Features

- **Hashtag targeting.** Searches each hashtag in `TARGET_HASHTAGS`, collects recent post and Reel links, and interacts with them in random order.
- **Optional location targeting.** If `LOCATION_URL` is set, it also works through that location's "Recent" feed.
- **Home feed warm-up.** Likes a few posts on your home feed each cycle so the session looks more like normal use.
- **Deduplication.** Records every processed post in `visited_posts.txt` and every processed author in `visited_users.txt`. Neither is repeated across runs.
- **Comment-safe liking.** Like buttons inside comment sections are skipped.
- **Double-tap fallback.** If no like button is found, it double-clicks the media instead.
- **Randomized timing.** Delays between actions and between cycles are randomized to look less mechanical.
- **Persistent login.** The Chrome profile is saved in `./chrome_profile`, so you only log in manually the first time.

## Requirements

- Python 3.9 or newer
- Google Chrome installed
- Python packages:
  ```bash
  pip install selenium webdriver-manager
  ```
  `webdriver-manager` downloads a matching ChromeDriver automatically on first run.

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/SarpantineRain/instagram-growth-script.git
   cd instagram-growth-script
   ```

2. Open `instagram_growth_script.py` and edit the configuration block at the top:

   ```python
   USERNAME = "your_account_username"      # Used to detect that you're logged in

   TARGET_HASHTAGS = [                     # Hashtags to browse, one picked per cycle
       "marketing",
       "branding",
       "design",
   ]

   LOCATION_URL = ""                       # Optional: an Instagram location "recent" URL

   MAX_DAILY_LIKES = 300
   MAX_DAILY_FOLLOWS = 50
   ```

3. Run the script:
   ```bash
   python instagram_growth_script.py
   ```

4. If no saved session is found, a Chrome window opens on the Instagram login page. Log in manually, including any two-factor step. The script detects the login automatically and continues. You have about 48 seconds to finish logging in.

## How it works

Each cycle does the following:

1. Picks a random hashtag from `TARGET_HASHTAGS` (cycles through the full list before repeating).
2. If `LOCATION_URL` is set, collects up to 25 unseen posts from that location feed and processes them.
3. Collects up to 20 unseen posts from the hashtag's search results and processes them.
4. Warms up the home feed with up to 4 likes.
5. Prints a session summary and waits 60 to 120 seconds before the next cycle.

Processing a single post:

- Opens the post and reads its author.
- Skips it if the author is already in `visited_users.txt`.
- Clicks **Follow** if it is available.
- Clicks **Like** if it is available, or double-clicks the media as a fallback.
- Logs the post and author to the history files.

## Output

The script prints one line per action and a summary after each cycle, for example:

```
--- [2. HASHTAG] #design (Target: 20) ---
  └ Found posts for #design: 20. Processing...
  └ [#design] Post liked successfully!
  └ [#design] Successfully followed @someone!

[SESSION SUMMARY] Likes=42/300, Follows=8/50
[DATABASE] Unique posts: 310 | Unique users: 145
```

## Known limitations

- **Limits reset on restart.** `MAX_DAILY_LIKES` and `MAX_DAILY_FOLLOWS` are counted in memory for the current run only. Restarting the script resets them, so the limits are not true daily caps.
- **Selector fragility.** The script finds buttons by English, Russian, and Hungarian labels and by Instagram's CSS class names. Instagram changes its markup often, so some actions may silently stop working.
- **Browser automation is detectable.** Instagram can detect automated sessions, which is one more reason to keep volumes low.
- **Single account.** Each run controls one logged-in account.

## Files created at runtime

| File | Purpose |
| --- | --- |
| `chrome_profile/` | Saved Chrome profile, including the Instagram session. Keep it private. |
| `visited_posts.txt` | Post URLs already processed. |
| `visited_users.txt` | Author usernames already processed. |

Add these to `.gitignore`. Never commit them, because they contain session data and account information.

## Responsible use

If you run this script, consider:

- Keeping daily volumes far below the defaults. The defaults are high enough to trigger action blocks on many accounts.
- Using it only on accounts you own, and never to harass, spam, or mass-follow people who have not opted in.
- Reading Instagram's Terms of Use and accepting the risk of account restrictions.

## Disclaimer

This project is provided for educational purposes, without warranty of any kind. You are responsible for how you use it and for complying with the terms of every platform you connect to.

## License

Choose a license before publishing (for example MIT). Until then, all rights are reserved by the author.
