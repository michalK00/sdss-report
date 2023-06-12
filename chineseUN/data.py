import time
from selenium import webdriver
from bs4 import BeautifulSoup
import pandas as pd
import re

driver = webdriver.Chrome("chromedriver.exe")
driver.maximize_window()
time.sleep(4)

base_url = "https://www.shanghairanking.com"
start_subdomain = "/rankings/bcur/2023"
driver.get(base_url + start_subdomain)
time.sleep(2)

universities = []
institutions_no = int(
    driver.find_element(
        "xpath", '(//div[@class="table-title"]/div)[last()]'
    ).text.split()[0]
)

data_frames = []


def get_stat(divs, div_index, span_index):
    try:
        value = divs[div_index].select("span")[span_index].text
        return None if value == "/" or value == "" else value
    except IndexError:
        return None


def extract_uni_data(passed_driver, unis_data, uni_name):
    soup = BeautifulSoup(passed_driver.page_source, "lxml")
    contact_info_divs = soup.find_all("div", {"class": "contact-item"})
    key_stats_divs = soup.find_all("div", {"class": "data-box"})

    founding_year = get_stat(contact_info_divs, 2, 1)
    total_enrollment = get_stat(key_stats_divs, 0, 0)
    total_enrollment_int_stud = get_stat(key_stats_divs, 1, 0)
    ug_enrollment = get_stat(key_stats_divs, 2, 0)
    ug_enrollment_int_stud = get_stat(key_stats_divs, 3, 0)
    g_enrollment = get_stat(key_stats_divs, 4, 0)
    g_enrollment_int_stud = get_stat(key_stats_divs, 5, 0)

    uni_data = pd.DataFrame(
        {
            "Institution": [uni_name],
            "Founding Year": [founding_year],
            "Total Students": [total_enrollment],
            "Total International Students": [total_enrollment_int_stud],
            "Undergraduate Students": [ug_enrollment],
            "Undergraduate International Students": [ug_enrollment_int_stud],
            "Graduate Students": [g_enrollment],
            "Graduate International Students": [g_enrollment_int_stud],
        }
    )
    return pd.concat([unis_data, uni_data])


uni_data = pd.DataFrame(
    columns=[
        "Institution",
        "Founding Year",
        "Total Students",
        "Total International Students",
        "Undergraduate Students",
        "Undergraduate International Students",
        "Graduate Students",
        "Graduate International Students",
    ]
)

unis_dict = {}

while sum(len(elem) for elem in data_frames) < institutions_no:
    soup = BeautifulSoup(driver.page_source, "lxml")

    table = soup.select("table")[0]

    data_frames.append(pd.read_html(str(table))[0])

    next_page = driver.find_element(
        "xpath", '(//a[@class="ant-pagination-item-link"])[last()]'
    )

    unis_elements = driver.find_elements("xpath", '(//span[@class="univ-name"])')
    uni_urls = [url for url in soup.find_all("a") if "/institution/" in str(url)]
    pattern = r'href="([^"]*)"[^>]*>([^<]*)<'
    unis_subdict = {}

    for url in uni_urls:
        match = re.search(pattern, str(url))

        if match:
            name = url.findChild("span", recursive=False).text.strip()
            href_value = match.group(1)
            unis_dict[name] = href_value

    unis_dict.update(unis_subdict)

    time.sleep(1)
    if next_page:
        next_page.click()
        time.sleep(1)
    else:
        break

for uni in unis_dict:
    driver.get(base_url + unis_dict[uni])
    time.sleep(0.5)
    uni_data = extract_uni_data(driver, uni_data, uni)

driver.close()
merged_df = pd.concat(data_frames)

merged_df = merged_df.reset_index(drop=True)
merged_df.rename(columns={"Unnamed: 2": "Region"}, inplace=True)
all_in_one = pd.merge(merged_df, uni_data, on="Institution")

all_in_one.to_csv("uni_data.csv", sep=",")
