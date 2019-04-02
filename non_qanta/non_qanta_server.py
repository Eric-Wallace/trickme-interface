# Backend server that handles searching past questions
# and loading questions to rewrite
import itertools
import sqlite3
import os
import wikipedia
import json
from PyDictionary import PyDictionary
from nltk.corpus import wordnet
from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import pickle
import spacy
from nltk.corpus import stopwords as sw
from nltk.util import ngrams
from nltk.tokenize import word_tokenize
import random

app = Flask(__name__)
app.run(host='0.0.0.0', port=8000, debug=False)
dictionary = PyDictionary()

highlight_color = '#ecff6d'
highlight_prefix = '<span style="background-color: ' + highlight_color + '">'
highlight_suffix = '</span>'
highlight_template = highlight_prefix + '{}' + highlight_suffix

stop_words = set(sw.words('english'))
chars = ".,;?!\'"

with open('existing_questions.pickle', 'rb') as handle:
	existing_questions = pickle.load(handle)

# returns number of ngrams in common and a list of the common ngrams
def compareNGrams(ngrams1, ngrams2):
    common = 0
    highlight_list = []
    for grams1 in ngrams1:
       if grams1 in ngrams2:
         common = common + 1
         highlight_list.append(grams1)
    return common, highlight_list

def join_punctuation(seq, characters='.,;?!\''):
    characters = set(characters)
    seq = iter(seq)
    current = next(seq)

    for nxt in seq:
        if nxt in characters:
            current += nxt       
        elif nxt.find('<mark>') >= 0 and (nxt.split("<mark>")[1]).split('</mark>')[0] in characters:
            current += nxt
        else:
            yield current
            current = nxt

    yield current

# searches past questions for query and sorts the results by ngram overlap
def search_past_answers(query, questionText):
	n = 2 # use bigrams
	questionText = word_tokenize(questionText.lower())	
	ngrams1 = list(ngrams(questionText, n))

	query = query.split(" ") 
	query = '_'.join(query) #place _ in between spaces as database has it

	connection = sqlite3.connect('./data/non_naqt.db', check_same_thread=False)
	cursor = connection.cursor()
	# get id's of matching questions
	cursor.execute('SELECT id FROM questions WHERE page == ? COLLATE NOCASE',   # find question where answer is query, ignoring cases
		(query,)
		)
	questions = cursor.fetchall() # get all results
	if len(questions) == 0:
		return "No Matches"

	# get tournament info
	cursor.execute('SELECT tournament FROM questions WHERE page == ? COLLATE NOCASE',   # find question where answer is query, ignoring cases
		(query,)
		)
	tournaments = cursor.fetchall() # get all results
	tournaments = [t[0] for t in tournaments] # grab tourney name
	questions = [question[0] for question in questions] #turn from 1 element tuple to single
	result = []
	for index, question in enumerate(questions): 
		cursor.execute(
				"SELECT raw FROM text WHERE question = ? ",   # gather the raw text from the question
				(question,)
			)
		# turn the text into a list of sentences
		temp = cursor.fetchall()
		temp = [t[0] for t in temp]
		tokenized_sents = [word_tokenize(t) for t in temp]
		tokenized_sents = list(itertools.chain.from_iterable(tokenized_sents))  
		full_text = " ".join(tokenized_sents)

		ngrams2 = list(ngrams(full_text.lower().split(), n))
		count, highlight_list = compareNGrams(ngrams1, ngrams2)
		for index2, ngram in enumerate(highlight_list):  # add highlights html tags to all the ngrams
			(word1, word2) = ngram
			word1 = "<mark>" + word1
			word2 = word2 + "</mark>"			
			highlight_list[index2] = word1 + " " + word2

		result.append((full_text, tournaments[index], count, highlight_list))

	# sorts results based on number of ngram overlap
	cursor.close()
	result = sorted(result, key=lambda x: x[2])
	result.reverse()
	tournaments = []
	questions = []
	final_highlight_list = []

	# unhighlight all the stop words and punctuations characters
	for question, tournament, _, highlight_list in result:
		tournaments.append(tournament)
		temp1 = question.split(" ")
		temp2 = list(temp1)		
		for x in highlight_list:
			foo = (x.split("<mark>")[1]).split('</mark>')[0]
			for index, t in enumerate(temp1):
				if (index < len(temp1) - 1 and (temp1[index].lower() + " " + temp1[index+1].lower()) == foo.lower()):					
					if (temp1[index].lower() not in stop_words) and (temp1[index].lower() not in chars):					
						temp2[index] = "<mark data-entity=\"org\">" + temp1[index] + "</mark>"
					if (temp1[index+1].lower() not in stop_words) and (temp1[index+1].lower() not in chars): 
						temp2[index+1] = "<mark data-entity=\"org\">" + temp1[index+1] + "</mark>"


		questions.append(" ".join(join_punctuation(temp2)))
		final_highlight_list.append(highlight_list)
	return "**".join(tournaments) + "***" + "**".join(questions)
	
@app.route('/api/search_answers', methods=['POST'])
def answer_question():
	question = request.form['text']
	query = request.form['query']
	return search_past_answers(query, question)            

# Get a random past question, get QANTA's response and send it
@app.route('/api/getQuestion', methods = ['POST'])
def getQuestion():
	# get a new random question that QANTA gets correct
	while (True):
		index = random.randint(0,len(existing_questions)-1)  # rand index		
		rewrite, answer = existing_questions[index]
		answer = answer.replace("_"," ")
		QANTA_guesses = requests.post("http://0.0.0.0:5000/api/answer_question",  data={'text': rewrite, 'answer': answer, 'bell': 'false'})		
		if QANTA_guesses.text == "Num0":
			continue 
		qanta_guesses_list = QANTA_guesses.json()
		if not (len(qanta_guesses_list['guess']) == 0) and qanta_guesses_list['guess'][0] == answer:
			return rewrite + "**" + str(index) + "**" + answer

