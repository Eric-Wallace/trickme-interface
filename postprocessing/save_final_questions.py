# File is used to parse logs and save the final questions
import csv
import pickle
import os
import time
import json
import random
from difflib import Differ
from pprint import pprint
from flask import Flask, request, jsonify
import requests
from datetime import datetime
import math
from badwords import checkBadWords

# Open files and sort based on file number
files = os.listdir('../interface/logs')
files.sort(key = lambda a: int(a.split("_")[1].split(".")[0]))

public_unique_questions = []
private_unique_questions = []
public_rewrite_questions = []
private_rewrite_questions = []

existing_questions = json.load(open('raw_question_text.json','r')) # all of the training, dev, and test questions in the Quiz Bowl dataset. Used to check duplicates

# This list contains fragments of questions that were flagged as invalid because the exact phrase was used in the existing dataset, but the question is actually valid (manually validated by Eric)
valid_list = ['and was written by Emile Zola', 'leaves Pencey Prep and roams New York City.', 'name this country which fought against the US', 'both based on whose 1865 assassination', 'who briefly ruled England in 1141', 'name this country where the Rococo style was developed after the reign of Louis XIV', 'name this order of mammals that lays eggs', 'Albert Einstein that has special and general', 'and which may consist of different', 'leaving features like the Grand Canyon', 'name this Central Asian tribe whose first Christian king', 'gesture with their fingers when performing blessings', 'posited everything was characterized by sunyata or emptiness','this Pillar of Islam that involves', 'superiority of republics to even the best monarchies', 'trait that led the devas to create this goddess']

def lookupEmail(myHash):
    submitted_emails = pickle.load(open("../interface/submitted_emails.pkl","rb"))
    for em, ha in submitted_emails:
        if ha == myHash:
            return em
    return myHash

# filters out invalid questions
# TODO, should make some code that checks for small diffs with training data instead of exact matches. Some near duplicates are slipping through. 
def filter(z, answer):
    # remove questions which are empty, too short, or have certain strings which I typed in when testing the interface.
    if (z == None or z == "" or z == " " and z.isspace() or 'a a a a a a a a a a' in z or 'dasdasdasdasdasdasdda' in z or 'markdasdadadchallenge' in z or len(z) < 100):
        return False
    if not checkBadWords(z):
        return False
    
    # for all the sentences in the question, check if it has a sentence fragment that is already present in the datatset, and if so, it is invalid. Except if the fragment is in valid_list.
    for sentence in existing_questions: 
        if sentence in z and len(sentence) > 15 and sentence != "1" and sentence != "-" and sentence != "." and sentence != "?" and sentence != "For 10 points," and sentence != '”.' and sentence != "on." and sentence != "A." and sentence != "a." and sentence != "I.":
             for valid in valid_list:
                 if valid in z:
                      return True                                                
             return False 

    return True

# Saves questions
count = 0
questions = []
answers = []

es_questions = []
es_answers = []
rnn_questions = []
rnn_answers = []

times = []
emails = []
categories = []
es_logs = []
rnn_logs = []
switchToRNN = True

for i in range(len(files)):
    with open('../interface/logs/' + files[i], 'rb') as question:
        q = pickle.load(question)
        submitted = False
        email = 'None'
        category = 'None'
        question = 'None'
        answer = 'None'
        time = 'None'
        for ID, element in q:
            # if ID == "EDIT":
            #     time, answer, question = element
            #     if answer == 'END':
            #        continue                
            #     questions.remove(' '.join(question.replace(u'\u200b', '').split()))
            #     answers.remove(answer.lower().replace("_"," "))                
            if ID == "BEGIN":
                _, email, _ = element
                email = lookupEmail(email)
            if ID == "CATEGORY":
                _, category, _ = element
            if ID == "SUBMIT":
                time, question, answer = element
        if filter(question, answer):
            if question not in questions: 
                count = count + 1
                questions.append(' '.join(question.replace(u'\u200b', '').split()))
                answers.append(answer.replace("_"," "))
                emails.append(email)
                categories.append(category)

                if time == "None":
                    times.append("None")
                else:
                    times.append(datetime.utcfromtimestamp(int(math.floor(float(time)))).strftime('%Y-%m-%d %H:%M:%S'))
                if switchToRNN:
                    es_questions.append(' '.join(question.replace(u'\u200b', '').split()))
                    es_answers.append(answer.replace("_"," "))
                else:
                    rnn_questions.append(' '.join(question.replace(u'\u200b', '').split()))
                    rnn_answers.append(answer.replace("_"," "))

            if "The flux of this compound into the atmosphere" in question:
                switchToRNN = False
            if switchToRNN:
                es_logs.append(q)
            else:
                rnn_logs.append(q)

# Dump all questions to different json and csv
print(count)
c = list(zip(questions, answers, emails, categories))
# random.shuffle(c)
questions, answers, emails, categories= zip(*c)
with open('final_adversarial_questions.json', 'w') as outfile:
    x = [{'question': question, 'answer': answer, 'email': email, 'category': category, 'time': time} for question, answer, email, category, time in zip(questions, answers, emails, categories, times)]
    json.dump(x, outfile)

outfile = csv.writer(open('final_adversarial_questions.csv', 'w'))
for question, answer, email, category, time in zip(questions, answers, emails, categories, times):
    outfile.writerow([question, answer, email, category, time])

# save ES questions
c = list(zip(es_questions, es_answers))
# random.shuffle(c)
es_questions, es_answers = zip(*c)
with open('es_final_adversarial_questions.json', 'w') as outfile:
    x = [{'question': question, 'answer': answer} for question, answer in zip(es_questions, es_answers)]
    json.dump(x, outfile)

# save RNN questions
c = list(zip(rnn_questions, rnn_answers))
# random.shuffle(c)
rnn_questions, rnn_answers = zip(*c)
with open('rnn_final_adversarial_questions.json', 'w') as outfile:
    x = [{'question': question, 'answer': answer} for question, answer in zip(rnn_questions, rnn_answers)]
    json.dump(x, outfile)


# This code prints the number of rewritten questions 

# rewritten_count = 0
# questions = []
# answers = []
# for i in range(len(files)):
#    with open('../interface/logs/' + files[i], 'rb') as question:
#        q = pickle.load(question)
#        submitted = False
#        rewrite = False
#        for ID, element in q:
#            if ID == "SUBMIT":
#                _, question, answer = element
#                if filter(question, answer):
#                    submitted = True
#            if ID == "REWRITE":
#                 _, rewrite_question, rewrite_answer = element                                
#                 if rewrite_question != "None":
#                     rewrite = True
#        if rewrite and submitted:
#            rewritten_count = rewritten_count + 1
# print("Number of Rewritten Questions", rewritten_count)    

# This code prints the number of private questions

# private_count = 0
# questions = []
# answers = []
# for i in range(len(files)):
#    with open('../interface/logs/' + files[i], 'rb') as question:
#        q = pickle.load(question)
#        flagger = False
#        for ID, element in q:
#             if ID == "PRIVATE":
#                 _, string_flagger, _ = element
#                 if string_flagger == 'true':
#                     flagger = True
#                 else:
#                     flagger = False
#             if ID == "SUBMIT" and flagger:
#                 t, question, answer = element            
#                 if filter(question, answer):                      
#                     if question not in questions:                         
#                         private_count = private_count + 1
#                         questions.append(' '.join(question.replace(u'\u200b', '').split()))
#                         answers.append(answer.replace("_"," "))                                                  
# print('Number of private questions', private_count)