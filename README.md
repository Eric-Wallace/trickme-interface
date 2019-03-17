# Trick Me If You Can: Adversarial Writing of Trivia Challenge Questions

Official code for the interface in ```Trick Me If You Can: Adversarial Writing of Trivia Challenge Questions```, [preprint](https://arxiv.org/abs/1809.02701) and early version at 2018 ACL Student Research Workshop.

This is an interactive user interface for creating question-answer pairs that are difficult (adversarial) for computers to answer. The goal is for users to either write unique questions, or to reformulate existing questions, such that they adversarially break a question answering system. The underlying computer system is based on [QANTA](https://github.com/Pinafore/qb), a deep-learning Question Answering system. The interface can be naturally extended to other NLP tasks.

See the [competition site](https://sites.google.com/view/qanta/home) for more information on our Question Answering competition, and [our paper](https://arxiv.org/abs/1809.02701) for more information on the project. 

## Running The Interface

I recommend using ```screen``` to launch everything, so you don't need a bunch of terminals.

To run the server with multiple workers, go the the folder ```/interface```, and run using gunicorn (this command launches 4 parallel workers):  ```gunicorn --bind 0.0.0.0:7000 web_server:app --workers 4``` 

Then launch the non_qanta server, inside ```/non_qanta``` run ```python server.py```.  

Then you need to launch QANTA. 

I use the following code to launch the RNN guesser.

```
import qanta.guesser.rnn 
RnnGuesserLocal = qanta.guesser.rnn.RnnGuesser.load('output/guesser/7')
RnnGuesserLocal.web_api()
```


## Project Structure

There are three main pieces of code that run the service. Each one is described below. There is additional parsing and postprocessing code described at the end.

import qanta.guesser.rnn
RnnGuesserLocal = qanta.guesser.rnn.RnnGuesser.load('output/guesser/7')
RnnGuesserLocal.web_api()

## Main Interface

This is where most of the magic happens, ```/interface```.

* The main server is in ```web_server.py```
* The main HTML code is in ```templates/server.html```.
* ```static``` contains the javascript functions and css files. ```static/js/scripts.js``` is the file that does most of the interfaces functionality
* ```static/answers.json``` contains all of the possible answers that are system can guess on (extracted from the training data portion of the Quiz Bowl data).
* ```logs```, ```log_list```, ```evidenceStore``` are all folders that store logs about the user's actions and submitted questions. This will be phased out in place of a database.

## Non-QANTA Server

The Non-QANTA server ```/non_qanta``` handles certain backend functionality that doesn't involve answering questions or calculating evidence. Originally it did more computation, and it was separated out to put computationally expensive things on a different machine. It can probably be merged into the Main Interface at some point.

Non-QANTA hosts two REST endpoints that the main interface uses. ```get_question``` and ```search_answers```. ```get_question``` gets a question from the development set to be rewritten by the user. ```search_answers``` searches all past questions (from the Quiz Bowl dataset) and returns the top ones based on n-gram overlap with your question. This fills the past evidence box in the interface.

## QANTA

QANTA is used for answering questions and generating the evidence that is highlighted in the interface. For simplicity, we used the ElasticSearch system for answering questions in QANTA.  

QANTA hosts two REST endpoints that the main interface uses. ```get_highlights``` and ```answer_question```. To get QANTA up and running, see that [repository](https://github.com/Pinafore/qb). The code to run the correct QANTA services is part of the web app API code. 

## Parse Logs and Postprocessing

All of the postprocessing from the submitted questions happens in ```/postprocessing```. Use ```extract_raw_question_text.py''' to save all the text of the existing questions. Then run ```save_final_questions.py'''.


## Contact
This code is maintained by Eric Wallace. Feel free to open bug report or pull requests. For contact, find my email on [my website](http://www.ericswallace.com).


### Post Processing of Data
* I added filters for vulgar words, which accidently caught 
some words like Rape. Make sure this isn't happening for real questions (not spam)
* Some of the questions are very close to duplicates. For example, they changed
"10 points" to "ten points". See if you can filter these out (probably check n-gram
similarity and then filter out by hand)
* Make all the questions say "For 10 points" or whatever is said in the Quiz Bowl data. I think
Pedro has tried to be consistent about this (he might have scripts already for this). i.e. "for the points" -> "for 10 points" or "ftp" -> "for 10 points"
* Make sure not to show any questions that are labeled as "private"


### Weird Things To Note
* references to ```email``` in JS is not the email, but rather is a hash
* Everything uses ```*``` or ```**``` for delimiting between different fields. JSON should be used instead =( 
* The highlighting functionality is an absolute mess. Think you should contact me if you want to change that
* editID is -1 when your not editing. Set when you are.
