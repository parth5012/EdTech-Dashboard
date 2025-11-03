
import requests
import pandas as pd
# import plotly.express as px
import re
from bs4 import BeautifulSoup

# -----------------------------
# 🔹 Platform Data Fetching Functions
# -----------------------------

def fetch_leetcode_data(username):
    try:
        url = f"https://leetcode-stats-api.herokuapp.com/{username}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if 'totalSolved' in data:
                return data
        return None
    except Exception as e:
        print(f"LeetCode fetch error: {e}")
        return None

def fetch_codeforces_data(username):
    try:
        url = f'https://codeforces.com/api/user.info?handles={username}'
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data["status"] == "OK":
                user = data["result"][0]
                return {
                    "rating": user.get("rating", "N/A"),
                    "maxRating": user.get("maxRating", "N/A"),
                    "rank": user.get("rank", "N/A"),
                    "maxRank": user.get("maxRank", "N/A")
                }
        return None
    except Exception as e:
        print(f"Codeforces fetch error: {e}")
        return None

# def fetch_codechef_data(username):
#     try:
#         url = f'https://codechef-api.vercel.app/{username}'
#         res = requests.get(url, timeout=10)
#         if res.status_code == 200:
#             data = res.json()
#             if "rating" in data:
#                 return data
#         return None
#     except Exception as e:
#         st.error(f"CodeChef fetch error: {e}")
#         return None

def fetch_github_data(username):
    url = f"https://api.github.com/users/{username}"
    try:
        response = requests.get(url, timeout=8)
        if response.status_code == 200:
            data = response.json()
            return {
                "login": data.get("login"),
                "name": data.get("name"),
                "bio": data.get("bio"),
                "public_repos": data.get("public_repos"),
                "followers": data.get("followers"),
                "following": data.get("following"),
                "created_at": data.get("created_at"),
                "avatar_url": data.get("avatar_url"),
                "html_url": data.get("html_url"),
            }
        else:
            return None
    except Exception as e:
        print(f"GitHub fetch error: {e}")
        return None

# def fetch_hackerrank_data(username):
#     try:
#         url = f"https://www.hackerrank.com/{username}"
#         res = requests.get(url, timeout=10)
#         if res.status_code == 200:
#             soup = BeautifulSoup(res.text, 'html.parser')
#             name_tag = soup.find("h1")
#             return {"name": name_tag.text.strip() if name_tag else username}
#         return None
#     except Exception as e:
#         st.error(f"HackerRank fetch error: {e}")
#         return None

# -----------------------------
# 🔹 Input Parsing Function
# -----------------------------
def parse_input(user_input):
    if not user_input:
        return None, None

    u = user_input.strip()
    u = re.sub(r"^https?://", "", u, flags=re.I)
    u = re.sub(r"^www\.", "", u, flags=re.I)
    u = u.split("?", 1)[0].split("#", 1)[0]

    platforms = {
        "leetcode.com": ("leetcode", r"(?:u/)?([^/]+)/?$"),
        "leetcode-cn.com": ("leetcode", r"(?:u/)?([^/]+)/?$"),
        "hackerrank.com": ("hackerrank", r"([^/]+)/?$"),
        "codeforces.com": ("codeforces", r"(?:profile/)?([^/]+)/?$"),
        "codechef.com": ("codechef", r"(?:users/)?([^/]+)/?$"),
        "github.com": ("github", r"([^/]+)/?$"),
    }

    for domain, (platform, pattern) in platforms.items():
        if domain.lower() in u.lower():
            match = re.search(pattern, u, flags=re.I)
            if match:
                username = match.group(1).strip()
                if username:
                    return platform, username
                else:
                    return None, None

    if "/" in u:
        parts = [p for p in u.split("/") if p]
        if len(parts) >= 2:
            fallback_username = parts[-1]
            return "leetcode", fallback_username

    return "leetcode", u

# -----------------------------
# 🔹 Streamlit UI
# -----------------------------
# st.set_page_config(page_title="Student Coding Dashboard", layout="wide")
# st.title("📊 Student Coding & Test Performance Dashboard")

# user_input = input("Enter your profile URL or username (LeetCode / Codeforces / CodeChef / HackerRank / GitHub):")

# platform, username = parse_input(user_input)

# uploaded_file = st.sidebar.file_uploader("📂 Upload CSV with Test Scores", type=["csv"])
# if uploaded_file:
#     try:
#         scores_df = pd.read_csv(uploaded_file)
#         # st.sidebar.success("✅ File Uploaded Successfully!")
#         # st.sidebar.dataframe(scores_df)
#     except Exception as e:
#         # st.sidebar.error(f"Error reading CSV: {e}")
#         print(f"Error reading CSV: {e}")

# -----------------------------
# 🔹 Fetch and Display Data
# -----------------------------
# if username:
#     if platform == "leetcode":
#         data = fetch_leetcode_data(username)
#         if data:
#             st.header(f"🐍 LeetCode Stats for **{username}**")
#             st.metric("Total Problems Solved", data.get("totalSolved", 0))
#             st.metric("Acceptance Rate (%)", data.get("acceptanceRate", 0))
#             difficulty_data = pd.DataFrame({
#                 "Difficulty": ["Easy", "Medium", "Hard"],
#                 "Solved": [data.get("easySolved", 0),
#                           data.get("mediumSolved", 0),
#                           data.get("hardSolved", 0)]
#             })
#             fig = px.pie(difficulty_data, names="Difficulty", values="Solved",
#                          title="Problems Solved by Difficulty")
#             st.plotly_chart(fig, use_container_width=True)
#         else:
#             st.error("❌ Could not fetch LeetCode data. Check username or API availability.")

#     elif platform == "codeforces":
#         data = fetch_codeforces_data(username)
#         if data:
#             st.header(f"⚡ Codeforces Stats for **{username}**")
#             st.metric("Current Rating", data["rating"])
#             st.metric("Max Rating", data["maxRating"])
#             st.write(f"**Rank:** {data['rank'].title()} | **Max Rank:** {data['maxRank'].title()}")
#         else:
#             st.error("❌ Could not fetch Codeforces data.")

#     elif platform == "codechef":
#         data = fetch_codechef_data(username)
#         if data:
#             st.header(f"🍴 CodeChef Stats for **{username}**")
#             st.metric("Rating", data.get("rating", "N/A"))
#             st.metric("Stars", data.get("stars", "N/A"))
#             st.write(f"🌍 Global Rank: {data.get('global_rank', 'N/A')}")
#             st.write(f"🇮🇳 Country Rank: {data.get('country_rank', 'N/A')}")
#         else:
#             st.error("❌ Could not fetch CodeChef data.")

#     elif platform == "hackerrank":
#         data = fetch_hackerrank_data(username)
#         if data:
#             st.header(f"💻 HackerRank Profile: {data['name']}")
#             st.info("Detailed HackerRank stats feature coming soon!")
#         else:
#             st.error("❌ Could not fetch HackerRank data.")
#     elif platform == "github":
#         data = fetch_github_data(username)
#         if data:
#             st.header(f"🐙 GitHub Profile for **{username}**")
#             st.metric("Public Repositories", data["public_repos"])
#             st.metric("Followers", data["followers"])
#             st.metric("Following", data["following"])
#             st.write(f"Name: {data['name']}")
#             st.write(f"Bio: {data['bio']}")
#             st.image(data['avatar_url'], width=120)
#             st.write(f"[Profile Link]({data['html_url']})")
#         else:
#             st.error("❌ Could not fetch GitHub data.")
#     else:
#         st.error("⚠️ Unsupported platform or invalid input.")

# -----------------------------
# 🔹 Test Score Visualization
# -----------------------------
# if uploaded_file:
#     st.header("📈 Test Scores Visualization")
#     try:
#         if "Test" in scores_df.columns and "Score" in scores_df.columns:
#             fig_score = px.bar(scores_df, x="Test", y="Score",
#                               title="Test Scores", text_auto=True)
#             st.plotly_chart(fig_score, use_container_width=True)
#         else:
#             st.warning("Your CSV must have 'Test' and 'Score' columns.")
#     except Exception as e:
#         st.error(f"Error plotting test scores: {e}")
def get_performance_score(json_content):
    platform, username = parse_input(json_content['platform link'][0])
    performance = 0
    if platform == 'leetcode':
        performance = fetch_leetcode_data(username).get('acceptanceRate')
    elif platform == "github":
        performance = fetch_github_data(username)
    elif platform == "codeforces":
        performance = fetch_codeforces_data(username)
    else:
        # It's a platform you don't recognize.
        # You could log this or set a specific value.
        print(f"Warning: Unknown platform '{platform}' encountered.")
        performance = -1  # Or None, or -1, etc.
    return performance