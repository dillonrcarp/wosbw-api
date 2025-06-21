import asyncio
from collections import Counter
from flask import Flask, Response
from bs4 import BeautifulSoup
from pyppeteer import launch

app = Flask(__name__)

# 1) Render the WOS mirror page and grab the HTML
async def fetch_html(url):
    browser = await launch(args=["--no-sandbox"])
    page = await browser.newPage()
    await page.goto(url, waitUntil="networkidle2")
    html = await page.content()
    await browser.close()
    return html

# 2) Parse the letter/count pairs out of the scramble
def parse_letter_counts(html):
    soup = BeautifulSoup(html, "html.parser")
    counts = Counter()
    for div in soup.select(".Game_letter__jIgKJ"):
        for li in div.select("ul li"):
            letter = li.contents[0].strip().lower()
            count  = int(li.find("span").get_text())
            counts[letter] += count
    return counts

# 3) Find all the longest words you can build
def find_big_words(available_counts, dict_path="enable1.txt"):
    longest, max_len = [], 0
    with open(dict_path) as f:
        for w in f:
            word = w.strip().lower()
            freq = Counter(word)
            # can’t use a letter more than we have
            if all(freq[ch] <= available_counts[ch] for ch in freq):
                l = len(word)
                if l > max_len:
                    longest, max_len = [word], l
                elif l == max_len:
                    longest.append(word)
    return longest

@app.route("/")
def big_word():
    url = "https://wos.gg/r/ad66e7bc-81d9-435e963c-a6159cb13282"
    # fetch + parse
    html = asyncio.get_event_loop().run_until_complete(fetch_html(url))
    counts = parse_letter_counts(html)
    candidates = find_big_words(counts)
    # return first—or empty string if none
    return Response(candidates[0] if candidates else "", mimetype="text/plain")

if __name__ == "__main__":
    app.run(host="0.0.0.0")
