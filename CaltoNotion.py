import html
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
    nameList.append((html.unescape(summary[2:int(len(str(summery)))-1])).strip())
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

#if name is the same as another name, add number to end
for i in range(len(editedNameList)):
    if editedNameList.count(editedNameList[len(editedNameList) - i - 1]) > 1:
        editedNameList[len(editedNameList) - i - 1] = editedNameList[len(editedNameList) - i - 1] + " " + str(editedNameList.count(editedNameList[len(editedNameList) - i - 1]))

# Read Notion data and save name field to list
def database_query_all(self, databaseID: str) -> dict:
    """Return the query of all the databases."""
    data = self.databases.query(databaseID)
    database_object = data['object']
    has_more = data['has_more']
    next_cursor = data['next_cursor']
    while has_more == True:
        data_while = self.databases.query(databaseID, start_cursor=next_cursor)
        for row in data_while['results']:
            data['results'].append(row)
        has_more = data_while['has_more']
        next_cursor = data_while['next_cursor']

    new_database = {
        "object": database_object,
        "results": data["results"],
        "next_cursor": next_cursor,
        "has_more": has_more
    }
    return new_database

retries2 = 1
success2 = False
while not success2:
    try:
        my_page = database_query_all(notion, "437cd227b8b946d485abdf2af1cbef3e").get("results")
        success2 = True
    except:
        wait2 = retries2 * 30
        print('Error! Waiting %s secs and re-trying...' % wait2)
        time.sleep(wait2)
        retries2 += 1


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