#!/usr/bin/env python3

from datetime import datetime
from tempoapiclient import client
import json
import requests
from azubiheftAPI.azubiheft import AzubiheftAPI
from azubiheftAPI.WebUntis.webuntis import Webuntis
from azubiheftAPI.WebUntis.cache import Cache
import argparse

with open('/home/lalwazny/.local/bin/azubiheftAPI/credentials.json') as file:
    data = json.load(file)

tempo = client.Tempo(
    auth_token=data['tempo']['token'],
    base_url="https://api.tempo.io/core/3"
)

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

def get_topics(start, end):
    client = Webuntis(username, password, server, school)

    client.login()

    lessons = client.get_all_lessons(start, end)

    lesson_topic_dict = {}
    
    for year in lessons:
        for lesson in year:
            index_day = lesson["date"]

            if lesson_topic_dict.get(index_day) is None:
                lesson_topic_dict[index_day] = []

            lesson_topic_dict[index_day].append(client.get_lesson_topic(lesson))
    
    client.logout()
    
    return lesson_topic_dict

if __name__ == '__main__':
    with requests.session() as session:
        api = AzubiheftAPI(session)
        api.login_user(data['azubiheft']['email'], data['azubiheft']['password'])

        for worklog in worklogs:
            worklogDate = worklog['startDate']
            worklogWeek = api.get_week_number(worklogDate)
            art = '1'
            log = worklog['issue']['key']
            
            if log == 'FOODS6-55':
                worklogDescription = 'Shopware-Project: Team daily'
            elif log == 'FLAGBIT-3':
                worklogDescription = 'Urlaub'
                art = '3'
            elif log == 'FLAGBIT-5':
                worklogDescription = 'Arbeitsunfähig'
                art = '5'
            elif log == 'FLAGBIT-4':
                date = int(worklogDate.replace('-', ''))
                
                # TODO modify this date object so you can use it as a parameter 
                start = int(args.startDate.splite('-'))
                end = int(args.endDate.replace('-', ''))
                
                
                topics = []
                for topic in get_topics(start, end)[date]:
                    topics.append(f"({topic['subjectLong']}) {topic['topic']}")
                topics = [topic + ' === ' for topic in topics]
                topics = sorted(set(topics))
                topics[-1] = topics[-1][:-5]
                worklogDescription = topics
                art = '2'
            else:
                worklogDescription = f'Shopware-Projekt: {worklog["description"]}'

            print(worklogDescription)
            # api.create_entry(worklogDate, worklogWeek, art, worklogDescription)
