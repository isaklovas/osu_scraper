import datetime
from bs4 import BeautifulSoup
import csv
import sys
import time
import threading
import requests
import math


def loading(message, stop):
    chars = ["\\", "|", "/", "-"]
    while True:
        for char in chars:
            if stop(): return
            print(message() + char, end="\r")
            time.sleep(0.2)


def clean_text(text: str):
    return text.replace("nbsp;", "").replace(",", "").strip()


def main():
    base_page = "https://osu.ppy.sh/rankings/osu/performance?"

    country = sys.argv[1].lower()
    start = int(sys.argv[2])
    end = int(sys.argv[3]) + 1
    csv_name = str(datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")) + "_" + country + "_" + "page" + str(start) + "-" + str(end - 1)
    time_start = time.time()

    if start < 1:
        print("Start range cannot be smaller than 1")
        return
    if end > 201:
        print("End range cannot be larger than 200")
        return

    stop_loading = False
    message = "Started scraping ... "

    loading_thread = threading.Thread(target=loading, args=[lambda : message, lambda : stop_loading])
    loading_thread.start()

    if country == "global":
        base_page += "page="
    else:
        base_page += "country=" + country + "&page="

    rank_string = "global" 
    if "country" in base_page: rank_string = "country"

    with open(csv_name + ".csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["user_id", "user_name", "name_len", f"{rank_string}_rank", "user_pp", "playcount", "user_acc", "ss", "s", "a"])

    for j, i in enumerate(range(start, end)):
        r = requests.get(base_page + str(i))
        with open(csv_name + ".csv", "a", newline="") as csvfile:
            writer = csv.writer(csvfile)
            soup = BeautifulSoup(r.text, "html.parser")
            users = soup.find_all("tr", {"class": "ranking-page-table__row"})
            for user in users:
                user_container = user.find_all("td")
                user_id = user_container[1].div.find_all("a")[1]["href"].split("/")[-2]
                user_name = user_container[1].div.find_all("a")[1].get_text().strip()
                user_rank = user_container[0].get_text().strip().removeprefix("#")
                user_acc = user_container[2].get_text().replace("nbsp;", "").replace(",", ".").strip()
                user_pc = clean_text(user_container[3].get_text())
                user_pp = clean_text(user_container[4].get_text())
                user_ss = clean_text(user_container[5].get_text())
                user_s = clean_text(user_container[6].get_text())
                user_a = clean_text(user_container[7].get_text())

                writer.writerow([user_id, user_name, len(user_name), user_rank, user_pp, user_pc, user_acc, user_ss, user_s, user_a])
        message = f"Finished scraping page {start + j}/{end - 1} ... "
        time.sleep(2) # to not get 429'd

    stop_loading = True
    print(f"finished scraping data from {(end - start) * 50} users in",
        f"{math.floor((time.time() - time_start) / 60)} min {math.floor((time.time() - time_start) % 60)} sec")


if __name__ == "__main__":
    main()