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

classList = ["adv topics", "ap chem", "comp sci", "phy c", "apush", "eng war"]

for subject in classList:
    if(subject == "adv topics"):
        notionID = "5e635587dd8a4687a7c5b4f51bc55962"
        className = "Advanced Topics in Mathematics - H - 1 (F)"
    elif(subject == "ap chem"):
        notionID = "4192926577004b29a6a90e85bf8b2168"
        className = "AP Chemistry - 1 (A)"
    elif(subject == "comp sci"):
        notionID = "835c93790fc7403f9818d19d2b511885"
        className = "AP Computer Science A - 1 (G)"
    elif(subject == "phy c"):
        notionID = "54d788f0d79e40889cbb2a79a159f269"
        className = "AP Physics C: Mechanics, Electricity and Magnetism - 1 (D)"
    elif(subject == "apush"):
        notionID = "a746dc5152e64507911107ab34ee8ae4"
        className = "AP United States History - 2 (C)"
    elif(subject == "eng war"):
        notionID = "b2f3bb600d884195bff2f088a3a4efcf"
        className = "English 12 - Literature of War & Survival - 2 (H)"

    blackbaudNameList = []
    blackbaudGradeList = []
    blackbaudNotesList = []
    notionNameList = []
    notionGradeList = []
    notionNotesList = []

    blackbaudNameList.clear()
    blackbaudGradeList.clear()
    blackbaudNotesList.clear()
    notionNameList.clear()
    notionGradeList.clear()
    notionNotesList.clear()

    # Read Notion data and save name field to list
    my_page = notion.databases.query(
        **{
            "database_id": notionID,
            "filter": {
                "and": [
                {"property": "Name",
                "rich_text": {
                        "contains": "",
                        "is_not_empty": True
                    } },
                {"property": "Points",
                "rich_text": {
                    "contains": "",
                    "is_not_empty": True
                }
                }
                ]
            }
        }
    ).get("results")

    for result in my_page:
        print(result)
        print(str(result['properties']['Name']['title'][0]['text']['content']))
        print(str(result['properties']['Points']['rich_text'][0]['text']['content']))
        notionNameList.append(str(result['properties']['Name']['title'][0]['text']['content'].replace("\r", "").replace("\n", "")))
        notionGradeList.append(str(result['properties']['Points']['rich_text'][0]['text']['content']))
        # notionIDList.append(str(result['id']))

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
    actions.perform()
    WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID, "progress-btn"))).click()
    time.sleep(2)
    blackbaudName = ""
    while blackbaudName != className:
        #get all grade detail buttons
        gradeDetailButtons = driver.find_elements(By.XPATH, "//a[@class ='btn btn-default']")
        #click on each grade detail button
        for button in gradeDetailButtons:
            button.click()
            time.sleep(3)
            blackbaudName = driver.find_element(By.XPATH, "//h1[contains(@class,'bb-dialog-header media-heading')]").text
            print(blackbaudName)
            if(blackbaudName == className):
                break
            closeButton = driver.find_element(By.XPATH, "//a[contains(@class,'close fa fa-times')]")
            closeButton.click()

    #get name, grade, and notes
    nameList = driver.find_elements(By.XPATH, "//td[contains(@data-heading,'Assignment')]")
    for name in nameList:
        print(name.text)
        blackbaudNameList.append(name.text)
    gradeList = driver.find_elements(By.XPATH, "//td[contains(@data-heading,'Points')]")
    for grade in gradeList:
        print(grade.text)
        blackbaudGradeList.append(grade.text)
    notesList = driver.find_elements(By.XPATH, "//td[contains(@data-heading,'Notes')]")
    for notes in notesList:
        print(notes.text)
        blackbaudNotesList.append(notes.text)
    netGrade = driver.find_element(By.XPATH, "//div[contains(@class,'text-align-center')]//h1").text
    print(netGrade)
    
    #compare lists and update Notion
    for i in range(len(blackbaudNameList)):
        if(blackbaudNameList[i] not in notionNameList):
            print("New grade found: " + blackbaudNameList[i])
            newPage = notion.pages.create(
                parent={
                    "database_id": notionID
                },
                properties={
                    "Name": {
                        "title": [
                            {
                                "text": {
                                    "content": blackbaudNameList[i]
                                }
                            }
                        ]
                    },
                    "Points": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": blackbaudGradeList[i]
                                }
                            }
                        ]
                    },
                    "Notes": {
                        "rich_text": [
                            {
                                "text": {
                                    "content": blackbaudNotesList[i]
                                }
                            }
                        ]
                    }
                }
            )

    my_page = notion.databases.update(
    **{
        "database_id": notionID,
        "title": [
            {
                        "text": {
                            "content": className + " - " + netGrade
                        }
            }
        ]
                
            }

)

    print("done")
    driver.quit()
