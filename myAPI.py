#!/usr/bin/env python3

from datetime import datetime
from tempoapiclient import client
import json
import requests
from azubiheftAPI.azubiheft import AzubiheftAPI
from azubiheftAPI.WebUntis.webuntis import Webuntis
from azubiheftAPI.WebUntis.cache import Cache
import argparse

def valid_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        msg = "\n\n==== Invalid date! Needed dateformat: YYYY-MM-DD ===="
        raise argparse.ArgumentTypeError(msg)

parser = argparse.ArgumentParser(description='An API which pulls all the worklogs from Jira Tempo and and parses them into your Azubiheft')

parser.add_argument('-s', '--startDate', help='Pull all the worklogs beginning from the date specified by this switch (format: YYYY-MM-DD)', required=True, type=valid_date)
parser.add_argument('-e', '--endDate', default=datetime.today().strftime('%Y-%m-%d'), help='Set a Date where the API should stop pulling the worklogs and adding them to the Azubiheft (defaults to the current date if not specified)', type=valid_date)

args = parser.parse_args()

# check if the endDate comes after the startDate (when the given parameters are correct)
if args.startDate > args.endDate:
    print('endDate needs to be after the startDate')

with open('/home/lalwazny/.local/bin/azubiheftAPI/credentials.json') as file:
    data = json.load(file)

tempo = client.Tempo(
    auth_token=data['tempo']['token'],
    base_url="https://api.tempo.io/core/3"
)

worklogs = tempo.get_worklogs(
    dateFrom=args.startDate,
    dateTo=args.endDate,
    accountId=data['tempo']['account_id']
)

# Get login credentials from env file
username = data['webuntis']['name']
password = data['webuntis']['password']
server = data['webuntis']['server']
school = data['webuntis']['school']

def get_lessons(client, start, end):
    lessons = client.get_lessons(start, end)

    lesson_topic_dict = {}
    
    for year in lessons:
        for lesson in year:
            index_day = lesson["date"]

            if lesson_topic_dict.get(index_day) is None:
                lesson_topic_dict[index_day] = []

            lesson_topic_dict[index_day].append(client.get_lesson_topic(lesson))
    
    return lesson_topic_dict


def get_lesson_topics(client, date):
    start = format_date(args.startDate)
    end = format_date(args.endDate)
    
    topics = []

    for topic in get_lessons(client, start, end)[date]:
        topics.append(f"({topic['subjectLong']}) {topic['topic']}")
    
    topics = sorted(set(topics))
    topics = [topic + ' === ' for topic in topics]
    topics[-1] = topics[-1][:-5]

    return topics

def format_date(date):
    return int(date.strftime("%Y%m%d"))

# maybe pass a name of a function as a value which returns the worklog and art 
logs = {
    'FOODS6-55': ['Shopware-Project: Team daily', '1'],
    'FLAGBIT-3': ['Urlaub', '3'],
    'FLAGBIT-5': ['Arbeitsunfähig', '5']
}

if __name__ == '__main__':
    with requests.session() as session:
        api = AzubiheftAPI(session) #? make the session a property of the API which is being created internally
        api.login_user(data['azubiheft']['email'], data['azubiheft']['password'])
        
        client = Webuntis(username, password, server, school)
        client.login()

        for worklog in worklogs:
            worklogDate = worklog['startDate']
            worklogWeek = api.get_week_number(worklogDate)
            log = worklog['issue']['key']
            blub = logs.get(log, None)
            
            if blub is None:
                art = '1'

                if log == 'FLAGBIT-4':
                    date = int(worklogDate.replace('-', ''))
                    worklogDescription = get_lesson_topics(client, date)
                    art = '2'
                elif log[:6] == 'FOODS6':
                    worklogDescription = f'Shopware-Projekt: {worklog["description"]}'
                else: 
                    worklogDescription = worklog["description"]
            else:
                worklogDescription, art = blub[0], blub[1] if blub else None

            print(worklogDescription, art)
            # api.create_entry(worklogDate, worklogWeek, art, worklogDescription)
