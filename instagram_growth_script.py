import os
import re
import time
import random
import warnings
import urllib.parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

warnings.filterwarnings("ignore", category=Warning)

# ==================== CONFIGURATION ====================
# Your Instagram account handle (used to verify active login session)
USERNAME = "your_account_username"

# Target hashtags to scrape and interact with
TARGET_HASHTAGS = [
    "marketing",
    "branding",
    "entrepreneur",
    "design",
    "business",
    "startup"
]

# Optional: Specific location explore/recent URL (Leave empty or set to target location URL)
# Example location URL format: "https://www.instagram.com/explore/locations/YOUR_LOCATION_ID/location-name/recent/"
LOCATION_URL = "" 

# Daily safety thresholds
MAX_DAILY_LIKES = 300
MAX_DAILY_FOLLOWS = 50

# Local history records to prevent duplicate actions
POST_HISTORY_FILE = "visited_posts.txt"
USER_HISTORY_FILE = "visited_users.txt"
# =======================================================


def normalize_post_url(url):
    """Strips extra parameters, keeping clean post/reel ID link."""
    match = re.search(r'(https?://www\.instagram\.com/(?:p|reel)/[^/]+)', url)
    if match:
        return match.group(1) + "/"
    return url.split("?")[0]


def load_history(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()


def save_history(filename, item):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"{item}\n")


VISITED_POSTS = load_history(POST_HISTORY_FILE)
VISITED_USERS = load_history(USER_HISTORY_FILE)


def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--start-maximized")

    user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
    options.add_argument(f"--user-data-dir={user_data_dir}")

    options.add_argument(
        "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver


def check_if_logged_in(driver):
    try:
        profile_element = driver.find_elements(
            By.XPATH,
            f"//a[contains(@href, '/{USERNAME}/')] | //*[name()='svg'][@aria-label='Home' or @aria-label='Главная страница']"
        )
        return len(profile_element) > 0
    except Exception:
        return False


def login(driver):
    print("Opening Instagram...")
    driver.get("https://www.instagram.com/")
    time.sleep(2)

    if check_if_logged_in(driver):
        print("Session found! Already logged in.")
        return

    print("\nMANUAL AUTHORIZATION REQUIRED! Log into your account in the browser window...")
    driver.get("https://www.instagram.com/accounts/login/")

    for _ in range(24):
        if check_if_logged_in(driver):
            print("Successful login detected!")
            return
        time.sleep(2)


def safe_sleep(min_sec=1.2, max_sec=2.5):
    time.sleep(random.uniform(min_sec, max_sec))


def native_click(driver, element):
    try:
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", element)
        time.sleep(0.2)

        actions = ActionChains(driver)
        actions.move_to_element(element).pause(0.1).click().perform()
        return True
    except Exception:
        try:
            driver.execute_script(
                "var evt = document.createEvent('MouseEvents');"
                "evt.initMouseEvent('click', true, true, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);"
                "arguments[0].dispatchEvent(evt);",
                element
            )
            return True
        except Exception:
            return False


def get_post_author(driver):
    """Extracts the post author username (supports regular posts and Reels)"""
    try:
        author_elems = driver.find_elements(
            By.XPATH,
            "//header//a[contains(@href, '/') and not(contains(@href, '/explore/')) and not(contains(@href, '/p/')) and not(contains(@href, '/reel/'))]"
        )
        for elem in author_elems:
            href = elem.get_attribute("href")
            if href:
                user = href.strip("/").split("/")[-1]
                if user and user not in ["explore", "reels", "direct"]:
                    return user
    except Exception:
        pass
    return None


def collect_massive_post_urls(driver, target_count=25):
    """Scrolls feed deeply and collects unique post/reel URLs"""
    unique_urls = []
    scroll_attempts = 0

    while len(unique_urls) < target_count and scroll_attempts < 15:
        post_elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/p/') or contains(@href, '/reel/')]")
        all_found = [p.get_attribute("href") for p in post_elements if p.get_attribute("href")]

        for url in all_found:
            clean_url = normalize_post_url(url)
            if clean_url not in VISITED_POSTS and clean_url not in unique_urls:
                unique_urls.append(clean_url)

        driver.execute_script(f"window.scrollBy(0, {random.randint(900, 1600)});")
        time.sleep(1.0)
        scroll_attempts += 1

    random.shuffle(unique_urls)
    return unique_urls[:target_count]


def process_posts_list(driver, post_urls, context_label="Target"):
    likes_done = 0
    follows_done = 0

    for url in post_urls:
        clean_url = normalize_post_url(url)
        if clean_url in VISITED_POSTS:
            continue

        VISITED_POSTS.add(clean_url)
        save_history(POST_HISTORY_FILE, clean_url)

        driver.get(clean_url)
        safe_sleep(2.0, 3.5)

        # Check post author
        author = get_post_author(driver)
        if author and author in VISITED_USERS:
            print(f"  └ [{context_label}] Author @{author} already processed. Skipping...")
            continue

        if author:
            VISITED_USERS.add(author)
            save_history(USER_HISTORY_FILE, author)

        # --- FOLLOW ACTION ---
        follow_candidates = driver.find_elements(
            By.XPATH,
            "//*[text()='Follow' or text()='Подписаться' or text()='Követés']/ancestor::button[1] | //*[text()='Follow' or text()='Подписаться' or text()='Követés']/parent::div[1]"
        )

        for cand in follow_candidates:
            if cand.is_displayed():
                text_content = cand.text
                if "Following" in text_content or "Подписки" in text_content or "Követve" in text_content:
                    break

                if native_click(driver, cand):
                    follows_done += 1
                    print(f"  └ [{context_label}] Successfully followed @{author or 'user'}!")
                    safe_sleep(1.0, 1.8)
                    break

        # --- LIKE ACTION (STRICTLY AVOIDING COMMENTS) ---
        like_clicked = False

        like_candidates = driver.find_elements(
            By.XPATH,
            "//section[not(contains(@class, 'comment'))]//*[name()='svg'][@aria-label='Like' or @aria-label='Нравится' or @aria-label='Tetszik']/ancestor::button[1] | "
            "//span[contains(@class, 'x1lliihq')]//*[name()='svg'][@aria-label='Like' or @aria-label='Нравится' or @aria-label='Tetszik']/ancestor::button[1]"
        )

        for cand in like_candidates:
            try:
                parent_comment = cand.find_elements(By.XPATH,
                                                    "./ancestor::ul | ./ancestor::li | ./ancestor::div[contains(@role, 'row')]")
                if parent_comment:
                    continue
            except Exception:
                pass

            if cand.is_displayed():
                unlikes = cand.find_elements(By.XPATH,
                                             ".//*[name()='svg'][@aria-label='Unlike' or @aria-label='Не нравится']")
                if unlikes:
                    like_clicked = True
                    break

                if native_click(driver, cand):
                    likes_done += 1
                    like_clicked = True
                    print(f"  └ [{context_label}] Post liked successfully!")
                    safe_sleep(1.0, 1.8)
                    break

        # Fallback option: Double click directly on media element
        if not like_clicked:
            try:
                media_elements = driver.find_elements(
                    By.XPATH,
                    "//article//div[contains(@role, 'button')]//img | //main//img[contains(@class, 'x5yr21d')] | //video"
                )
                for media in media_elements:
                    if media.is_displayed() and media.size['height'] > 250:
                        actions = ActionChains(driver)
                        actions.double_click(media).perform()
                        likes_done += 1
                        print(f"  └ [{context_label}] Liked via double-click on media!")
                        break
            except Exception:
                pass

        safe_sleep(1.2, 2.5)

    return likes_done, follows_done


def module_target_location(driver, max_interactions=25):
    if not LOCATION_URL:
        return 0, 0
    
    print(f"\n--- [1. LOCATION] Explore Recent (Target: {max_interactions}) ---")
    driver.get(LOCATION_URL)
    safe_sleep(2.5, 4.0)

    try:
        post_urls = collect_massive_post_urls(driver, target_count=max_interactions)

        if not post_urls:
            print("  └ No posts found for location. Skipping...")
            return 0, 0

        print(f"  └ Found posts: {len(post_urls)}. Processing...")
        return process_posts_list(driver, post_urls, context_label="Location Geo")

    except Exception as e:
        print(f"  └ Location error: {e}")
        return 0, 0


def module_target_hashtags(driver, hashtag, max_interactions=20):
    encoded_tag = urllib.parse.quote(f"#{hashtag}")
    search_url = f"https://www.instagram.com/explore/search/keyword/?q={encoded_tag}"

    print(f"\n--- [2. HASHTAG] #{hashtag} (Target: {max_interactions}) ---")
    driver.get(search_url)
    safe_sleep(2.5, 4.0)

    try:
        post_urls = collect_massive_post_urls(driver, target_count=max_interactions)

        if not post_urls:
            print(f"  └ No posts found for #{hashtag}. Skipping...")
            return 0, 0

        print(f"  └ Found posts for #{hashtag}: {len(post_urls)}. Processing...")
        return process_posts_list(driver, post_urls, context_label=f"#{hashtag}")

    except Exception as e:
        print(f"  └ Hashtag error #{hashtag}: {e}")
        return 0, 0


def module_scroll_feed(driver, max_likes=4):
    print("\n--- [3. HOME FEED] Profile Warmup ---")
    driver.get("https://www.instagram.com/")
    safe_sleep(2.5, 4.0)

    likes_done = 0
    scroll_attempts = 0

    while likes_done < max_likes and scroll_attempts < 8:
        scroll_attempts += 1

        like_elements = driver.find_elements(
            By.XPATH,
            "//article//*[name()='svg'][@aria-label='Like' or @aria-label='Нравится' or @aria-label='Tetszik']/ancestor::*[(self::button or @role='button') and not(ancestor::section[contains(@class, 'comment')])][1]"
        )

        clicked_in_this_scroll = False

        for elem in like_elements:
            if elem.is_displayed():
                unlikes = elem.find_elements(By.XPATH,
                                             ".//*[name()='svg'][@aria-label='Unlike' or @aria-label='Не нравится']")
                if unlikes:
                    continue

                if native_click(driver, elem):
                    likes_done += 1
                    clicked_in_this_scroll = True
                    print(f"  └ [Feed] Like! ({likes_done}/{max_likes})")
                    safe_sleep(1.2, 2.2)
                    break

        if not clicked_in_this_scroll:
            try:
                feed_images = driver.find_elements(By.XPATH, "//article//img | //article//video")
                for img in feed_images:
                    if img.is_displayed() and img.size['height'] > 200:
                        actions = ActionChains(driver)
                        actions.double_click(img).perform()
                        likes_done += 1
                        print(f"  └ [Feed] Double-click like! ({likes_done}/{max_likes})")
                        safe_sleep(1.2, 2.2)
                        break
            except Exception:
                pass

        driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
        time.sleep(random.uniform(1.0, 2.0))

    return likes_done


def main():
    driver = init_driver()
    try:
        login(driver)
        if not check_if_logged_in(driver):
            print("\nAuthorization failed. Terminating script.")
            return

        total_likes_today = 0
        total_follows_today = 0

        available_hashtags = list(TARGET_HASHTAGS)

        while total_likes_today < MAX_DAILY_LIKES and total_follows_today < MAX_DAILY_FOLLOWS:

            if not available_hashtags:
                available_hashtags = list(TARGET_HASHTAGS)

            hashtag = available_hashtags.pop(random.randint(0, len(available_hashtags) - 1))

            # 1. Location Module (if URL provided)
            loc_likes, loc_follows = module_target_location(driver, max_interactions=25)

            # 2. Hashtag Module
            h_likes, h_follows = module_target_hashtags(driver, hashtag, max_interactions=20)

            # 3. Home Feed Warmup Module
            f_likes = module_scroll_feed(driver, max_likes=4)

            total_likes_today += (loc_likes + h_likes + f_likes)
            total_follows_today += (loc_follows + h_follows)

            print(
                f"\n[SESSION SUMMARY] Likes={total_likes_today}/{MAX_DAILY_LIKES}, Follows={total_follows_today}/{MAX_DAILY_FOLLOWS}")
            print(f"[DATABASE] Unique posts: {len(VISITED_POSTS)} | Unique users: {len(VISITED_USERS)}")

            # Pause between execution cycles (1 to 2 minutes)
            time.sleep(random.uniform(60, 120))

    finally:
        driver.quit()
        print("\nScript execution finished.")


if __name__ == "__main__":
    main()