# Trick Me If You Can: Adversarial Writing of Trivia Challenge Questions

Official code for the interface in the [TACL 2019 paper](https://arxiv.org/abs/1809.02701) ```Trick Me If You Can: Human-in-the-loop Generation of Adversarial Question Answering Examples```.

This is an interactive user interface for creating question-answer pairs that are difficult (adversarial) for computers to answer. The goal is for users to either write unique questions, or to reformulate existing questions, such that they adversarially break a question answering system. The underlying computer QA system is based on [QANTA](https://github.com/Pinafore/qb). The interface can be naturally extended to other NLP tasks.

![Interface Figure](trickme-interface/README_image.png)

See the [competition site](https://sites.google.com/view/qanta/home) for more information on our Question Answering competition, and [our paper](https://arxiv.org/abs/1809.02701) for more information on the project. 

## Running The Interface

1. I recommend using `screen`/`tmux` to launch the various servers, that way you do not need numerous terminals.
2. Run `mkdir interface/evidenceStore interface/logs, interface/log_list`
3. To run the server with multiple workers, go the the folder ```/interface```, and run using gunicorn (this command launches 4 parallel workers):  ```gunicorn --bind 0.0.0.0:7000 web_server:app --workers 4``` 
4. And download the `qanta.2018.04.18.sqlite3` from [QANTA](https://github.com/Pinafore/qb)
5. Then launch the non_qanta server, inside ```/non_qanta``` run ```python server.py```.

Then you need to launch QANTA. I use the following code to launch the RNN guesser. If you don't have a trained model you can use our docker container instead by running `docker TODO`
```
import qanta.guesser.rnn 
RnnGuesserLocal = qanta.guesser.rnn.RnnGuesser.load('output/guesser/qanta.guesser.rnn.RnnGuesser/7')
RnnGuesserLocal.web_api(port=6000)
```

Navigate to `localhost:7000` and the interface should be running.


## Project Structure

There are three main pieces of code that run the service. Each one is described below. There is additional parsing and postprocessing code described at the end.

## Main Interface

This is where most of the magic happens, ```/interface```.

* The main server is in ```web_server.py```
* The main HTML code is in ```templates/server.html```.
* ```static``` contains the javascript functions and css files. ```static/js/scripts.js``` is the file that contains most of the interface's functionality.
* ```static/answers.json``` contains all of the possible answers that are system can guess on (extracted from the training data portion of the Quiz Bowl data).
* ```logs```, ```log_list```, ```evidenceStore``` are all folders that store logs about the user's actions and submitted questions. This will be phased out in place of a database in future versions.

## Non-QANTA Server

The Non-QANTA server ```/non_qanta``` handles certain backend functionality that doesn't involve answering questions or calculating evidence. Originally it did more computation, and it was separated out to put computationally expensive things on a different machine. It can probably be merged into the Main Interface at some point.

Non-QANTA hosts two REST endpoints that the main interface uses. ```get_question``` and ```search_answers```. ```get_question``` gets a question from the development set to be rewritten by the user. ```search_answers``` searches all past questions (from the Quiz Bowl dataset) and returns the top ones based on n-gram overlap with your question. This fills the past evidence box in the interface.

## QANTA

QANTA is used for answering questions and generating the evidence that is highlighted in the interface. The current version of the interface uses the RNN guesser, though an elastic search version is available.

QANTA hosts two REST endpoints that the main interface uses. ```get_highlights``` and ```answer_question```. To get QANTA up and running, see that [repository](https://github.com/Pinafore/qb). The code to run the correct QANTA services is part of the web app API code. We also have docker containers available (see instructions to run the interface above).

## Parse Logs and Postprocessing

All of the postprocessing from the submitted questions happens in ```/postprocessing```. Use ```extract_raw_question_text.py''' to save all the text of the existing questions. Then run ```save_final_questions.py'''.


### Post Processing of Data
* I added filters for vulgar words, which accidently caught some words like Rape. Make sure this isn't happening for real questions (not spam).
* Some of the questions are very close to duplicates. For example, they changed "10 points" to "ten points". See if you can filter these out (probably check n-gram similarity and then filter out by hand).
* Make all the questions say "For 10 points" or whatever is said in the Quiz Bowl data. I think Pedro has tried to be consistent about this (he might have scripts already for this). i.e. "for the points" -> "for 10 points" or "ftp" -> "for 10 points".

### Weird Things To Note
* references to ```email``` in JS is not the email, but rather is a hash
* Everything uses ```*``` or ```**``` for delimiting between different fields. JSON should be used instead =( 
* The highlighting functionality needs to be cleaned up. Think you should contact me if you want to change that.
* editID is -1 when your not editing. Set when you are.

## Contact
This code is maintained by Eric Wallace. Feel free to open bug report or pull requests. For contact, find my email on [my website](http://www.ericswallace.com).

## References
[1] Eric Wallace, Pedro Rodriguez, Shi Feng, Ikuya Yamada, and Jordan Boyd-Graber, [Trick Me If You Can: Human-in-the-loop Generation of Adversarial Question Answering Examples](https://arxiv.org/abs/1809.02847). 

```
@inproceedings{Wallace2019Trick,
  title={Trick Me If You Can: Human-in-the-loop Generation of Adversarial Question Answering Examples},
  author={Eric Wallace and Pedro Rodriguez and Shi Feng and Ikuya Yamada and Jordan Boyd-Graber},
  booktitle = "Transactions of the Association for Computational Linguistics"
  year={2019},  
}
```
