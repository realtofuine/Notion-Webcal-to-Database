import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import urlopen

import pytz
from icalendar import Calendar, Event, vCalAddress, vText
from notion_client import Client

webcal = os.environ["WEB_CAL"]

notion = Client(auth=os.environ["NOTION_TOKEN"])

nameList = []
assignList = []
dueList = []
notionNameList = []
notionAssignList = []
notionDueList = []
notionIDList = []

nameList.clear()
assignList.clear()
dueList.clear()
notionNameList.clear()
notionAssignList.clear()
notionDueList.clear()
notionIDList.clear()

# Read calendar data and save to lists

data = urlopen(webcal).read()

cal = Calendar.from_ical(data)

for event in cal.walk('vevent'):

    datestart = event.decoded('dtstart')
    dateend = event.decoded('dtend')
    summery = event.decoded('summary')
    summary = str(summery)
    print(str(datestart))
    print(str(dateend))
    print(summary[2:int(len(str(summery)))-1])
    nameList.append(summary[2:int(len(str(summery)))-1])
    assignList.append(str(datestart))
    if isinstance(dateend, datetime): #If dateend is a datetime object keep the time
        dueList.append(str((dateend)))
    else: #If dateend is a date object, convert to datetime and subtract one day (there is an offset for some reason)
        dueList.append(str((dateend - timedelta(days = 1))))

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
    notionAssignList.append(str(result['properties']['Assign']['date']['start']))
    notionDueList.append(str(result['properties']['Due']['date']['start']))
    notionIDList.append(str(result['id']))

# If event is in both lists, compare dates and update Notion if necessary
def getmatchingindex(j):
    for i in range(len(notionNameList)):
        if nameList[j] == notionNameList[i]:
            print("Match found")
            print(nameList[j])
            print(notionNameList[i])
            print(assignList[j])
            print(notionAssignList[i])
            print(dueList[j])
            print(notionDueList[i])
            if assignList[j] != notionAssignList[i]:
                print("Assign date changed")
                notion.pages.update(
                    page_id = notionIDList[i],
                    properties={
                        "Assign": {
                            "date": {
                                "start": assignList[j]
                            }
                        }
                    }
                )
            if dueList[j] != notionDueList[i]:
                print("Due date changed")
                notion.pages.update(
                    page_id = notionIDList[i],
                    properties={
                        "Due": {
                            "date": {
                                "start": dueList[j]
                            }
                        }
                    }
                )

# Compare lists and add new events to Notion

for i in range(len(nameList)):
    if nameList[i] not in notionNameList:
        print("New event found: " + nameList[i])
        if("AP Physics C" in nameList[i]):
            course = "AP Phy C"
            print(course)
        elif("AP United States History" in nameList[i]):
            course = "APUSH"
            print(course)
        elif("Advanced Topics in Mathematics" in nameList[i]):
            course = "AT"
            print(course)
        elif("AP Chemistry" in nameList[i]):
            course = "AP Chem"
            print(course)
        elif("English 12" in nameList[i]):
            course = "Eng"
            print(course)
        elif("AP Computer Science A" in nameList[i]):
            course = "APCSA"
            print(course)
        else:
            course = "None"
            print(course)

        newPage = notion.pages.create(
            parent={
                "database_id": "437cd227b8b946d485abdf2af1cbef3e"
            },
            properties={
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": nameList[i]
                            }
                        }
                    ]
                },
                "Assign": {
                    "date": {
                        "start": assignList[i]
                    }
                },
                "Due": {
                    "date": {
                        "start": dueList[i]
                    }
                },
                "Class": {
                    "select": {
                        "name": course
                    }
                }
            }
        )
    else:
        getmatchingindex(i)
        
        print("No new events found")

#Remove events from Notion if they are not in the calendar

for i in range(len(notionNameList)):
    if notionNameList[i] not in nameList:
        # Check if item has checkbox checked
        if notion.pages.retrieve(page_id = notionIDList[i])['properties']['Manually Added']['checkbox'] == True:
            print("Canceled removing")
        else:
            print("Event removed: " + notionNameList[i])
            notion.pages.update(
                page_id = notionIDList[i],
                archived = True
            )
    else:
        print("No events removed")
