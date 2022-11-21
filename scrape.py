import csv
import time
import argparse
import datetime
import requests
import threading
from bs4 import BeautifulSoup


def loading(message, stop):
    chars = ["\\", "|", "/", "-"]
    while True:
        for char in chars:
            if stop(): return
            print(message() + char + "\0", end="\r")
            time.sleep(0.2)

def clean_text(text: str):
    return text.replace("nbsp;", "").replace(",", "").strip()

def clear():
    print("\0" * 100, end="\r")

def get_time():
    return datetime.datetime.now().strftime("%H:%M:%S")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("country", default="global", nargs="?")
    parser.add_argument("start", default=1, type=int, nargs="?")
    parser.add_argument("end", default=200, type=int, nargs="?")
    parser.add_argument("-d", "--detailed", action="store_true")
    args = parser.parse_args()

    start = args.start
    end = args.end + 1
    country = args.country

    base_page = "https://osu.ppy.sh/rankings/osu/performance?"
    csv_name = str(datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")) + "_" + country + "_" +\
        "page" + str(start) + "-" + str(end - 1) + ("_detailed" if args.detailed else "")
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

    rank_string = "country" if "country" in base_page else "global"

    # all code below is horrible aaaaaaaa

    if args.detailed:
        cols = ["user_id", "user_name", "prev_username", "name_len", "title", f"{rank_string}_rank",
                "user_pp", "playcount", "user_acc", "ss", "s", "a", "badge_count", "badge_names",
                "join_date", "last_active", "location", "occupation", "interests", "website", "twitter",
                "playstyle", "is_supporter"]
    else:
        cols = ["user_id", "user_name", "name_len", f"{rank_string}_rank",
                "user_pp", "playcount", "user_acc", "ss", "s", "a"]

    with open(csv_name + ".csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(cols)

    print(f"[{get_time()}] Started scraping...")

    for j, i in enumerate(range(start, end)):
        soup = BeautifulSoup(requests.get(base_page + str(i)).text, "html.parser")
        users = soup.find_all("tr", {"class": "ranking-page-table__row"})

        if not args.detailed:
            message = f"Scraping page {start + j}/{end - 1} ... "
            # kinda messy but its the easiest way i could find
            # to save per user when doing detailed scraping
            # and only save per page when doing normal scraping
            csvfile = open(csv_name + ".csv", "a", newline="", errors="ignore")

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

            if args.detailed:
                message = f"Scraping page {start + j}/{end - 1} ... " +\
                    f"scraping data from user {users.index(user)}/{len(users)} ... "

                profile_url = f"https://old.ppy.sh/u/{user_id}#_general"
                soup = BeautifulSoup(requests.get(profile_url).text, "html.parser")
                userbox = soup.find("div", {"class": "centrep userbox"})

                previous_username = None
                user_title = None
                is_supporter = False
                has_pfp = False

                previous_username_div = userbox.find("div", {"class": "profile-username"})

                if "title" in previous_username_div.attrs:
                    previous_username = previous_username_div["title"].replace("Previously known as ", "").strip()

                if userbox.find("div", {"class": "avatar-holder"}) is not None:
                    has_pfp = True

                if not has_pfp:
                    title_index = 2
                else:
                    title_index = 3

                if userbox.find("div", {"class": "profileSupporter"}) is not None:
                    is_supporter = True

                userbox = userbox.find_all("div")

                if userbox[title_index].img is None:
                    user_title = userbox[title_index].get_text().strip()

                badge_index = 2

                if has_pfp:
                    badge_index += 1
                if user_title is not None:
                    badge_index += 1

                if is_supporter:
                    badge_end_index = -2
                else:
                    badge_end_index = -1

                badges = userbox[badge_index:badge_end_index]
                badge_count = len(badges)
                badge_names = ",".join([badge.img["title"] for badge in badges])

                if badge_count == 0:
                    badge_names = None

                profile_details = soup.find("div", {"class": "profile-details"})
                profile_details = profile_details.find_all("div")

                last_active = None;location = None;occupation = None
                interests = None;website = None;twitter = None

                for ele in profile_details:
                    if "title" in ele.attrs:
                        # the discord field doesn't exist on old website
                        if ele["title"] == "Arrived":
                            join_date = ele.div.get_text().strip()
                        elif ele["title"] == "Last Active":
                            last_active = ele.div.get_text().strip()
                        elif ele["title"] == "Location":
                            location = ele.div.get_text().strip()
                        elif ele["title"] == "Occupation":
                            occupation = ele.div.get_text().strip()
                        elif ele["title"] == "Interests":
                            interests = ele.div.get_text().strip()
                        elif ele["title"] == "Website":
                            website = ele.div.get_text().strip()
                        elif ele["title"] == "Twitter":
                            twitter = ele.div.get_text().strip()

                playstyle_container = soup.find("div", {"class": "playstyle-container"})
                playstyle_container = playstyle_container.find_all("div")

                playstyles = []

                for playstyle in playstyle_container:
                    playstyle = playstyle["class"]
                    if playstyle[-1] == "using":
                        playstyles.append(playstyle[1])
                playstyles = ",".join(playstyles)

                if playstyles == "":
                    playstyles = None

                with open(csv_name + ".csv", "a", newline="", errors="ignore") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([user_id, user_name, previous_username, len(user_name), user_title, user_rank,
                    user_pp, user_pc, user_acc, user_ss, user_s, user_a, badge_count, badge_names, join_date,
                    last_active, location, occupation, interests, website, twitter, playstyles, is_supporter])
                time.sleep(1.2) # user profile sleep
            else:
                writer = csv.writer(csvfile)
                writer.writerow([user_id, user_name, len(user_name), user_rank,
                            user_pp, user_pc, user_acc, user_ss, user_s, user_a])

        if not args.detailed:
            csvfile.close()
        time.sleep(2) # page sleep

    stop_loading = True
    clear()
    print(f"[{get_time()}] Finished scraping data from {(end - start) * 50} users in",
        f"{((time.time() - time_start) / 60):.0f} min {((time.time() - time_start) % 60):.0f} sec")


if __name__ == "__main__":
    main()
