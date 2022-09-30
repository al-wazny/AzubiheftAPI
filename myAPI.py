#!/usr/bin/env python3

from datetime import datetime
from tempoapiclient import client
import json
from azubiheftAPI.azubiheft import AzubiheftAPI
from azubiheftAPI.WebUntis.webuntis import Webuntis
import argparse

# Is being used to check if the user typed in a valid date (format and if the date even exists)
def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        msg = "\n\n==== Invalid date! Needed dateformat: YYYY-MM-DD ===="
        raise argparse.ArgumentTypeError(msg)

parser = argparse.ArgumentParser(description='An API which pulls all the worklogs from Jira Tempo and and parses them into your Azubiheft')

# create the arguments for the cli tool that can be passed as parameters
parser.add_argument('-s', '--startDate', help='Pull all the worklogs beginning from the date specified by this switch (format: YYYY-MM-DD)', required=True, type=valid_date)
parser.add_argument('-e', '--endDate', default=datetime.today().strftime('%Y-%m-%d'), help='Set a Date where the API should stop pulling the worklogs and adding them to the Azubiheft (defaults to the current date if not specified)', type=valid_date)

# take in the user input
args = parser.parse_args()

# check if the endDate comes after the startDate (when the given parameters are correct)
if args.startDate > args.endDate:
    print('endDate needs to be after the startDate')

# Get login credentials from credentials file
with open('/home/lalwazny/.local/bin/azubiheftAPI/credentials.json') as file:
    data = json.load(file)

# log into tempo
tempo = client.Tempo(
    auth_token=data['tempo']['token'],
    base_url="https://api.tempo.io/core/3"
)

# pull all the needed worklogs from tempo
worklogs = tempo.get_worklogs(
    dateFrom=args.startDate,
    dateTo=args.endDate,
    accountId=data['tempo']['account_id']
)

username = data['webuntis']['name']
password = data['webuntis']['password']
server = data['webuntis']['server']
school = data['webuntis']['school']

# pull all the lessons between two dates
def get_lessons(client, start, end):
    lessons = client.get_lessons(start, end)

    lesson_topic_dict = {}
    
    for lesson in lessons[0]:
        index_day = lesson["date"]

        if lesson_topic_dict.get(index_day) is None:
            lesson_topic_dict[index_day] = []

        lesson_topic_dict[index_day].append(client.get_lesson_topic(lesson))
    
    return lesson_topic_dict

# format the topic in such a way to use it for the entry in azubiheft
def format_lesson_topics(topics):
    topics = [topic + ' === ' for topic in set(topics)]
    topics[-1] = topics[-1][:-5]

    return topics

# pull the topic of each lesson and format them
def get_lesson_topics(client, date):
    start = format_date(args.startDate)
    end = format_date(args.endDate)
    
    topics = []

    for topic in get_lessons(client, start, end)[date]:
        topics.append(f"({topic['subjectLong']}) {topic['topic']}")
    
    return format_lesson_topics(topics), '2'

# remove the hyphen and cast the date into an integer to satisfy the key format for the lesson topics 
def format_date(date):
    return int(date.strftime("%Y%m%d"))

# maybe pass a name of a function as a value which returns the worklog and art 
logs = {
    'FOODS6-55': ['Shopware-Project: Team daily', '1'],
    'FLAGBIT-3': ['Urlaub', '3'],
    'FLAGBIT-4': locals()['get_lesson_topics'],
    'FLAGBIT-5': ['Arbeitsunfähig', '5']
}

# return a static description if the worklog doesn't have a description is it's type is unknown (not in the dictionary)
def get_unkown_ticket_desciption(issue, worklog):
    if issue[:6] == 'FOODS6':
        worklogDescription = f'Shopware-Projekt: {worklog["description"]}'
    else:
        worklogDescription = worklog["description"]

    return worklogDescription, '1'

# format the text for the entry depending on the type of the worklog
def get_entry(client, worklog):
    date = int(worklog['startDate'].replace('-', ''))
    issue = worklog['issue']['key']
    ticket = logs.get(issue, None)

    if callable(ticket):
        return ticket(client, date)
    elif ticket is None:
        return get_unkown_ticket_desciption(issue, worklog)
    else:
        return ticket[0], ticket[1]

if __name__ == '__main__':
    # connect to azubiheft to create the entrys later on
    azubiheft = AzubiheftAPI()
    azubiheft.login(data['azubiheft']['email'], data['azubiheft']['password'])
    
    # connect to webuntis to pull the lesson topics
    webuntisClient = Webuntis(username, password, server, school)
    webuntisClient.login()

    for worklog in worklogs:
        worklogDescription, art = get_entry(webuntisClient, worklog)
        worklogDate = worklog['startDate']
        
        azubiheft.create_entry(worklogDate, worklogDescription, art)
    
    webuntisClient.logout()