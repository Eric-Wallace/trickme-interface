# File is used to parse logs and save the final questions

import pickle
import os
import time
import json
import random
from difflib import Differ
from pprint import pprint
from flask import Flask, request, jsonify
import requests

# Open files and sort based on file number
files = os.listdir('../adversarialQA/logs')
files.sort(key = lambda a: int(a.split("_")[1].split(".")[0]))

public_unique_questions = []
private_unique_questions = []
public_rewrite_questions = []
private_rewrite_questions = []

existing_questions = json.load(open('text.json','r')) # all of the training, dev, and test questions in the Quiz Bowl dataset

# This list contains fragments of questions that were flagged as invalid because the exact phrase was used in the existing dataset,
# but the question is actually valid (manually validated by Eric)
valid_list = ['and was written by Emile Zola', 'leaves Pencey Prep and roams New York City.', 'name this country which fought against the US', 'both based on whose 1865 assassination', 'who briefly ruled England in 1141', 'name this country where the Rococo style was developed after the reign of Louis XIV', 'name this order of mammals that lays eggs', 'Albert Einstein that has special and general', 'and which may consist of different', 'leaving features like the Grand Canyon', 'name this Central Asian tribe whose first Christian king', 'gesture with their fingers when performing blessings', 'posited everything was characterized by sunyata or emptiness','this Pillar of Islam that involves', 'superiority of republics to even the best monarchies', 'trait that led the devas to create this goddess']

# a big list of bad words
badWords = ['2g1c',
'2 girls 1 cup',
'acrotomophilia',
'anal',
'anilingus',
'anus',
'arsehole',
'ass',
'asshole',
'assmunch',
'auto erotic',
'autoerotic',
'babeland',
'baby batter',
'ball gag',
'ball gravy',
'ball kicking',
'ball licking',
'ball sack',
'ball sucking',
'bangbros',
'bareback',
'barely legal',
'barenaked',
'bastardo',
'bastinado',
'bbw',
'bdsm',
'beaver cleaver',
'beaver lips',
'bestiality',
'bi curious',
'big black',
'big breasts',
'big knockers',
'big tits',
'bimbos',
'birdlock',
'bitch',
'black cock',
'blonde action',
'blonde on blonde action',
'blow j',
'blow your l',
'blue waffle',
'blumpkin',
'bollocks',
'bondage',
'boner',
'boob',
'boobs',
'booty call',
'brown showers',
'brunette action',
'bukkake',
'bulldyke',
'bullet vibe',
'bung hole',
'bunghole',
'busty',
'butt',
'buttcheeks',
'butthole',
'camel toe',
'camgirl',
'camslut',
'camwhore',
'carpet muncher',
'carpetmuncher',
'chocolate rosebuds',
'circlejerk',
'cleveland steamer',
'clit',
'clitoris',
'clover clamps',
'clusterfuck',
'cock',
'cocks',
'coprolagnia',
'coprophilia',
'cornhole',
'cum',
'cumming',
'cunnilingus',
'cunt',
'darkie',
'date rape',
'daterape',
'deep throat',
'deepthroat',
'dick',
'dildo',
'dirty pillows',
'dirty sanchez',
'dog style',
'doggie style',
'doggiestyle',
'doggy style',
'doggystyle',
'dolcett',
'domination',
'dominatrix',
'dommes',
'donkey punch',
'double dong',
'double penetration',
'dp action',
'eat my ass',
'ecchi',
'ejaculation',
'erotic',
'erotism',
'escort',
'ethical slut',
'eunuch',
'faggot',
'fecal',
'felch',
'fellatio',
'feltch',
'female squirting',
'femdom',
'figging',
'fingering',
'fisting',
'foot fetish',
'footjob',
'frotting',
'fuck',
'fuck buttons',
'fudge packer',
'fudgepacker',
'futanari',
'g-spot',
'gang bang',
'gay sex',
'genitals',
'giant cock',
'girl on',
'girl on top',
'girls gone wild',
'goatcx',
'goatse',
'gokkun',
'golden shower',
'goo girl',
'goodpoop',
'goregasm',
'grope',
'group sex',
'guro',
'hand job',
'handjob',
'hard core',
'hardcore',
'hentai',
'honkey',
'hooker',
'hot chick',
'how to kill',
'how to murder',
'huge fat',
'humping',
'incest',
'intercourse',
'jack off',
'jail bait',
'jailbait',
'jerk off',
'jigaboo',
'jiggaboo',
'jiggerboo',
'jizz',
'juggs',
'kike',
'kinbaku',
'kinkster',
'kinky',
'knobbing',
'leather restraint',
'leather straight jacket',
'lemon party',
'lolita',
'lovemaking',
'make me come',
'male squirting',
'masturbate',
'menage a trois',
'milf',
'missionary position',
'motherfucker',
'mound of venus',
'mr hands',
'muff diver',
'muffdiving',
'nambla',
'nawashi',
'negro',
'neonazi',
'nig nog',
'nigga',
'nigger',
'nimphomania',
'nipple',
'nipples',
'nsfw images',
'nudity',
'nympho',
'nymphomania',
'octopussy',
'omorashi',
'one cup two girls',
'one guy one jar',
'orgasm',
'orgy',
'paedophile',
'panties',
'panty',
'pedobear',
'pedophile',
'pegging',
'phone sex',
'piece of shit',
'piss pig',
'pissing',
'pisspig',
'playboy',
'pleasure chest',
'pole smoker',
'ponyplay',
'poof',
'poop chute',
'poopchute',
'porn',
'porno',
'prince albert piercing',
'pthc',
'pubes',
'pussy',
'queaf',
'raghead',
'raging boner',
'raping',
'rapist',
'rectum',
'reverse cowgirl',
'rimjob',
'rimming',
'rosy palm',
'rosy palm and her 5 sisters',
'rusty trombone',
's&m',
'sadism',
'scat',
'schlong',
'scissoring',
'semen',
'sexo',
'sexy',
'shaved beaver',
'shaved pussy',
'shemale',
'shibari',
'shota',
'shrimping',
'slanteye',
'slut',
'smut',
'snatch',
'snowballing',
'sodomize',
'sodomy',
'spic',
'spooge',
'spread legs',
'strap on',
'strapon',
'strappado',
'strip club',
'style doggy',
'suck',
'sucks',
'suicide girls',
'sultry women',
'swastika',
'swinger',
'tainted love',
'taste my',
'tea bagging',
'threesome',
'throating',
'tied up',
'tight white',
'tit',
'tits',
'titties',
'titty',
'tongue in a',
'topless',
'tosser',
'towelhead',
'tranny',
'tribadism',
'tub girl',
'tubgirl',
'tushy',
'twat',
'twink',
'twinkie',
'two girls one cup',
'undressing',
'upskirt',
'urethra play',
'urophilia',
'venus mound',
'vibrator',
'violet blue',
'violet wand',
'vorarephilia',
'voyeur',
'vulva',
'wank',
'wet dream',
'wetback',
'white power',
'women rapping',
'wrapping men',
'wrinkled starfish',
'xx',
'xxx',
'yaoi',
'yellow showers',
'yiffy',
'zoophilia',
'{margin:']

# filters out invalid questions
# TODO, should make some code that checks for small diffs with training data instead of exact matches. 
def filter(z, answer):
    # empty, too short, the exact string are stuff I typed in when testing
    if (z == None or z == "" or z == " " and z.isspace() or 'a a a a a a a a a a' in z or 'dasdasdasdasdasdasdda' in z or 'markdasdadadchallenge' in z or len(z) < 100):
        return False
    for i in z.split(" "):   # if contains a bad word, its invalid
        if i in badWords:            
            return False    
    for sentence in existing_questions: # for all the sentences in the question, check if it has a sentence fragment that is already present in the datatset, and if so, it is invalid. Except if the fragment is in valid_list, then its fine
        if sentence in z and len(sentence) > 15 and sentence != "1" and sentence != "-" and sentence != "." and sentence != "?" and sentence != "For 10 points," and sentence != '”.' and sentence != "on." and sentence != "A." and sentence != "a." and sentence != "I.":
             for valid in valid_list:
                 if valid in z:
                      return True                                                
             return False 

    return True

# This code prints the number of rewritten questions 
count = 0
questions = []
answers = []
for i in range(len(files)):
    with open('../adversarialQA/logs/' + files[i], 'rb') as question:
        q = pickle.load(question)
        submitted = False
        rewrite = False
        for ID, element in q:
            if ID == "SUBMIT":
                _, question, answer = element
                if filter(question, answer):
                    submitted = True
            if ID == "REWRITE":
                 _, rewrite_question, rewrite_answer = element                                
                 if rewrite_question != "None":
                     rewrite = True
        if rewrite and submitted:
            count = count + 1
print("Number of Rewritten Questions", count)

# Prints the number of private questions
count = 0
questions = []
answers = []
for i in range(len(files)):
    with open('../adversarialQA/logs/' + files[i], 'rb') as question:
        q = pickle.load(question)
        flagger = False
        for ID, element in q:
             if ID == "PRIVATE":
                 _, string_flagger, _ = element
                 if string_flagger == 'true':
                     flagger = True
                 else:
                     flagger = False
             if ID == "SUBMIT" and flagger:
                 t, question, answer = element            
                 if filter(question, answer):                      
                     if question not in questions:                         
                         count = count + 1
                         questions.append(' '.join(question.replace(u'\u200b', '').split()))
                         answers.append(answer.replace("_"," "))                                                  
print('Number of private questions', count)

# prints questions
#for question, answer in zip(questions, answers):
#    print(question)
#    print(answer)


# dumps questions to a json format
c = list(zip(questions, answers))
random.shuffle(c)
questions, answers = zip(*c)
with open('final_adversarial_questions.json', 'w') as outfile:
    x = [{'question': question, 'answer': answer} for question, answer in zip(questions, answers)]
    json.dump(x, outfile)


# Deprecated code to do some more fine-grained analysis
# for i in range(len(files)):
#     if i < len(files) - 100:
#         continue
#     with open('../adversarialQA/logs/' + files[i], 'rb') as question:
#         q = pickle.load(question)
#         q.reverse()
#         print(q) 
#         x = input("next")
#         ID, element  = q[len(q)-1]
#         if ID == "BEGIN":
#             t, email, _ = element
#         #if (email != "jordanbg@gmail.com"):
#         #    continue
#         #if (email == "eswallace@comcast.net"):
#         #    continue
#         private = False
#         ID, element = q[0]
#         if ID == "SUBMIT":                
#             t, question, answer = element               
#             t = int(float(t))
#             t = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t))
                    
#             print(question) ###
#             print(answer)   ###
#             print(t)
#             continue 
#         else:
#             print(q)  ###
#             continue ###
#             if len(q) == 1:
#                  continue
#             ID, element = q[1]
#             if ID == "PRIVATE":
#                 _, val, _ = element
#                 if val == "true":
#                     private = True                     
#             else:
#                 print("Private was not there")
#                 continue  
#         if ID == "EDIT":
#             #print("IT ENDED WITH AN EDIT OMG")            
#             continue
#         if ID == "NEWQUESTION":
#             #print("IT ENDED WITH A NEW QUESTION OMG")                        
#             continue
#         ID, element  = q[len(q)-3]
#         if ID == "REWRITE":
#             _, rewrite_question, rewrite_answer = element                                
#             if rewrite_question == "None":
#                 print("Double log non-rewrite")
#             else:   
#                 if private:
#                     private_rewrite_questions.append((question,answer,rewrite_question,rewrite_answer))
#                     if question == rewrite_question:
#                             print("They didn't change anything in the rewrite, probably delete these")
#                 else:
#                     public_rewrite_questions.append((question,answer,rewrite_question,rewrite_answer))
#                     if question == rewrite_question:
#                             print("They didn't change anything in the rewrite, probably delete these")
#         else:
#             ID, element  = q[len(q)-2]
#             if ID == "REWRITE":
#                 _, rewrite_question, rewrite_answer = element                                          
#                 if rewrite_question == "None":
#                     if private:
#                         private_unique_questions.append((question,answer))
#                     else:
#                         public_unique_questions.append((question,answer))
#                 else:            
#                     if private:
#                         private_rewrite_questions.append((question,answer, rewrite_question, rewrite_answer))
#                         if question == rewrite_question:
#                             print("They didn't change anything in the rewrite, probably delete these")
#                     else:
#                         public_rewrite_questions.append((question,answer, rewrite_question, rewrite_answer))                    
#                         if question == rewrite_question:
#                             print("They didn't change anything in the rewrite, probably delete these")
            
#             if ID == "EDIT":
#                 print("IT WAS AN EDIT, NEED TO REMOVE SOME")                            

#         ID, element  = q[len(q)-1]
#         if ID == "BEGIN":
#             t, email, _ = element               

#         if ID == "REWRITE":
#             #print("REWRITE but no BEGIN")
#             _, rewrite_question, rewrite_answer = element
#             if rewrite_question == "None":
#                 if private:
#                     private_unique_questions.append((question,answer))
#                 else:
#                     public_unique_questions.append((question,answer))
#             else:
#                 if private:
#                     private_rewrite_questions.append((question,answer, rewrite_question, rewrite_answer))
#                     if question == rewrite_question:
#                         print("They didn't change anything in the rewrite, probably delete these")
#                 else:
#                     public_rewrite_questions.append((question,answer, rewrite_question, rewrite_answer))
#                     if question == rewrite_question:
#                         print("They didn't change anything in the rewrite, probably delete these")
 
# # for question,answer in public_unique_questions:
# #     print(question)
# #     print(answer)
# #     print()
# #     print()

# d = Differ()
# for question,answer,orig_question,orig_answer in public_rewrite_questions:
#    #print(question)
#    #print(answer)
#    #print(orig_question)
#    #print(orig_answer)
#    text1 = question.splitlines(1)
#    text2 = orig_question.splitlines(1)
#    pprint(list(d.compare(text1, text2)))
#    #print(difflib.SequenceMatcher(None, question, orig_question))

# #print(public_unique_questions)
# #print(public_rewrite_questions)
# #print(private_unique_questions)
# #print(private_rewrite_questions)
