import os
import time
from datetime import datetime, timedelta

import pytz
from notion_client import Client
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

notion = Client(auth=os.environ["NOTION_TOKEN"])

blackbaudNameList = []
blackbaudDetailsList = []
notionNameList = []
notionIDList = []
notionIconList = []
gradeList = []

blackbaudNameList.clear()
blackbaudDetailsList.clear()
notionNameList.clear()
notionIDList.clear()
notionIconList.clear()
gradeList.clear()

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
options = webdriver.ChromeOptions()
options.add_argument('--window-size=1920,1080')
options.add_argument('--start-maximized')
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)
actions = ActionChains(driver)

driver.get("https://smtexas.myschoolapp.com/app/student#login")
time.sleep(2)
email = driver.find_element(By.ID, "Username")
email.send_keys("24rair@smtexas.org")
next = driver.find_element(By.ID, "nextBtn")
next.click()
time.sleep(5)
actions.send_keys(os.environ["ACCOUNT_PASSWORD"])
actions.perform()
actions.send_keys(Keys.ENTER)
actions.perform()
time.sleep(2)
actions.send_keys(Keys.ENTER)
actions.perform() #now logged in
WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.ID, "assignment-center-btn"))).click()
time.sleep(2)
monthView = driver.find_element(By.ID, "month-view")
monthView.click()
due = driver.find_element(By.XPATH, "//*[@data-sort='date_due']")
due.click()
time.sleep(5)
# get all assignments
assignment = driver.find_elements(By.XPATH, "//a[contains(@href,'assignmentdetail')]")
print(len(assignment))
i=0
for i in range(len(assignment)):
    fullDetails = ""
    # print(assignment[i].text.replace("\r", " ").replace("\n", " "))
    blackbaudNameList.append((assignment[i].text).strip().replace("\r", " ").replace("\n", " "))
    assignment[i].click()
    time.sleep(5)
    details = driver.find_element(By.XPATH, "//div[contains(@style,'margin-top:10px')]")
    print(details.text)
    fullDetails = fullDetails + details.text
    downloads = driver.find_elements(By.XPATH, "//div[contains(@class,'well')]")
    if(len(downloads) > 0):
        print("Downloads:")
        fullDetails = fullDetails + "\n\nDownloads:\n"
        files = driver.find_elements(By.XPATH, "//a[contains(@href,'/ftpimages')]")
        for j in range(len(files)):
            print(files[j].get_attribute("href"))
            fullDetails = fullDetails + files[j].get_attribute("href") + "\n"
        files = driver.find_elements(By.XPATH, "//div[contains(@class,'well')]//a[contains(@href,'http')]")
        for j in range(len(files)):
            print(files[j].get_attribute("href"))
            fullDetails = fullDetails + files[j].get_attribute("href") + "\n"
    print(fullDetails)
    blackbaudDetailsList.append(fullDetails)
    grade = driver.find_element(By.XPATH, "//span[contains(@class,'assignment-detail-status-label')]")
    gradeList.append(grade.text[8:len(grade.text)])
    driver.back()
    time.sleep(5)
    assignment = driver.find_elements(By.XPATH, "//a[contains(@href,'assignmentdetail')]")
    # time.sleep(2)

time.sleep(10)
driver.quit()

#if name is the same as another name, add number to end
for i in range(len(blackbaudNameList)):
    if blackbaudNameList.count(blackbaudNameList[len(blackbaudNameList) - i - 1]) > 1:
        blackbaudNameList[len(blackbaudNameList) - i - 1] = blackbaudNameList[len(blackbaudNameList) - i - 1] + " " + str(blackbaudNameList.count(blackbaudNameList[len(blackbaudNameList) - i - 1]))

#Add the assignment details to the corresponding Notion page
for i in range(len(notionNameList)):
    for j in range(len(blackbaudNameList)):
        if notionNameList[i] == blackbaudNameList[j]:
            print("Match found")
            print(notionNameList[i])
            print(blackbaudNameList[j])
            #check if details are already in Notion
            
            #if page is empty
            retries = 1
            success = False
            while not success:
                try:
                    retrieve = notion.blocks.retrieve(block_id = notionIDList[i])["has_children"]
                    success = True
                except:
                    wait = retries * 30
                    print('Error! Waiting %s secs and re-trying...' % wait)
                    time.sleep(wait)
                    retries += 1
            if not retrieve:
                print("Details not in Notion")
                retries = 1
                success = False
                while not success:
                    try:
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
                        success = True
                    except:
                        wait = retries * 30
                        print('Error! Waiting %s secs and re-trying...' % wait)
                        time.sleep(wait)
                        retries += 1
                
                
            else:
                retries2 = 1
                success2 = False
                while not success2:
                    try:
                        my_page = notion.blocks.children.list(block_id= notionIDList[i]).get("results")
                        blockID = my_page[0]["id"]
                        success2 = True
                    except:
                        wait2 = retries2 * 30
                        print('Error! Waiting %s secs and re-trying...' % wait2)
                        time.sleep(wait2)
                        retries2 += 1
                
                print("Details updated")
                retries4 = 1
                success4 = False
                while not success4:
                    try:
                        notion.blocks.delete(block_id = blockID)
                        success4 = True
                    except:
                        wait4 = retries4 * 30
                        print('Error! Waiting %s secs and re-trying...' % wait4)
                        time.sleep(wait4)
                        retries4 += 1
                retries3 = 1
                success3 = False
                while not success3:
                    try:
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
                        success3 = True
                    except:
                        wait3 = retries3 * 30
                        print('Error! Waiting %s secs and re-trying...' % wait3)
                        time.sleep(wait3)
                        retries3 += 1
                
            #add grade to Notion if available
            if(gradeList[j] != "d" and gradeList[j] != ""): #check if grade is available
                retries3 = 1
                success3 = False
                while not success3:
                    try:
                        notion.pages.update(
                            page_id = notionIDList[i],
                            properties={
                                "Grade": {
                                    "rich_text": [
                                        {
                                        "type": "text",
                                        "text": {
                                            "content": gradeList[j]
                                        }
                                        }
                                    ]
                                }
                            }
                        )
                        success3 = True
                    except:
                        wait3 = retries3 * 30
                        print('Error! Waiting %s secs and re-trying...' % wait3)
                        time.sleep(wait3)
                        retries3 += 1
                

# Add current date and time to database title
my_page = notion.databases.update(
    **{
        "database_id": "437cd227b8b946d485abdf2af1cbef3e",
        "title": [
            {
                        "text": {
                            "content": "Assignments as of " + str(datetime.now(pytz.timezone('America/Chicago')).strftime("%m/%d, %I:%M %p"))
                        }
            }
        ]
                
            }

)