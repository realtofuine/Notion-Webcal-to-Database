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
editedNameList = []
assignList = []
dueList = []
courseList = []
notionNameList = []
notionAssignList = []
notionDueList = []
notionIDList = []

nameList.clear()
editedNameList.clear()
assignList.clear()
dueList.clear()
courseList.clear()
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

# Create editedNameList to remove name prefix and courseList to add course name
for name in nameList:
    if("AP Physics C" in name):
            course = "AP Phy C"
            editedNameList.append(name[56:])
            print(course)
            courseList.append(course)
    elif("AP United States History" in name):
        course = "APUSH"
        editedNameList.append(name[30:])
        print(course)
        courseList.append(course)
    elif("Advanced Topics in Mathematics" in name):
        course = "AT"
        editedNameList.append(name[40:])
        print(course)
        courseList.append(course)
    elif("AP Chemistry" in name):
        course = "AP Chem"
        editedNameList.append(name[18:])
        print(course)
        courseList.append(course)
    elif("English 12 - Literature of War" in name):
        course = "Eng"
        editedNameList.append(name[47:])
        print(course)
        courseList.append(course)
    elif("AP Computer Science A" in name):
        course = "APCSA"
        editedNameList.append(name[27:])
        print(course)
        courseList.append(course)
    else:
        course = "Not Found"
        editedNameList.append(name)
        print(course)
        courseList.append(course)

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
        if editedNameList[j] == notionNameList[i]:
            print("Match found")
            print(editedNameList[j])
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

for i in range(len(editedNameList)):
    if editedNameList[i] not in notionNameList:
        print("New event found: " + editedNameList[i])

        newPage = notion.pages.create(
            parent={
                "database_id": "437cd227b8b946d485abdf2af1cbef3e"
            },
            properties={
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": editedNameList[i]
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
                        "name": courseList[i]
                    }
                }
            }
        )
    else:
        getmatchingindex(i)
        
        print("No new events found")

#Remove events from Notion if they are not in the calendar

for i in range(len(notionNameList)):
    if notionNameList[i] not in editedNameList:
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