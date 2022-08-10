from bs4 import BeautifulSoup, element
import os
import requests
import pandas as pd
import numpy as np
import signal
from tqdm import tqdm

class LimitReachedException(Exception):
    pass

def exit_handler(sig, frame):
    raise KeyboardInterrupt

def main():
    urlhead = 'https://www.vgchartz.com/gamedb/?page='
    urltail = '&console=&region=All&developer=&publisher=&genre=&boxart=Both&ownership=Both'
    urltail += '&results=100&order=Sales&showtotalsales=0&showtotalsales=1&showpublisher=0'
    urltail += '&showpublisher=1&showvgchartzscore=0&shownasales=1&showdeveloper=1&showcriticscore=1'
    urltail += '&showpalsales=0&showpalsales=1&showreleasedate=1&showuserscore=1&showjapansales=1'
    urltail += '&showlastupdate=0&showlastupdate=1&showothersales=1&showgenre=1&showshipped=0&showshipped=1&sort=GL'

    csv_path = os.environ.get("CSV_PATH", os.getcwd())
    limit = int(os.environ.get("LIMIT", 0))

    max_retries = 100

    results = []
    rec_count = 0
    page = 1
    signal.signal(signal.SIGINT, exit_handler)
    signal.signal(signal.SIGTERM, exit_handler)
    try:
        with tqdm(total=1, unit="games") as myprogressbar:
            while True:
                error_count = 0
                try:
                    surl = urlhead + str(page) + urltail

                    r = requests.get(surl).text
                    soup = BeautifulSoup(r, "html.parser")

                    # vgchartz website is really weird so we have to search for
                    # <a> tags with game urls
                    game_tags = list(filter(
                        lambda x: x['href'].startswith('https://www.vgchartz.com/game/'),
                        # discard the first 10 elements because those
                        # links are in the navigation bar
                        soup.find_all("a", href=True)
                    ))

                    if len(game_tags) == 0:
                        break

                    result_count = int(soup.find("div", {"id": "generalBody"})
                                    .find_all("table")[1]
                                    .find("th").string
                                    .split()[1][1:-1].replace(",", ""))
                    myprogressbar.total = result_count

                    for tag in game_tags:
                        error_count = 0
                        if limit > 0 and rec_count >= limit:
                            raise LimitReachedException
                        try:
                            # get different attributes
                            # traverse up the DOM tree
                            data = tag.parent.parent.find_all("td")

                            game_name = " ".join(tag.string.split())

                            myprogressbar.set_description_str(f"{game_name[:15]:<15}")

                            release_date = data[14].string.split()
                            release_year = release_date[-1]
                            
                            last_update = data[15].string.split()
                            update_year = last_update[-1]
                            
                            result = [
                                game_name,
                                np.int32(data[0].string),
                                data[3].find('img').attrs['alt'].strip(),
                                data[4].string.strip(),
                                data[5].string.strip(),
                                *[float(data[idx].string.strip()) if not data[idx].string.startswith("N/A") else np.nan for idx in range(6, 8)],
                                *[float(data[idx].string[:-1].strip()) if not data[idx].string.startswith("N/A") else np.nan for idx in range(8, 14)]
                            ]
                            if release_year.startswith('N/A'):
                                result.append(np.nan)
                            else:
                                if int(release_year) >= 60:
                                    release_date[-1] = "19" + release_year
                                else:
                                    release_date[-1] = "20" + release_year
                                result.append(pd.to_datetime(f"{' '.join(release_date)}"))
                            
                            if update_year.startswith('N/A'):
                                result.append(np.nan)
                            else:
                                if int(update_year) >= 60:
                                    last_update[-1] = "19" + release_year
                                else:
                                    last_update[-1] = "20" + release_year
                                result.append(pd.to_datetime(f"{' '.join(last_update)}"))

                            # go to every individual website to get genre info
                            url_to_game = tag['href']
                            site_raw = requests.get(url_to_game).text
                            sub_soup = BeautifulSoup(site_raw, "html.parser")
                            # again, the info box is inconsistent among games so we
                            # have to find all the h2 and traverse from that to the genre name
                            h2s = sub_soup.find("div", {"id": "gameGenInfoBox"}).find_all('h2')
                            # make a temporary tag here to search for the one that contains
                            # the word "Genre"
                            temp_tag = element.Tag
                            for h2 in h2s:
                                if h2.string == 'Genre':
                                    temp_tag = h2
                            result.append(temp_tag.next_sibling.string.strip())

                            results.append(result)
                            rec_count += 1
                            myprogressbar.update(1)
                        except Exception as exc:
                            if error_count <= max_retries:
                                continue
                            raise exc
                    page += 1
                except LimitReachedException:
                    myprogressbar.close()
                    print("Limit reached.")
                    break
                except KeyboardInterrupt:
                    break
                except Exception as exc:
                    if error_count <= max_retries:
                        continue
                    raise exc
    except Exception as exc:
        print(exc)
    finally:
        df = pd.DataFrame(results, columns=[
            'Name', 'Rank', 'Platform', 'Publisher', 'Developer',
            'Critic_Score', 'User_Score', 'Total_Shipped', 'Total_Sales',
            'NA_Sales', 'PAL_Sales', 'JP_Sales', 'Other_Sales',
            'Release_Date', 'Last_Update', 'Genre'])
        print(df)
        df.to_csv(os.path.join(csv_path, "vgsales.csv"), sep=",", encoding='utf-8', index=False)
        print("Saved data to file")


if __name__ == "__main__":
    main()