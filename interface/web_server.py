#!flask/bin/python

# The main web app for the server side. Routes calls to answer questions, getting evidence. Also
# has a currently extremely ugly way of storing user information and doing highlighting.

from flask import Flask, render_template, request, redirect, Response, jsonify
import random, json
import subprocess
import requests
import wikipedia
import os
import pickle
import html
from collections import Counter
import logging
import nltk
from nltk.corpus import stopwords
import nltk.data
import hashlib

tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
hashGen = hashlib.sha512()
stop_words = set(stopwords.words('english')) 

log_list = {}
evidenceStore = {}
ID = {}

host='0.0.0.0'
port = 7000  # port 7000 is the web user, 5000 is QANTA, 8000 is the non-qanta server
debug = False 

submitted_answers = pickle.load(open('submitted_answers.pkl','rb'))
submitted_emails = pickle.load(open('submitted_emails.pkl','rb'))

app = Flask(__name__)

# All error messages are saved to message log
hdlr = logging.FileHandler('message.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
my_log = logging.getLogger(__name__)
my_log.setLevel(logging.INFO)
my_log.addHandler(hdlr)

# Launch app
@app.route('/')
def output():
    return render_template('server.html')

# load existing question if necessary and stores user information
@app.route('/begin', methods = ['POST'])
def begin():
    email = request.form['email']
    time = request.form['time']
    my_log.info("begin email: {}".format(email))
    if (email != "BEGIN_EMAIL"):        
        log_list[email] = []
        pickle.dump(log_list[email], open("log_list/" + email + ".pkl", 'wb'))
        evidenceStore[email] = {}
        evidenceStore[email]["evidence1"] = ""
        evidenceStore[email]["evidence2"] = ""
        evidenceStore[email]["evidence3"] = ""
        evidenceStore[email]["evidence4"] = ""
        pickle.dump(evidenceStore[email], open("evidenceStore/" + email + ".pkl",'wb'))    

        submitted_answers = pickle.load(open('submitted_answers.pkl','rb'))
        if email not in submitted_answers:
            submitted_answers[email] = []
            pickle.dump(submitted_answers, open("submitted_answers.pkl",'wb'))  
        log(email, "BEGIN", time, email, "None")            
    return "None"         
    
# log that they started over
@app.route('/servernewQuestion', methods = ['POST'])
def servernewQuestion():
    email = request.form['email']
    time = request.form['time']
    log(email, "NEWQUESTION", time, "None", "None")         
    dumpFiles(email)    
    return "None"

# log that they started over
@app.route('/edit', methods = ['POST'])
def edit():
    email = request.form['email']
    time = request.form['time']
    log(email, "EDIT", time, "END", "END")          
    dumpFiles(email)
    log(email,"BEGIN", time, email, "None")
    log(email, "EDIT", time, request.form['question'], request.form['answer'])          
    return "None"

# Grab existing question for the user to rewrite
@app.route('/rewrite', methods = ['POST'])
def rewrite():
    rewrite = request.form['rewrite']
    email_val = request.form['email']
    if (rewrite == 'true'):
        return_val = requests.post("http://0.0.0.0:8000/api/getQuestion").text
        rewrite = return_val.split("**")[0]
        id_val = return_val.split("**")[1]
        answer = return_val.split("**")[2].replace("_", " ")
        if email_val != "BEGIN_EMAIL":
            ID[email_val] = id_val
            time = request.form['time']
            log(email_val, "REWRITE", time, rewrite, answer)
        return rewrite + "**" + answer
    else:
        email_val = request.form['email']
        time = request.form['time']
        log(email_val, "REWRITE", time, "None", '-1')
        return "None"

# Saves users submission into logs
@app.route('/submit', methods = ['POST'])
def submit():
    email_val = request.form['email']
    private_data = request.form['private_data']
    log(email_val, "CATEGORY", request.form['time'], request.form['category'], "None")
    log(email_val, "PRIVATE", request.form['time'], private_data, "None")
    log(email_val, "SUBMIT", request.form['time'], request.form['text'], request.form['answer'])
 
    dumpFiles(email_val)
    return "finish"

# Get predictions from QANTA
@app.route('/predictES', methods = ['POST'])
def predictorES():
    # Get current predictions
    question = request.form['text']
    answer = request.form['answer']
    email_val = request.form['email']
    QANTA_guesses = requests.post("http://0.0.0.0:6000/api/interface_answer_question",  data={'text': question, 'answer': answer, 'bell': 'false'})
    # Convert returned value to list
    qanta_guesses_list = QANTA_guesses.json()
    doc_names = []
    doc_scores = []
    if(len(qanta_guesses_list['guess']) == 0):
        return "Empty"
    for i in range(len(qanta_guesses_list['guess'])):
        doc_names.append(qanta_guesses_list['guess'][i])
        doc_scores.append(round(float(qanta_guesses_list['score'][i]),2)) # 2 decimals
    
    # Get hyperlink to wikipedia for the page
    wikipedia_link = []
    for doc in doc_names:
        try:
            page = "https://en.wikipedia.org/wiki/" + doc.replace(" ","_")
        except:
            page = "https://www.wikipedia.org/"
        wikipedia_link.append(page)
    doc_names = "*".join(doc_names)
    doc_scores = "*".join(str(x) for x in doc_scores)
    wikipedia_links = "*".join(wikipedia_link)

    returnVal = doc_names + "**" + doc_scores + "**" + wikipedia_links + "**" + str(qanta_guesses_list['num'])
    log(email_val, "PREDICT_ES", request.form['time'], question, returnVal)
    return returnVal

# When QANTA answers your question correctly, figure our which position in the question to place the bell. Does so
# using binary search on the words. 
@app.route('/placeBell', methods = ['POST'])
def placeBell():
    # Get current predictions
    question = request.form['text']
    answer = request.form['answer']
    question = question.split(" ")
    
    # Binary search through the words to find the bell position
    last = len(question) - 1
    prev = first = 0
    while first<=last:
        midpoint = (first + last)//2
        firstHalfQuestion = question[0:midpoint+1]
        QANTA_guesses = requests.post("http://0.0.0.0:6000/api/interface_answer_question",  data={'text': ' '.join(firstHalfQuestion), 'answer': answer, 'bell': 'true'})
        if (QANTA_guesses.text == "Num0"):
            first = midpoint + 1
            continue
        qanta_guesses_list = QANTA_guesses.json()
        guess = qanta_guesses_list['guess'][0].replace("_"," ")
        if (guess.strip().lower() != answer.strip().lower()):
            first = midpoint + 1
        else:
            prev = midpoint + 1
            last = midpoint - 1     

    firstHalfQuestion = question[0:prev]
    joined_firstHalfQuestion = ' '.join(firstHalfQuestion)

    # find which sentence bell is in
    tk_sent = tokenizer.tokenize(joined_firstHalfQuestion)
    tk_sent = tk_sent[len(tk_sent)-1]
    firstHalfQuestion = firstHalfQuestion[-5:len(firstHalfQuestion)]
    return ' '.join(firstHalfQuestion) + "**" + str(len(tokenizer.tokenize(joined_firstHalfQuestion))) + "**" + tk_sent
    
# Implements the "past answers" box, searches for past QB questions based on answer using database
@app.route('/search', methods = ['POST'])
def searchor():
    question = request.form['text']
    query = request.form['query']   
    returnVal = requests.post("http://0.0.0.0:8000/api/search_answers", data={'text': question, 'query': query}).text
    email_val = request.form['email']
    log(email_val, "SEARCH", request.form['time'], question, returnVal)
    return returnVal

# This is some of the worst code of all time, if you want to change highlighting, probably
# contact Eric
# Implements highlighting functionality for the evidence box
@app.route('/highlight', methods = ['POST'])
def highlight():
    question = request.form['text']
    guessForEvidence = request.form['guessForEvidence']
    
    QANTA_answer = ""
    return_highlighted = []
    all_highlights = []
    sentence_index = []
    question_highlight_list = []
    source_indicator = []

    second_sentence_index = []
    second_question_highlight_list = []
    second_source_indicator = []
    second_return_highlighted = []

    third_sentence_index = []
    third_question_highlight_list = []  
    third_source_indicator = []
    third_return_highlighted = []

    fourth_sentence_index = []
    fourth_question_highlight_list = []
    fourth_source_indicator = []
    fourth_return_highlighted = []

    # itnrates over first 5 sentences
    rnn_returnVal = []
    for index, sentence in enumerate(tokenizer.tokenize(question)):
    #parsed = nlp(question)
    #for index, sentence in enumerate(parsed.sents):
        if index == 5:
            break
        #sentence = sentence.text   
        
        # gets higlights from qb
        response = requests.post("http://127.0.0.1:6000/api/interface_get_highlights", data={'text': sentence, 'guessForEvidence': guessForEvidence})
        if (response.text == "Num0"):
            return_highlighted.append("No evidence")
            question_highlight_list.append("null")
            sentence_index.append(str(index + 1))
            source_indicator.append(" ")
            second_return_highlighted.append("No evidence")
            second_question_highlight_list.append("null")
            second_sentence_index.append(str(index + 1))
            second_source_indicator.append(" ")
            third_return_highlighted.append("No evidence")
            third_question_highlight_list.append("null")
            third_sentence_index.append(str(index + 1))
            third_source_indicator.append(" ")
            fourth_return_highlighted.append("No evidence")
            fourth_question_highlight_list.append("null")
            fourth_sentence_index.append(str(index + 1))
            fourth_source_indicator.append(" ")
            continue
        try:
            text = response.json()
            QANTA_answer = text['guess'].replace("_"," ")
            if (len(text['wiki']) > 1):
                highlighted = [text['qb'][0], text['qb'][1], text['wiki'][0], text['wiki'][1]]
            else:
                highlighted = [text['qb'][0], text['qb'][1], text['wiki'][0], " "]
        except:
            return_highlighted.append("No evidence")
            question_highlight_list.append("null")
            sentence_index.append(str(index + 1))
            source_indicator.append(" ")
            second_return_highlighted.append("No evidence")
            second_question_highlight_list.append("null")
            second_sentence_index.append(str(index + 1))
            second_source_indicator.append(" ")
            third_return_highlighted.append("No evidence")
            third_question_highlight_list.append("null")
            third_sentence_index.append(str(index + 1))
            third_source_indicator.append(" ")
            fourth_return_highlighted.append("No evidence")
            fourth_question_highlight_list.append("null")
            fourth_sentence_index.append(str(index + 1))
            fourth_source_indicator.append(" ")

            continue
       
        rnn_returnVal.append(text['visual'])
        continue
        # removes stopwords from REST returned highlighted list
        highlighted = [h.replace("<em>","<mark>").replace("</em>","</mark>") for h in highlighted]
        for h_index, h in enumerate(highlighted):
            splitH = h.split(' ')
            for sH_i, j in enumerate(splitH):
                temp_j = j.replace("<mark>","").replace("</mark>","").lower()
                for char in ['.',',',';','?','!','\'','"','\n']:
                    temp_j = temp_j.replace(char, "")
                if temp_j in stop_words:
                    splitH[sH_i] = j.replace("<mark>","").replace("</mark>","")
            
            h = ' '.join(splitH)
            highlighted[h_index] = h
        # iterates through the four highlights given (2 qb, 2 wiki)
        # and selects the one with the most unigram matches with question sentence
        # also highlights the corresponding question sentence
        max_index = 0
        max_count = 0
        temp_all_highlights = []
        temp_aggregrate_question_highlist_list = []
        source = ""
        for inner_index, highlightedJoined in enumerate(highlighted):
            count = 0
            questionSplit = sentence.split(' ')         
            temp_question_highlight_list = []
            for word in highlightedJoined.split(' '):
                if '<mark>' in word:
                    word = word.split('<mark>')[1].split('</mark>')[0].lower()
                    for char in ['.',',',';','?','!','\'','"','\n']:
                        word = word.replace(char, "")   
                    for my_index, _ in enumerate(questionSplit):
                        temp = questionSplit[my_index].lower()
                        for char in ['.',',',';','?','!','\'','"','\n']:
                            temp = temp.replace(char, "")
                        if temp == word:
                            count = count + 1
                            temp_question_highlight_list.append(questionSplit[my_index])

            if len(temp_question_highlight_list) == 0:
                 temp_question_highlight_list = ["null"]
            temp_aggregrate_question_highlist_list.append(temp_question_highlight_list)

            if (count > max_count):
                max_count = count
                max_index = inner_index
                if inner_index == 0 or inner_index == 1:
                    source = "(Quiz Bowl)"
                else:
                    source = '(Wikipedia)'#'<i class="fab fa-wikipedia-w"></i>'

            if inner_index == 0 or inner_index == 1:
                temp_all_highlights.append((count, index + 1, highlightedJoined, temp_question_highlight_list, "(Quiz Bowl)"))
            elif inner_index == 2 or inner_index == 3:
                temp_all_highlights.append((count, index + 1, highlightedJoined, temp_question_highlight_list, '(Wikipedia)'))#'<i class="fab fa-wikipedia-w"></i>'))
            else:
                exit("Inner index was higher than 3", inner_index)

        #if max_count != 0:
        return_highlighted.append(highlighted[max_index])
        question_highlight_list.append(temp_aggregrate_question_highlist_list[max_index])
        sentence_index.append(str(index + 1))
        source_indicator.append(source)

        for i_ind, h_i in enumerate(highlighted):
            if h_i not in return_highlighted:
                if i_ind == 0 or i_ind == 1:
                    source = "(Quiz Bowl)"
                else:
                    source = "(Wikipedia)"
                if len(second_return_highlighted) < len(return_highlighted):
                    second_return_highlighted.append(h_i)
                    second_source_indicator.append(source)
                    second_sentence_index.append(str(index+1))
                    second_question_highlight_list.append(temp_aggregrate_question_highlist_list[i_ind])
                elif len(third_return_highlighted) < len(return_highlighted):
                    third_return_highlighted.append(h_i)
                    third_source_indicator.append(source)
                    third_sentence_index.append(str(index+1))
                    third_question_highlight_list.append(temp_aggregrate_question_highlist_list[i_ind])
                elif len(fourth_return_highlighted) < len(return_highlighted):
                    fourth_return_highlighted.append(h_i)
                    fourth_source_indicator.append(source)
                    fourth_sentence_index.append(str(index+1))
                    fourth_question_highlight_list.append(temp_aggregrate_question_highlist_list[i_ind])
                else:
                    exit("da fuck")
        
        all_highlights.extend(temp_all_highlights) 
   
    rnn_returnVal.append(" ")
    rnn_returnVal.append(" ") 
    rnn_returnVal.append(" ") 
    return QANTA_answer + "***" + '***'.join(rnn_returnVal)
    email_val = request.form['email']
      
    sentences_selected = []
    second_sentences_selected = []
    third_sentences_selected = []
    fourth_sentences_selected = [] 
    
    temp_sentences = tokenizer.tokenize(question)    
    for si in sentence_index:                
        sentences_selected.append(temp_sentences[int(si)-1])
        second_sentences_selected.append(temp_sentences[int(si)-1])
        third_sentences_selected.append(temp_sentences[int(si)-1])
        fourth_sentences_selected.append(temp_sentences[int(si)-1])

    while len(return_highlighted) < 5:
        return_highlighted.append(" ")
        sentences_selected.append(" ")
    while len(second_return_highlighted) < 5:
        second_return_highlighted.append(" ")
        second_sentences_selected.append(" ")
    while len(third_return_highlighted) < 5:
        third_return_highlighted.append(" ")
        third_sentences_selected.append(" ")
    while len(fourth_return_highlighted) < 5:
        fourth_return_highlighted.append(" ")
        fourth_sentences_selected.append(" ")

    first_question_highlight_set = set()
    second_question_highlight_set = set()
    third_question_highlight_set = set()
    fourth_question_highlight_set = set()
    for q_h_l_index, q_h_l in enumerate(question_highlight_list):
        for q_h_l_item in q_h_l:
            first_question_highlight_set.add(q_h_l_item)
    for q_h_l_index, q_h_l in enumerate(second_question_highlight_list):
        for q_h_l_item in q_h_l:
            second_question_highlight_set.add(q_h_l_item)
    for q_h_l_index, q_h_l in enumerate(third_question_highlight_list):
        for q_h_l_item in q_h_l:
            third_question_highlight_set.add(q_h_l_item)                    
    for q_h_l_index, q_h_l in enumerate(fourth_question_highlight_list):
        for q_h_l_item in q_h_l:
            fourth_question_highlight_set.add(q_h_l_item)

    first_question_highlight_set = list(first_question_highlight_set)
    second_question_highlight_set = list(second_question_highlight_set)
    third_question_highlight_set = list(third_question_highlight_set)
    fourth_question_highlight_set = list(fourth_question_highlight_set)

    first_question_highlight_set.extend(second_question_highlight_set)
    first_question_highlight_set.extend(third_question_highlight_set)
    first_question_highlight_set.extend(fourth_question_highlight_set)    
    counts = Counter(first_question_highlight_set)    

    for q_h_l_index, q_h_l in enumerate(question_highlight_list):
        for q_h_l_item_index, q_h_l_item in enumerate(q_h_l):
            if q_h_l_item in counts and len(q_h_l_item) > 1:
                new_str = q_h_l[q_h_l_item_index] + "__" + str(counts[q_h_l_item])
                q_h_l[q_h_l_item_index] = new_str
    for q_h_l_index, q_h_l in enumerate(second_question_highlight_list):
        for q_h_l_item_index, q_h_l_item in enumerate(q_h_l):
            if q_h_l_item in counts and len(q_h_l_item) > 1:
                new_str = q_h_l[q_h_l_item_index] + "__" + str(counts[q_h_l_item])
                q_h_l[q_h_l_item_index] = new_str
    for q_h_l_index, q_h_l in enumerate(third_question_highlight_list):
        for q_h_l_item_index, q_h_l_item in enumerate(q_h_l):
            if q_h_l_item in counts and len(q_h_l_item) > 1:
                new_str = q_h_l[q_h_l_item_index] + "__" + str(counts[q_h_l_item])
                q_h_l[q_h_l_item_index] = new_str

    for q_h_l_index, q_h_l in enumerate(fourth_question_highlight_list):    
        for q_h_l_item_index, q_h_l_item in enumerate(q_h_l):
            if q_h_l_item in counts and len(q_h_l_item) > 1:
                new_str = q_h_l[q_h_l_item_index] + "__" + str(counts[q_h_l_item])
                q_h_l[q_h_l_item_index] = new_str

    for q_h_l_index, q_h_l in enumerate(question_highlight_list):
        question_highlight_list[q_h_l_index] = "*".join(q_h_l)
    for q_h_l_index, q_h_l in enumerate(second_question_highlight_list):
        second_question_highlight_list[q_h_l_index] = "*".join(q_h_l)
    for q_h_l_index, q_h_l in enumerate(third_question_highlight_list):
        third_question_highlight_list[q_h_l_index] = "*".join(q_h_l)
    for q_h_l_index, q_h_l in enumerate(fourth_question_highlight_list):
        fourth_question_highlight_list[q_h_l_index] = "*".join(q_h_l)
    
    returnVal = QANTA_answer + "***" + "**".join(return_highlighted) + "***" + "**".join(sentences_selected) + "***" + "**".join(question_highlight_list) + "***" + "**".join(source_indicator) + "***" + "**".join(sentence_index)
    second_returnVal = QANTA_answer + "***" + "**".join(second_return_highlighted) + "***" + "**".join(second_sentences_selected) + "***" + "**".join(second_question_highlight_list) + "***" + "**".join(second_source_indicator) + "***" + "**".join(second_sentence_index)
    third_returnVal = QANTA_answer + "***" + "**".join(third_return_highlighted) + "***" + "**".join(third_sentences_selected) + "***" + "**".join(third_question_highlight_list) + "***" + "**".join(third_source_indicator) + "***" + "**".join(third_sentence_index)
    fourth_returnVal = QANTA_answer + "***" + "**".join(fourth_return_highlighted) + "***" + "**".join(fourth_sentences_selected) + "***" + "**".join(fourth_question_highlight_list) + "***" + "**".join(fourth_source_indicator) + "***" + "**".join(fourth_sentence_index)
    
    if (email_val != "BEGIN_EMAIL"):
        evidenceStore[email_val] = pickle.load(open("evidenceStore/" + email_val + ".pkl",'rb'))
        evidenceStore[email_val]["evidence1"] = returnVal
        evidenceStore[email_val]["evidence2"] = "None"#second_returnVal
        evidenceStore[email_val]["evidence3"] = "None"#third_returnVal
        evidenceStore[email_val]["evidence4"] = "None"#fourth_returnVal    
        pickle.dump(evidenceStore[email_val], open("evidenceStore/" + email_val + ".pkl",'wb'))    

    log(email_val, "HIGHLIGHT", request.form['time'], question, returnVal)
    return returnVal


# a backup method for storing submissions that just pickles the results
@app.route('/set_submitted', methods=['POST'])
def set_submitted():
    print(request.form['category'])
    email = request.form['email']
    editID = int(request.form['editID'])
    question_answer = request.form['question_answer']
    text = request.form['text'] 
    my_log.info(question_answer)
    my_log.info(text)
    submitted_answers = pickle.load(open('submitted_answers.pkl','rb'))
 
    if (editID != -1):
        submitted_answers[email][int(editID)] = question_answer
        submitted_answers[email][int(editID) + 1] = text
    else:
        submitted_answers[email].append(question_answer)
        submitted_answers[email].append(text)

    pickle.dump(submitted_answers, open("submitted_answers.pkl",'wb'))  
    return "TODO"   

# loads the past submitted questions of this user
@app.route('/load_submitted', methods=['POST'])
def load_submitted():
    email = request.form['email']

    try:
        submitted_answers = pickle.load(open('submitted_answers.pkl','rb'))
    except:
        return "undefined"

    if email in submitted_answers:
                if len(submitted_answers[email]) == 0:
                        return "undefined"
                return jsonify(submitted_answers[email])
    else:
        return "undefined"

# cycles the evidence pane and returns the new evidence
@app.route('/more_evidence', methods=['POST'])
def more_evidence():
    email = request.form['email']
    indicator = request.form['indicator']
    if indicator == "null":
        return "None"
    try:
        evidenceStore[email] = pickle.load(open("evidenceStore/" + email + ".pkl",'rb'))    
        returnVal = evidenceStore[email][indicator]     
        return returnVal
    except:         
        return "None"   

# takes the users email and password, hashes it, and sends it back
@app.route('/checkEmail', methods=['POST'])
def checkEmail():
    email = request.form['email']
    password = request.form['password']
    print(email)
    print(password)
    hashGen = hashlib.sha512()
    hashGen.update((email + password).encode('utf-8'))

    myHash = hashGen.hexdigest()

    submitted_emails = pickle.load(open("submitted_emails.pkl","rb"))
    foundMe = False
    for em, ha in submitted_emails:
        if ha == myHash:
            return 'true'
        elif email == em:
            foundMe = True
    if foundMe:
        return 'false'
    return 'true'

# takes the users email and password, hashes it, and sends it back
@app.route('/storeEmail', methods=['POST'])
def storeEmail():
    email = request.form['email']
    password = request.form['password']
    hashGen = hashlib.sha512()
    hashGen.update((email + password).encode('utf-8'))
    
    myHash = hashGen.hexdigest()
    submitted_emails = pickle.load(open("submitted_emails.pkl","rb"))
    submitted_emails.append((email,myHash))
    pickle.dump(submitted_emails, open("submitted_emails.pkl",'wb'))    
    return myHash

# logs messages into the corresponding list
def log(email, request_type, time, question, returnVal):    
    if (email != "BEGIN_EMAIL"):
        try:
            question = html.unescape(question)          
            question = question.replace(u'\xa0', u' ')
            log_list[email] = pickle.load(open("log_list/" + email + ".pkl","rb"))
            log_list[email].append((request_type, [time, question, returnVal]))
            pickle.dump(log_list[email], open("log_list/" + email + ".pkl", 'wb'))
        except:
            log_list[email] = []
            question = html.unescape(question)
            log_list[email].append((request_type, [time, question, returnVal]))            
            pickle.dump(log_list[email], open("log_list/" + email + ".pkl", 'wb'))
            evidenceStore[email] = {}
            evidenceStore[email]["evidence1"] = ""
            evidenceStore[email]["evidence2"] = ""
            evidenceStore[email]["evidence3"] = ""
            evidenceStore[email]["evidence4"] = ""        
            pickle.dump(evidenceStore[email], open("evidenceStore/" + email + ".pkl",'wb'))    

            submitted_answers = pickle.load(open('submitted_answers.pkl','rb'))
            if email not in submitted_answers:
                submitted_answers[email] = []
                pickle.dump(submitted_answers, open("submitted_answers.pkl",'wb'))
            # catches the error when the server is restarted but the user has cookies

    if debug and request_type != "SEARCH":
        print(email)
        print(request_type)
        print(time)
        print(question)
        print(returnVal)

# takes the log and dumps it
def dumpFiles(email_val):
    files = os.listdir('./logs')
    if (len(files) == 0):
        filename = "./logs/question_1.pickle"
    else:
        files = [int(f.split("_")[1].split(".")[0]) for f in files]
        last = max(files)
        filename = "./logs/question_" + str(last + 1) + ".pickle" 
    
    log_list[email_val] = pickle.load(open("log_list/" + email_val + ".pkl","rb"))
    pickle.dump(log_list[email_val], open(filename, "wb"))
    log_list[email_val] = []    
    pickle.dump(log_list[email_val], open("log_list/" + email_val + ".pkl", 'wb'))

# if there is an error, print it
@app.teardown_request
def log_errors(error):
    if error is None:
        return

    print("An error occurred while handling the request", error)

if __name__ == '__main__':
    app.run(host=host, port=port, debug=debug)