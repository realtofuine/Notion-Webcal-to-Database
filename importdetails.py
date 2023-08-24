import os
import time

import chromedriver_autoinstaller
from notion_client import Client
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

notion = Client(auth=os.environ["NOTION_TOKEN"])

blackbaudNameList = []
blackbaudDetailsList = []
notionNameList = []
notionIDList = []
notionIconList = []

blackbaudNameList.clear()
blackbaudDetailsList.clear()
notionNameList.clear()
notionIDList.clear()
notionIconList.clear()

# Read Notion data and save name field to list
my_page = notion.databases.query(
    **{
        "database_id": "437cd227b8b946d485abdf2af1cbef3e",
        "filter": {
            "and": [
            {"property": "Name",
            "rich_text": {
                    "contains": "",
                    "is_not_empty": True
                } },
            {"property": "Due",
            "date": {
                "contains": "",
                "is_not_empty": True
            }
            }
            ]
        }
    }
).get("results")

for result in my_page:
    print(str(result['properties']['Name']['title'][0]['text']['content']))
    print(str(result['properties']['Due']['date']['start']))
    print(str(result['properties']['Assign']['date']['start']))
    print(str(result['id']))
    notionNameList.append(str(result['properties']['Name']['title'][0]['text']['content']))
    notionIDList.append(str(result['id']))


# Read Blackbaud data
display = Display(visible=0, size=(800, 800))  
display.start()
chromedriver_autoinstaller.install()
chrome_options = webdriver.ChromeOptions()
options = [
  # Define window size here
   #"--window-size=1200,1200",
    #"--ignore-certificate-errors"
 
    "--headless",
    #"--disable-gpu",
    #"--window-size=1920,1200",
    #"--ignore-certificate-errors",
    #"--disable-extensions",
    #"--no-sandbox",
    #"--disable-dev-shm-usage",
    #'--remote-debugging-port=9222'
]
for option in options:
    chrome_options.add_argument(option)

driver = webdriver.Chrome(options = chrome_options)
actions = ActionChains(driver)

driver.get("https://smtexas.myschoolapp.com/app/student#login")
time.sleep(2)
email = driver.find_element(By.ID, "Username")
email.send_keys("24rair@smtexas.org")
next = driver.find_element(By.ID, "nextBtn")
next.click()
time.sleep(5)
actions.send_keys("yzG6x5p@%$ztEc!i")
actions.perform()
actions.send_keys(Keys.ENTER)
actions.perform()
time.sleep(2)
actions.send_keys(Keys.ENTER)
actions.perform()
time.sleep(5) #now logged in
assignmentCenter = driver.find_element(By.ID, "assignment-center-btn")
assignmentCenter.click()
time.sleep(2)
monthView = driver.find_element(By.ID, "month-view")
monthView.click()
due = driver.find_element(By.XPATH, "//*[@data-sort='date_due']")
due.click()
time.sleep(2)
# get all assignments
assignment = driver.find_elements(By.XPATH, "//a[contains(@href,'assignmentdetail')]")
for i in range(len(assignment)):
    fullDetails = ""
    print(assignment[i].text)
    blackbaudNameList.append(assignment[i].text)
    assignment[i].click()
    time.sleep(2)
    details = driver.find_element(By.XPATH, "//div[contains(@style,'margin-top:10px')]")
    print(details.text)
    fullDetails = fullDetails + details.text
    downloads = driver.find_elements(By.XPATH, "//div[contains(@class,'well')]")
    if(len(downloads) > 0):
        print("Downloads:")
        fullDetails = fullDetails + "Downloads:\n"
        files = driver.find_elements(By.XPATH, "//a[contains(@href,'/ftpimages')]")
        for j in range(len(files)):
            print(files[j].get_attribute("href"))
            fullDetails = fullDetails + files[j].get_attribute("href")
        files = driver.find_elements(By.XPATH, "//div[contains(@class,'well')]//a[contains(@href,'http')]")
        for j in range(len(files)):
            print(files[j].get_attribute("href"))
            fullDetails = fullDetails + files[j].get_attribute("href")
    print(fullDetails)
    blackbaudDetailsList.append(fullDetails)
    driver.back()
    time.sleep(2)
    assignment = driver.find_elements(By.XPATH, "//a[contains(@href,'assignmentdetail')]")
    time.sleep(2)

time.sleep(10)
driver.quit()

#Add the assignment details to the corresponding Notion page
for i in range(len(notionNameList)):
    for j in range(len(blackbaudNameList)):
        if notionNameList[i] == blackbaudNameList[j]:
            print("Match found")
            print(notionNameList[i])
            print(blackbaudNameList[j])
            #check if details are already in Notion
            if not notion.blocks.retrieve(block_id = notionIDList[i])["has_children"]:
                print("Details not in Notion")
                notion.blocks.children.append(
                    block_id = notionIDList[i],
                    children = [
                        {
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                            "rich_text": [
                                {
                                "type": "text",
                                "text": {
                                    "content": blackbaudDetailsList[j]
                                }
                                }
                            ]
                            }
                        }
                    ]
                )