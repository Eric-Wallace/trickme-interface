/* The main file that does pretty much all of the functionality for the site */

// all of the possible answers (TODO needs to be updated)

var disableButtonTimeout = null;
question_answer = 'blank';

// guessForEvidence indicates which of the predictions in the Guesses section
// the user wants evidence for. i.e. if George Washington is the top prediction,
// and then Abraham Lincoln is the second highest prediction, and guessForEvidence
// is 2. Then the Abraham Lincoln Evidence will be shown. 
var guessForEvidence = 1;

// buttons are triggered by dropdown, and change state of which evidence to show
function storeOne(){ 
	guessForEvidence = 1;
	predict();
}

function storeTwo(){ 
	guessForEvidence = 2; 
	predict();
}

function storeThree(){ 
	guessForEvidence = 3;
	predict();
}

function storeFour(){ 
	guessForEvidence = 4;
	predict();	
}

function storeFive(){ 
	guessForEvidence = 5;
	predict();
}

// In the special case where the user's answer is in the top 20 but not in the top 5,
// guessForEvidence can be set to 6-20
function storeSix(){
	guessForEvidence = document.getElementById("AnswerPosition").innerHTML;
	predict();
}

// Triggered on presses to the Guess button or automatically, calls ElasticSearch guesser
// Places results into the "Guess" boxes on the left of the UI. Detects if the user's
// guess is not in the top 5 but is in the top 20, and if so it adds a sixth guess field.
// also calls evidence() at the end to get new evidence once the new guesses are in
function predict() {
	var text = document.getElementById("questionText").textContent;  // grab content from question box
	var time = new Date().getTime() / 1000; // get time in seconds     
	$('#guessButton').prop('disabled',true).css('opacity',0.5); // disable buttons when things ae updated

	var email_val = Cookies.get('email');

	// Send the question text and email, etc. to adversarial.py server
	$.post("predictES", {text: text, time: time, answer: question_answer, email: email_val},   
		function(data, status){                                   	
			if (data === "Empty"){   // if empty, then something weird happened on server side, so clear all fields 
				for (i = 0; i < 5; i++){
					guess = "Guess" + (i+1);
					score = "Score" + (i+1);
					document.getElementById(guess).innerHTML = " ";
					document.getElementById(guess + "_2").innerHTML = " ";
					document.getElementById(score).innerHTML = " ";
				}
				document.getElementById("AnswerGuess").innerHTML = " ";
				document.getElementById("AnswerGuess_2").innerHTML = " ";
				document.getElementById("AnswerScore").innerHTML = " ";
				document.getElementById("AnswerPosition").innerHTML = " ";
			}

			else {   // we got answers back from QANTA
                                var results = data.split("**"); // parse incoming
				// doc_names are the guesses, scores is the prediction confidences from qanta, links are the links to corresponding wiki page				
				var doc_names = results[0].split("*");   
				var doc_scores = results[1].split("*");
				var doc_links = results[2].split("*");   
				document.getElementById("header2").innerHTML = "Confidence";      // I use to change the title based on different conditons, but don't anymore. Probs can delete
				
				for (i = 0; i < 5; i++){   // turn guesses into hyperlink and display on guess window along with scores
					var link = "<a href=\"" + doc_links[i] + '" target="_blank" style="color:blue' + "\">" + doc_names[i].replace("_", " ").substring(0,25) + "</a>"; // hyperlink
					document.getElementById("Guess" + (i+1)).innerHTML = link;
					document.getElementById("Guess" + (i+1) + "_2").innerHTML = doc_names[i].replace("_", " ").substring(0,25);
					document.getElementById("Score" + (i+1)).innerHTML = doc_scores[i];					
				}

				if (doc_names.length == 6){  // if there is length 6 returned, then ur guess is in the top 20 but not top 5. In this case, add a sixth place for guesses
					var link = "<a href=\"" + doc_links[5] + '" target="_blank" style="color:blue' + "\">" + doc_names[5].replace("_", " ").substring(0,25) + "</a>"; // hyperlink			
					document.getElementById("AnswerGuess").innerHTML = link;
					document.getElementById("AnswerGuess_2").innerHTML = doc_names[5].replace("_", " ").substring(0,25) ;
					document.getElementById("AnswerScore").innerHTML = doc_scores[5];
					document.getElementById("AnswerPosition").innerHTML = results[3];       				
				}
				else {	// if length is not 6, then clear the sixth guess field
					document.getElementById("AnswerGuess").innerHTML = " ";
					document.getElementById("AnswerGuess_2").innerHTML = " ";
					document.getElementById("AnswerScore").innerHTML = " ";
					document.getElementById("AnswerPosition").innerHTML = " ";
				}
			}
			
			 // if the top guess is correct, then place the bell and the phrase it buzzed 
			 // underneath the text box. Also uses cookies to track in which position in which sentence
			 // the buzz is in. Evidence will update the evidence and then place the bell accordingly.
			if (doc_names[0].replace("_", " ") == question_answer){	 
				var span = document.getElementById('bellBar').innerHTML;
				$.post("placeBell", {text: text, answer: question_answer},   // find the bell location
					function(data, status){ 
						var bell = '\uD83D\uDD14';  // bell icon in unicode                                      
						bell = "<mark data-entity=\"buzz\">" + bell + " Buzz </mark>"; 
						document.getElementById('bellBar').innerHTML = "<b> QANTA" + bell + "</span>" + "on: </b>" + data.split("**")[0];
						bellPos = data.split("**")[1];
						bellSentence = data.split("**")[2];
						Cookies.set("bellPos", bellPos, {expires:1});					
						Cookies.set("bellSentence", bellSentence, {expires:1});				
						evidence();	  // When the user presses predict, you need to update the evidence because the predictions might change.
					})				
			}
			else { // if prediction is wrong, clear phrase below the text box
				document.getElementById('bellBar').innerHTML = "";
				Cookies.set("bellPos", "none", {expires:1});	
				evidence();
			}
		});
}

// asks the server for all of this user's past questions that they submitted. Then it makes them
// into dynamic buttons in the bottom right of the UI
function loadSubmittedAnswers(divId) {
	while(document.getElementById(divId).firstChild){  // remove all past toggle boxes
		document.getElementById(divId).removeChild(document.getElementById(divId).firstChild);
	}
	var button_template = '<button class="btn btn-info" type="button" data-toggle="collapse" data-target="#answerResult';
	var button_template2 = '" > ';
	var button_template3 = '</button> <div class="collapse" style = "font-size: 18px;" id="answerResult';
	var button_template4 = '"> <div class="card card-block"></div> </div> <br> <br>';
	var edit_button_template1 = '<button class="btn btn-info" type="button" onclick="editQuestion(';
	var edit_button_template2 = ')";> Edit </button>';

	var email_val = Cookies.get('email');
	if (!(typeof email_val === "undefined")){
		$.post("load_submitted", {email: email_val},
			function(data, status){               
				if (!(data === 'undefined')){
					var answers = data;
					for (i = 0; i < answers.length; i+=2){
						if (!(answers[i] == "nullToken")){
							var newdiv = document.createElement('div');
							newdiv.innerHTML = button_template + i + divId +  button_template2 + answers[i] + button_template3 + i + divId +  button_template4; 
							document.getElementById(divId).appendChild(newdiv);
							document.getElementById("answerResult" + i + divId).innerHTML = '<br>' + answers[i+1] + '  ' + edit_button_template1 + i + edit_button_template2;				
						}
					}    
				}
			});
	}
}

// Searches existing Quiz Bowl questions based on answer the user provided as the beginning// 
// Uses dynamicInput to display the toggle boxes that appear when results are returned
function search() {
	$('#updateButton').prop('disabled',true).css('opacity',0.5);  // disable button
	var text = document.getElementById("questionText").textContent;
	var query = document.getElementById("question_answer").innerHTML;
	var time = new Date().getTime() / 1000; // get time in seconds     
	$('#searchButton').prop('disabled',true).css('opacity',0.5);
	while(document.getElementById("dynamicInput").firstChild){  // remove all past toggle boxes
		document.getElementById("dynamicInput").removeChild(document.getElementById("dynamicInput").firstChild);
	}

	var email_val = Cookies.get('email');
	$.post("search", {text: text, time: time, query: query, email: email_val},
		function(data, status){
			if (data === "No Matches"){ // if the server returns this, there was no past answers or something bad happened. Clear everything
				var newdiv = document.createElement('div');
				newdiv.innerHTML = "No Matches";
				document.getElementById("dynamicInput").appendChild(newdiv);
			}
			else {
				var results = data.split("***"); // parse incoming
				var tournaments = results[0].split("**");
				var text = results[1].split("**");
				var display = "";
				
				// create new dynamic toggle button and store the correct data into its fields
				var button_template = '<button class="btn btn-info" type="button" data-toggle="collapse" data-target="#searchResult';
				var button_template2 = '" > ';
				var button_template3 = '</button> <div class="collapse" id="searchResult';
				var button_template4 = '"> <div class="card card-block"></div> </div> <br> <br>';

				for (i = 0; i < tournaments.length; i++){
					if (i > 5) {    // only show top 5 (or is it 6?) of the questions, because it can get quite long otherwise
						break;
					}
					rewrite_flag = Cookies.get('rewrite_question');
					if (i == 0 && rewrite_flag == "true"){  // if you are rewriting, the question you are rewriting will almost always be the most common. So just skip the first
						continue;
					}
					var newdiv = document.createElement('div');
					newdiv.innerHTML = button_template + i + button_template2 + tournaments[i] + button_template3 + i + button_template4; 
					document.getElementById("dynamicInput").appendChild(newdiv);
					document.getElementById("searchResult" + i).innerHTML = '<br>' + text[i];
				}				
			}
		});
}

// Given the sentence from your question and the evidence from QB, it highlights the matches between them.
// Depending on which sentence it is (first, second, third, etc.) it sets the color differently
function highlight_sentences(highlightlists){
	for (i = 0; i < highlightlists.length; i++){
		highlightlist = highlightlists[i].split("*");
		
		text = document.getElementById("Sentence" + (i+1)).innerHTML.split(" ");
		for (j = 0; j < text.length; j++){
			for (k = 0; k < highlightlist.length; k++){
				var temp1 = text[j].toLowerCase().replace('.','');
				temp1 = temp1.replace(',','');
				temp1 = temp1.replace(';','');
				temp1 = temp1.replace('?','');
				temp1 = temp1.replace('!','');
				temp1 = temp1.replace('\'','');
				temp1 = temp1.replace('\"','');
				temp1 = temp1.replace('\'','');
				temp1 = temp1.replace('\"','');
				temp1 = temp1.replace("\\",'');
				temp1 = temp1.replace("/",'');

				var temp2 = highlightlist[k].toLowerCase().replace('.','');
				temp2 = temp2.replace(',','');
				temp2 = temp2.replace(';','');
				temp2 = temp2.replace('?','');
				temp2 = temp2.replace('!','');
				temp2 = temp2.replace('\'','');
				temp2 = temp2.replace('\"','');
				temp2 = temp2.replace('\'','');
				temp2 = temp2.replace('\"','');
				temp2 = temp2.replace("\\",'');
				temp2 = temp2.replace("/",'');

				if (temp1 === temp2.replace("__1",'').replace("__2",'').replace("__3",'').replace("__4",'')){
					if (i == 0){
						if (temp2.indexOf('1') >= 0){
							text[j] = "<mark data-entity=\"norp1\">" + text[j] + "</mark>"; 
						}
						else if (temp2.indexOf('2') >= 0){
							text[j] = "<mark data-entity=\"norp2\">" + text[j] + "</mark>";
						}

						else if (temp2.indexOf('3') >= 0){
							text[j] = "<mark data-entity=\"norp3\">" + text[j] + "</mark>";
						}

						else if (temp2.indexOf('4') >= 0){
							text[j] = "<mark data-entity=\"norp4\">" + text[j] + "</mark>";
						}

					}
					if (i == 1){
						if (temp2.indexOf('1') >= 0){
							text[j] = "<mark data-entity=\"person1\">" + text[j] + "</mark>";
						}
						else if (temp2.indexOf('2') >= 0){
							text[j] = "<mark data-entity=\"person2\">" + text[j] + "</mark>";
						}

						else if (temp2.indexOf('3') >= 0){
							text[j] = "<mark data-entity=\"person3\">" + text[j] + "</mark>";
						}

						else if (temp2.indexOf('4') >= 0){
							text[j] = "<mark data-entity=\"person4\">" + text[j] + "</mark>";
						}

					}

					if (i == 2){
						if (temp2.indexOf('1') >= 0){
							text[j] = "<mark data-entity=\"org1\">" + text[j] + "</mark>";
						}
						else if (temp2.indexOf('2') >= 0){
							text[j] = "<mark data-entity=\"org2\">" + text[j] + "</mark>";
						}

						else if (temp2.indexOf('3') >= 0){
							text[j] = "<mark data-entity=\"org3\">" + text[j] + "</mark>";
						}

						else if (temp2.indexOf('4') >= 0){
							text[j] = "<mark data-entity=\"org4\">" + text[j] + "</mark>";
						}

					}

					if (i == 3){
						if (temp2.indexOf('1') >= 0){
							text[j] = "<mark data-entity=\"norp1\">" + text[j] + "</mark>";
						}
						else if (temp2.indexOf('2') >= 0){
							text[j] = "<mark data-entity=\"norp2\">" + text[j] + "</mark>";
						}

						else if (temp2.indexOf('3') >= 0){
							text[j] = "<mark data-entity=\"norp3\">" + text[j] + "</mark>";
						}

						else if (temp2.indexOf('4') >= 0){
							text[j] = "<mark data-entity=\"norp4\">" + text[j] + "</mark>";
						}

					}

					if (i == 4){
						if (temp2.indexOf('1') >= 0){
							text[j] = "<mark data-entity=\"person1\">" + text[j] + "</mark>";
						}
						else if (temp2.indexOf('2') >= 0){
							text[j] = "<mark data-entity=\"person2\">" + text[j] + "</mark>";
						}

						else if (temp2.indexOf('3') >= 0){
							text[j] = "<mark data-entity=\"person3\">" + text[j] + "</mark>";
						}

						else if (temp2.indexOf('4') >= 0){
							text[j] = "<mark data-entity=\"person4\">" + text[j] + "</mark>";
						}

					}

				}
			}
		}
		document.getElementById("Sentence" + (i+1)).innerHTML = text.join(' ');
	}
}


// Get the highlights from Elastic Search
function evidence() {
	var text = document.getElementById('questionText').textContent;
	var time = new Date().getTime() / 1000; // get time in seconds     
	$('#evidenceButton').prop('disabled',true).css('opacity',0.5);	
	var email_val = Cookies.get('email');

	// identity is the actual name of the Guess. Depending on guessForEvidence, send the correct person.
	if (guessForEvidence == 1){
		identity_guessForEvidence = document.getElementById("Guess1").innerHTML;
	}
	else if (guessForEvidence == 2){
		identity_guessForEvidence = document.getElementById("Guess2").innerHTML;
	}
	else if (guessForEvidence == 3){
		identity_guessForEvidence = document.getElementById("Guess3").innerHTML;
	}
	else if (guessForEvidence == 4){
		identity_guessForEvidence = document.getElementById("Guess4").innerHTML;
	}
	else if (guessForEvidence == 5){
		identity_guessForEvidence = document.getElementById("Guess5").innerHTML;
	}
	else{
		identity_guessForEvidence = document.getElementById("AnswerGuess").innerHTML;
	}

	$.post("highlight", {text: text, time: time, guessForEvidence: identity_guessForEvidence, email: email_val},
		function(data, status){                
		if (data === "IndexError"){	// error condition returned from server, clear everything		
			document.getElementById("Evidence1").innerHTML = " ";
			document.getElementById("Evidence2").innerHTML = " ";
			document.getElementById("Evidence3").innerHTML = " ";
			document.getElementById("Evidence4").innerHTML = " ";
			document.getElementById("Evidence5").innerHTML = " ";
			document.getElementById("guess_of_matches").innerHTML = " ";		

			document.getElementById("Sentence1").innerHTML = " ";
			document.getElementById("Sentence2").innerHTML = " ";
			document.getElementById("Sentence3").innerHTML = " ";
			document.getElementById("Sentence4").innerHTML = " ";
			document.getElementById("Sentence5").innerHTML = " ";

		}

		// the four different evidence panes that you can cycle through are stored on the server side. The keep track of which evidence pane you are currently looking at, it uses this ugly method. It has an array with the
		// four entries ["evidence1","evidence2","evidence3","evidence4"]. The current pane is the entry in index 0. To go to evidence 2 (triggered when the button is pressed), you left rotate the array.
		else { // results returned from server
			Cookies.set("evidenceResults",["evidence1","evidence2","evidence3","evidence4"],{expires:1});			
			var results = data.split("***"); // parse incoming                      
			document.getElementById("guess_of_matches").innerHTML = results[0];								

			// place evidence and sentences into their spots
			evidence_results = results[1].split("**"); 
			document.getElementById("Evidence1").innerHTML = evidence_results[0].replace(/<mark>/g, "<mark data-entity=\"norp2\">");
			document.getElementById("Evidence2").innerHTML = evidence_results[1].replace(/<mark>/g, "<mark data-entity=\"person2\">");
			document.getElementById("Evidence3").innerHTML = evidence_results[2].replace(/<mark>/g, "<mark data-entity=\"org2\">");
			document.getElementById("Evidence4").innerHTML = evidence_results[3].replace(/<mark>/g, "<mark data-entity=\"norp2\">");
			document.getElementById("Evidence5").innerHTML = evidence_results[4].replace(/<mark>/g, "<mark data-entity=\"person2\">");

			sentence_results = results[2].split("**");
			document.getElementById("Sentence1").innerHTML = sentence_results[0];
			document.getElementById("Sentence2").innerHTML = sentence_results[1];
			document.getElementById("Sentence3").innerHTML = sentence_results[2];
			document.getElementById("Sentence4").innerHTML = sentence_results[3];
			document.getElementById("Sentence5").innerHTML = sentence_results[4];			

			// the source indicator says which dataset the evidence can from, either Quiz Bowl or Wikipedia. Just append it to the end
			source_indicator = results[4].split("**");		
			for (i = 0; i < source_indicator.length; i++){				
				document.getElementById("Evidence" + (i+1)).innerHTML = document.getElementById("Evidence" + (i+1)).innerHTML + "... " + "<h7 font-family: Linux-Libertine style=\"display:inline-block;\">" + source_indicator[i] + "</h7>";
			}

			// This puts the bell inside the evidence box. If you are currently looking at the evidence for the top guess, and the bellPos is set (QANTA is correct), then place the bell in
			sentence_indices = results[5].split("**");	
			if (guessForEvidence == 1){
				for (i = 0; i < sentence_indices.length; i++){
					if (sentence_indices[i] == Cookies.get("bellPos")){
						var bell = '\uD83D\uDD14';
						bell = "<b><mark data-entity=\"buzz\">" + bell + " Buzz </b></mark>";     
						split_sentence = document.getElementById("Sentence" + (i+1)).textContent.split(" ");
						bellSentence = Cookies.get("bellSentence").split(" "); // this cookie tells you where to put the bell
						for (k = split_sentence.length - 1; k > -1; k--){
							if (split_sentence[k] == bellSentence[bellSentence.length-1]){
								if (k == 0 || split_sentence[k-1] == bellSentence[bellSentence.length-2]){
									split_sentence.splice(k+1,0,bell);  // put the bell inside
									break;
								}
							}
						}
						document.getElementById("Sentence" + (i+1)).innerHTML = split_sentence.join(' ');
					}
				}
			}

			highlight_sentences(results[3].split("**"));  // highlight the overlaps between your sentences and the QANTA evidence.
			if (guessForEvidence === 1){
				for (i = 0; i < sentence_indices.length; i++){
					if (sentence_indices[i] > Cookies.get("bellPos")){ // very big block of code. all this does it gray out the evidence boxes that are below where the bell is 
						document.getElementById("Sentence" + (i+1)).innerHTML = "<div class = \"text-muted\">" + document.getElementById("Sentence" + (i+1)).innerHTML + "</div>";
						document.getElementById("Evidence" + (i+1)).innerHTML = "<div class = \"text-muted\">" + document.getElementById("Evidence" + (i+1)).innerHTML + "</div>";
						document.getElementById("Evidence" + (i+1)).innerHTML = replaceAll(document.getElementById("Evidence" + (i+1)).innerHTML,"<mark data-entity=\"norp1\">", "<mark data-entity=\"norp-muted\">");
						document.getElementById("Evidence" + (i+1)).innerHTML = replaceAll(document.getElementById("Evidence" + (i+1)).innerHTML,"<mark data-entity=\"org1\">", "<mark data-entity=\"org-muted\">");
						document.getElementById("Evidence" + (i+1)).innerHTML = replaceAll(document.getElementById("Evidence" + (i+1)).innerHTML,"<mark data-entity=\"person1\">", "<mark data-entity=\"person-muted\">");
						document.getElementById("Evidence" + (i+1)).innerHTML = replaceAll(document.getElementById("Evidence" + (i+1)).innerHTML,"<mark data-entity=\"norp2\">", "<mark data-entity=\"norp-muted\">");
						document.getElementById("Evidence" + (i+1)).innerHTML = replaceAll(document.getElementById("Evidence" + (i+1)).innerHTML,"<mark data-entity=\"org2\">", "<mark data-entity=\"org-muted\">");
						document.getElementById("Evidence" + (i+1)).innerHTML = replaceAll(document.getElementById("Evidence" + (i+1)).innerHTML,"<mark data-entity=\"person2\">", "<mark data-entity=\"person-muted\">");
						document.getElementById("Evidence" + (i+1)).innerHTML = replaceAll(document.getElementById("Evidence" + (i+1)).innerHTML,"<mark data-entity=\"norp3\">", "<mark data-entity=\"norp-muted\">");
						document.getElementById("Evidence" + (i+1)).innerHTML = replaceAll(document.getElementById("Evidence" + (i+1)).innerHTML,"<mark data-entity=\"org3\">", "<mark data-entity=\"org-muted\">");
						document.getElementById("Evidence" + (i+1)).innerHTML = replaceAll(document.getElementById("Evidence" + (i+1)).innerHTML,"<mark data-entity=\"person3\">", "<mark data-entity=\"person-muted\">");
						document.getElementById("Evidence" + (i+1)).innerHTML = replaceAll(document.getElementById("Evidence" + (i+1)).innerHTML,"<mark data-entity=\"norp4\">", "<mark data-entity=\"norp-muted\">");
						document.getElementById("Evidence" + (i+1)).innerHTML = replaceAll(document.getElementById("Evidence" + (i+1)).innerHTML,"<mark data-entity=\"org4\">", "<mark data-entity=\"org-muted\">");
						document.getElementById("Evidence" + (i+1)).innerHTML = replaceAll(document.getElementById("Evidence" + (i+1)).innerHTML,"<mark data-entity=\"person4\">", "<mark data-entity=\"person-muted\">");
						document.getElementById("Sentence" + (i+1)).innerHTML = replaceAll(document.getElementById("Sentence" + (i+1)).innerHTML,"<mark data-entity=\"norp1\">", "<mark data-entity=\"norp-muted\">");
						document.getElementById("Sentence" + (i+1)).innerHTML = replaceAll(document.getElementById("Sentence" + (i+1)).innerHTML,"<mark data-entity=\"org1\">", "<mark data-entity=\"org-muted\">");
						document.getElementById("Sentence" + (i+1)).innerHTML = replaceAll(document.getElementById("Sentence" + (i+1)).innerHTML,"<mark data-entity=\"person1\">", "<mark data-entity=\"person-muted\">");
						document.getElementById("Sentence" + (i+1)).innerHTML = replaceAll(document.getElementById("Sentence" + (i+1)).innerHTML,"<mark data-entity=\"norp2\">", "<mark data-entity=\"norp-muted\">");
						document.getElementById("Sentence" + (i+1)).innerHTML = replaceAll(document.getElementById("Sentence" + (i+1)).innerHTML,"<mark data-entity=\"org2\">", "<mark data-entity=\"org-muted\">");
						document.getElementById("Sentence" + (i+1)).innerHTML = replaceAll(document.getElementById("Sentence" + (i+1)).innerHTML,"<mark data-entity=\"person2\">", "<mark data-entity=\"person-muted\">");
						document.getElementById("Sentence" + (i+1)).innerHTML = replaceAll(document.getElementById("Sentence" + (i+1)).innerHTML,"<mark data-entity=\"norp3\">", "<mark data-entity=\"norp-muted\">");
						document.getElementById("Sentence" + (i+1)).innerHTML = replaceAll(document.getElementById("Sentence" + (i+1)).innerHTML,"<mark data-entity=\"org3\">", "<mark data-entity=\"org-muted\">");
						document.getElementById("Sentence" + (i+1)).innerHTML = replaceAll(document.getElementById("Sentence" + (i+1)).innerHTML,"<mark data-entity=\"person3\">", "<mark data-entity=\"person-muted\">");
						document.getElementById("Sentence" + (i+1)).innerHTML = replaceAll(document.getElementById("Sentence" + (i+1)).innerHTML,"<mark data-entity=\"norp4\">", "<mark data-entity=\"norp-muted\">");
						document.getElementById("Sentence" + (i+1)).innerHTML = replaceAll(document.getElementById("Sentence" + (i+1)).innerHTML,"<mark data-entity=\"org4\">", "<mark data-entity=\"org-muted\">");
						document.getElementById("Sentence" + (i+1)).innerHTML = replaceAll(document.getElementById("Sentence" + (i+1)).innerHTML,"<mark data-entity=\"person4\">", "<mark data-entity=\"person-muted\">");
					}
				}
			}
		}	
	});
}

// duplicates much of the code from evidence(). It left rotates the evidence array, and then based on that it gets the new evidence pane from the server.
function moreEvidence(){
	indicator = arrayRotate(JSON.parse(Cookies.get("evidenceResults")));			
	Cookies.set("evidenceResults", indicator, {expires:1});
	var email_val = Cookies.get('email');
	$.post("more_evidence", {email: email_val, indicator: indicator[0]},
		function(data,status){
			results = data;	
			if (results == "None"){
				return;
			}
			results = data.split("***");
			document.getElementById("guess_of_matches").innerHTML = results[0];			
				evidence_results = results[1].split("**");
				document.getElementById("Evidence1").innerHTML = evidence_results[0].replace(/<mark>/g, "<mark data-entity=\"norp2\">");
				document.getElementById("Evidence2").innerHTML = evidence_results[1].replace(/<mark>/g, "<mark data-entity=\"person2\">");
				document.getElementById("Evidence3").innerHTML = evidence_results[2].replace(/<mark>/g, "<mark data-entity=\"org2\">");
				document.getElementById("Evidence4").innerHTML = evidence_results[3].replace(/<mark>/g, "<mark data-entity=\"norp2\">");
				document.getElementById("Evidence5").innerHTML = evidence_results[4].replace(/<mark>/g, "<mark data-entity=\"person2\">");

				sentence_results = results[2].split("**");
				document.getElementById("Sentence1").innerHTML = sentence_results[0];
				document.getElementById("Sentence2").innerHTML = sentence_results[1];
				document.getElementById("Sentence3").innerHTML = sentence_results[2];
				document.getElementById("Sentence4").innerHTML = sentence_results[3];
				document.getElementById("Sentence5").innerHTML = sentence_results[4];			

				source_indicator = results[4].split("**");		
				for (i = 0; i < source_indicator.length; i++){
					document.getElementById("Evidence" + (i+1)).innerHTML = document.getElementById("Evidence" + (i+1)).innerHTML + "... " + "<h7 font-family: Linux-Libertine style=\"display:inline-block;\">" + source_indicator[i] + "</h7>";
				}

				sentence_indices = results[5].split("**");	
				if (guessForEvidence === 1){
					for (i = 0; i < sentence_indices.length; i++){
						if (sentence_indices[i] == Cookies.get("bellPos")){
							var bell = '\uD83D\uDD14';
							bell = "<b><mark data-entity=\"buzz\">" + bell + " Buzz </b></mark>";     
						split_sentence = document.getElementById("Sentence" + (i+1)).textContent.split(" ");
						bellSentence = Cookies.get("bellSentence").split(" ");
						for (k = split_sentence.length - 1; k > -1; k--){
							if (split_sentence[k] == bellSentence[bellSentence.length-1]){
								if (k == 0 || split_sentence[k-1] == bellSentence[bellSentence.length-2]){
									split_sentence.splice(k+1,0,bell);
									break;
								}
							}
						}
						document.getElementById("Sentence" + (i+1)).innerHTML = split_sentence.join(' ');
					}
				}
			}
			highlight_sentences(results[3].split("**"));
			if (guessForEvidence === 1){
				for (i = 0; i < sentence_indices.length; i++){
					if (sentence_indices[i] > Cookies.get("bellPos")){
						document.getElementById("Sentence" + (i+1)).innerHTML = "<div class = \"text-muted\">" + document.getElementById("Sentence" + (i+1)).innerHTML + "</div>";
						document.getElementById("Evidence" + (i+1)).innerHTML = "<div class = \"text-muted\">" + document.getElementById("Evidence" + (i+1)).innerHTML + "</div>";
						document.getElementById("Evidence" + (i+1)).innerHTML = replaceAll(document.getElementById("Evidence" + (i+1)).innerHTML,"<mark data-entity=\"norp1\">", "<mark data-entity=\"norp-muted\">");
						document.getElementById("Evidence" + (i+1)).innerHTML = replaceAll(document.getElementById("Evidence" + (i+1)).innerHTML,"<mark data-entity=\"org1\">", "<mark data-entity=\"org-muted\">");
						document.getElementById("Evidence" + (i+1)).innerHTML = replaceAll(document.getElementById("Evidence" + (i+1)).innerHTML,"<mark data-entity=\"person1\">", "<mark data-entity=\"person-muted\">");
						document.getElementById("Evidence" + (i+1)).innerHTML = replaceAll(document.getElementById("Evidence" + (i+1)).innerHTML,"<mark data-entity=\"norp2\">", "<mark data-entity=\"norp-muted\">");
						document.getElementById("Evidence" + (i+1)).innerHTML = replaceAll(document.getElementById("Evidence" + (i+1)).innerHTML,"<mark data-entity=\"org2\">", "<mark data-entity=\"org-muted\">");
						document.getElementById("Evidence" + (i+1)).innerHTML = replaceAll(document.getElementById("Evidence" + (i+1)).innerHTML,"<mark data-entity=\"person2\">", "<mark data-entity=\"person-muted\">");
						document.getElementById("Evidence" + (i+1)).innerHTML = replaceAll(document.getElementById("Evidence" + (i+1)).innerHTML,"<mark data-entity=\"norp3\">", "<mark data-entity=\"norp-muted\">");
						document.getElementById("Evidence" + (i+1)).innerHTML = replaceAll(document.getElementById("Evidence" + (i+1)).innerHTML,"<mark data-entity=\"org3\">", "<mark data-entity=\"org-muted\">");
						document.getElementById("Evidence" + (i+1)).innerHTML = replaceAll(document.getElementById("Evidence" + (i+1)).innerHTML,"<mark data-entity=\"person3\">", "<mark data-entity=\"person-muted\">");
						document.getElementById("Evidence" + (i+1)).innerHTML = replaceAll(document.getElementById("Evidence" + (i+1)).innerHTML,"<mark data-entity=\"norp4\">", "<mark data-entity=\"norp-muted\">");
						document.getElementById("Evidence" + (i+1)).innerHTML = replaceAll(document.getElementById("Evidence" + (i+1)).innerHTML,"<mark data-entity=\"org4\">", "<mark data-entity=\"org-muted\">");
						document.getElementById("Evidence" + (i+1)).innerHTML = replaceAll(document.getElementById("Evidence" + (i+1)).innerHTML,"<mark data-entity=\"person4\">", "<mark data-entity=\"person-muted\">");
						document.getElementById("Sentence" + (i+1)).innerHTML = replaceAll(document.getElementById("Sentence" + (i+1)).innerHTML,"<mark data-entity=\"norp1\">", "<mark data-entity=\"norp-muted\">");
						document.getElementById("Sentence" + (i+1)).innerHTML = replaceAll(document.getElementById("Sentence" + (i+1)).innerHTML,"<mark data-entity=\"org1\">", "<mark data-entity=\"org-muted\">");
						document.getElementById("Sentence" + (i+1)).innerHTML = replaceAll(document.getElementById("Sentence" + (i+1)).innerHTML,"<mark data-entity=\"person1\">", "<mark data-entity=\"person-muted\">");
						document.getElementById("Sentence" + (i+1)).innerHTML = replaceAll(document.getElementById("Sentence" + (i+1)).innerHTML,"<mark data-entity=\"norp2\">", "<mark data-entity=\"norp-muted\">");
						document.getElementById("Sentence" + (i+1)).innerHTML = replaceAll(document.getElementById("Sentence" + (i+1)).innerHTML,"<mark data-entity=\"org2\">", "<mark data-entity=\"org-muted\">");
						document.getElementById("Sentence" + (i+1)).innerHTML = replaceAll(document.getElementById("Sentence" + (i+1)).innerHTML,"<mark data-entity=\"person2\">", "<mark data-entity=\"person-muted\">");
						document.getElementById("Sentence" + (i+1)).innerHTML = replaceAll(document.getElementById("Sentence" + (i+1)).innerHTML,"<mark data-entity=\"norp3\">", "<mark data-entity=\"norp-muted\">");
						document.getElementById("Sentence" + (i+1)).innerHTML = replaceAll(document.getElementById("Sentence" + (i+1)).innerHTML,"<mark data-entity=\"org3\">", "<mark data-entity=\"org-muted\">");
						document.getElementById("Sentence" + (i+1)).innerHTML = replaceAll(document.getElementById("Sentence" + (i+1)).innerHTML,"<mark data-entity=\"person3\">", "<mark data-entity=\"person-muted\">");
						document.getElementById("Sentence" + (i+1)).innerHTML = replaceAll(document.getElementById("Sentence" + (i+1)).innerHTML,"<mark data-entity=\"norp4\">", "<mark data-entity=\"norp-muted\">");
						document.getElementById("Sentence" + (i+1)).innerHTML = replaceAll(document.getElementById("Sentence" + (i+1)).innerHTML,"<mark data-entity=\"org4\">", "<mark data-entity=\"org-muted\">");
						document.getElementById("Sentence" + (i+1)).innerHTML = replaceAll(document.getElementById("Sentence" + (i+1)).innerHTML,"<mark data-entity=\"person4\">", "<mark data-entity=\"person-muted\">");
					}
				}		
			}
		});			
}

// Called whenever a new question begins (i.e. after submitted, pressing new question, changing to rewrite)
// logs the user's email and resets some server side things (the evidence pane, etc.)
function begin() {
	Cookies.set('editID', -1, {expires: 300});
	Cookies.set("bellPos", "none", {expires:1});
	loadSubmittedAnswers("pastQuestionsDynamic");
	loadSubmittedAnswers("pastQuestionsDynamic2");
    var time = new Date().getTime() / 1000; // get time in seconds     
    var email = Cookies.get('email');
    $.post("begin", {email: email, time: time},
    	function(data, status){
    	});
    fillQuestionText();
}

// If they aren't in rewrite mode, does the autocommplete work. If they are in rewrite, loads the answer and question.
function fillQuestionText(){
	var rewrite_flag = Cookies.get('rewrite_question');
	var answer;
	if (Cookies.get('rewrite_question') === 'false'){	
		document.getElementById('myModal').style.display = "block";
		var curr_answer = document.getElementById("answer_area").innerHTML;
		$('#answer_area').typeahead('val', curr_answer);
		document.getElementById("answer_area").focus();
		document.getElementById("answer_area").addEventListener("keyup", function(event) {
	    	if (event.keyCode === 13) { // if they hit enter		        
	    		question_answer = document.getElementById("answer_area").value;
	    		if (poss_answers.includes(question_answer)){
	    			document.getElementById('invalidPage').innerHTML = " ";
	    			document.getElementById('myModal').style.display = "none";		        
	    			document.getElementById('question_answer').innerHTML = question_answer;   
					document.getElementById('question_answer_title').innerHTML = 'Questions about ' + question_answer + '<button onclick="search();" type="button" style = "margin-left: 10px; visibility: hidden;" class="btn btn-info btn-lg" id = "searchButton"> <i class ="fa fa-search"> </i> </button>';// <button class="btn btn-info" style = "margin-left: 30px" type="button" data-toggle="collapse" data-target="#dynamicInput" aria-expanded="true" aria-controls="collapseExample" id="collapseDynamic"> Toggle Show </button>';
				}		       
				else {
					document.getElementById('invalidPage').innerHTML = "         Sorry, our AI system can only answer the listed Quiz Bowl Questions";              
				}
			}
		});
	}

	var email_val = Cookies.get('email');
	var time = new Date().getTime() / 1000; // get time in seconds    
	$.post("rewrite", {rewrite: rewrite_flag, email: email_val, time: time},
		function(data, status){
			if (data != "None"){
				document.getElementById("questionText").innerHTML = data.split('**')[0];    
				document.getElementById('question_answer').innerHTML = data.split('**')[1];			
				question_answer = data.split('**')[1];
                document.getElementById('question_answer_title').innerHTML = 'Questions about ' + question_answer  + '<button onclick="search();" type="button" style = "margin-left: 10px; visibility: hidden;" class="btn btn-info btn-lg" id = "searchButton"> <i class ="fa fa-search"> </i> </button>'; // <button class="btn btn-info" style = "margin-left: 30px" type="button" data-toggle="collapse" data-target="#dynamicInput" aria-expanded="true" aria-controls="collapseExample" id="collapseDynamic"> Toggle Show </button>';
                search();
                predict();				
			}
			else {
				refresh();
			}        
		});
}

// toggles the flag of whether you are in rewrite mode or not
function rewrite() {
	var rewrite_flag;        
	rewrite_flag = Cookies.get('rewrite_question');
	if (rewrite_flag === 'false') { rewrite_flag = 'true'; }
	else { rewrite_flag = 'false';}
	Cookies.set('rewrite_question', rewrite_flag, {expires: 2});
	begin();
	if (Cookies.get('rewrite_question') === 'true'){
		document.getElementById("generate_or_not").innerHTML = "Create Unique Question";
	}
	else{
		document.getElementById("generate_or_not").innerHTML = "Modify Existing Question";
	}
}

// called in one specific place, don't remember why this is separated from newQuestion
function dump_rewrite(){
	var email = Cookies.get('email');
    var time = new Date().getTime() / 1000; // get time in seconds     
    $.post("servernewQuestion", {email: email, time: time},
	   	function(data, status){
    });
}

// logs the fact that the user started over with a new question  
function newQuestion(){
 	var email = Cookies.get('email');
	var time = new Date().getTime() / 1000; // get time in seconds    
	guessForEvidence = 1; 
	$.post("servernewQuestion", {email: email, time: time},
		function(data, status){
			begin();
		});
	$('#new_question_button').prop('disabled',true).css('opacity',0.5);
	clearTimeout(disableButtonTimeout);
	disableButtonTimeout = setTimeout(function () {
		$('#new_question_button').prop('disabled',false).css('opacity',1.0);
	}, 2000); 
}

// When they click edit on a specific past submitted question (based on index), it loads that question into the question
// box and the answer box. Calls predict() and things to load everything up
function editQuestion(index) {
	refresh();
	document.getElementById('editModal').style.display = "none";
	index = parseInt(index);
	var email_val = Cookies.get('email');
	$.post("load_submitted", {email: email_val},
		function(data, status){                
			if (!(data === 'undefined')){
				var answers = data;
				document.getElementById("questionText").innerHTML = answers[index+1];    
				document.getElementById('question_answer').innerHTML = answers[index];	
				question_answer = answers[index];	
		        document.getElementById('question_answer_title').innerHTML = 'Questions about ' + question_answer + '<button onclick="search();" type="button" style = "margin-left: 10px; visibility: hidden;" class="btn btn-info btn-lg" id = "searchButton"> <i class ="fa fa-search"> </i> </button>'; // <button class="btn btn-info" style = "margin-left: 30px" type="button" data-toggle="collapse" data-target="#dynamicInput" aria-expanded="true" aria-controls="collapseExample" id="collapseDynamic"> Toggle Show </button>';

		        predict();							
				search();		

				var email = Cookies.get('email');
				var time = new Date().getTime() / 1000; // get time in seconds     
				$.post("edit", {email: email, question: answers[index], answer: answers[index+1], time: time},
					function(data, status){
					});		

				Cookies.set('editID', index, {expires: 300}); // editID keeps track of which question you are editing. Sent to server to know which question to overwrite
				loadSubmittedAnswers("pastQuestionsDynamic");
				loadSubmittedAnswers("pastQuestionsDynamic2");
			}
		});
}

// Called when the user presses submit. Sends their question and refreshes the page
function submit() {
	var text = document.getElementById("questionText").textContent;  
	var time = new Date().getTime() / 1000; // get time in seconds     
	document.getElementById("exitButton").style.visibility="visible";  
	document.getElementById("editButton").style.visibility="visible";
	document.getElementById("modalRewriteButton").style.visibility="visible";
	$('#submitButton').prop('disabled',true).css('opacity',0.5);

	var rewrite = Cookies.get('rewrite_question');
	var split_answer = question_answer.split(" "); 
	var match_answer = split_answer.join('_').toLowerCase();
	var email_val = Cookies.get('email');
	var no_public_data = document.getElementById("no_public_data").checked;
	Cookies.set('private_data', no_public_data, {expires: 2});
	var private_data = Cookies.get('private_data');
	$.post("submit", {text: text, rewrite: rewrite, time: time, answer: match_answer, email: email_val, private_data: private_data},
		function(data, status){                
		});

	var editID = Cookies.get('editID');
	$.post("set_submitted", {email: email_val, editID: editID, question_answer: question_answer, text: text}, // set_submitted is a backup submit storage
		function(data, status){
			begin();
		});
	refresh();
	Cookies.set('editID', -1, {expires: 300}); // turn of editID (-1 means not editing)
	guessForEvidence = 1;
}

// Clears everything on the page
function refresh() {
	document.getElementById("bellBar").innerHTML = "";
	Cookies.set("bellPos", "none", {expires:1});
	Cookies.set("evidenceResults",["null","null","null","null"],{expires:1});			
	for (i = 0; i < 5; i++){
		evidenceID = "Evidence" + (i+1);            
		document.getElementById(evidenceID).innerHTML = " ";           
		document.getElementById("guess_of_matches").innerHTML = " "; 
		document.getElementById("Sentence" + (i+1)).innerHTML = " ";
	}   

	for (i = 0; i < 5; i++){
		guess = "Guess" + (i+1);
		score = "Score" + (i+1);
		document.getElementById(guess).innerHTML = " ";
		document.getElementById(guess + "_2").innerHTML = " ";
		document.getElementById(score).innerHTML = " ";  
	} 

	document.getElementById("AnswerGuess").innerHTML = " ";
	document.getElementById("AnswerGuess_2").innerHTML = " ";
	document.getElementById("AnswerScore").innerHTML = " ";
	document.getElementById("AnswerPosition").innerHTML = " ";


	while(document.getElementById("dynamicInput").firstChild){
		document.getElementById("dynamicInput").removeChild(document.getElementById("dynamicInput").firstChild);
	}

	document.getElementById("questionText").innerHTML = " ";
	document.getElementById("question_answer").innerHTML = " ";
	document.getElementById("question_answer_title").innerHTML = "Questions about " + '<button onclick="search();" type="button" style = "margin-left: 10px; visibility: hidden;" class="btn btn-info btn-lg" id = "searchButton"> <i class ="fa fa-search"> </i> </button> '; //<button class="btn btn-info" style = "margin-left: 30px" type="button" data-toggle="collapse" data-target="#dynamicInput" aria-expanded="true" aria-controls="collapseExample" id="collapseDynamic"> Toggle Show </button>';
}

// grabs all the questions that person submitted, and places them into a txt file that is downloaded
function downloadSubmitted() {
	var text = "";
	var email_val = Cookies.get('email');
	$.post("load_submitted", {email: email_val},
		function(data, status){                
			if (!(data === 'undefined')){
				var answers = data;
				if (answers.length > 0){
					for (i = 0; i < answers.length; i+=2){
						if (!(answers[i] == "nullToken")){
							text = text + answers[i] + ":" + "\n";
							text = text + answers[i+1] + "\n" + "\n";	
						}
					}
					var element = document.createElement('a');
					element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
					element.setAttribute('download', 'submitted_questions');
					element.style.display = 'none';
					document.body.appendChild(element);
					element.click();
					document.body.removeChild(element);    
				}			
			}
		});
}

// when they want to finish, show the exitModal and count how many questions they submitted
function exitGame(){
	document.getElementById('myModal').style.display = "none";
	document.getElementById('exitModal').style.display = "block";
	var email_val = Cookies.get('email');
	$.post("load_submitted", {email: email_val},
		function(data, status){                
			if (!(data === 'undefined')){
				var answers = data;
				var count = 0;
				for (i = 0; i < answers.length; i+=2){
					if (!(answers[i] == "nullToken")){
						count = count + 1;
					}
				}
			}
			document.getElementById("numQuestions").innerHTML = "You submitted " + count + " questions. You can download your questions below. ";
		});
}

// Closes "Enter answer to your question" modal and opens editModal when the button is clicked
function editExisting(){
	document.getElementById('myModal').style.display = "none";
	document.getElementById('editModal').style.display = "block";
}

// Closes "Enter answer to your question" modal when they hit rewrite
function rewriteExisting(){
	document.getElementById('myModal').style.display = "none";        
	rewrite();
}

// if they hit end game, but then they want to keep playying, close the modals and refill the question
function continuePlaying(){
	document.getElementById('exitModal').style.display = "none";
	document.getElementById('editModal').style.display = "none";
	fillQuestionText();
}

// auto trigger download button when they signout (just in case things break, you can tell people to check their downloads)
function signOut(){   
	downloadSubmitted(); 
	var cookies = document.cookie.split(";");
	for (var i = 0; i < cookies.length; i++) {
		var cookie = cookies[i];
		var eqPos = cookie.indexOf("=");
		var name = eqPos > -1 ? cookie.substr(0, eqPos) : cookie;
		document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT";
	}
	location.reload();
}

//utils below
function arrayRotate(arr, reverse){
	if(reverse)
		arr.unshift(arr.pop())
	else
		arr.push(arr.shift())
	return arr
} 

function validateEmail(email) {
	var re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
	return re.test(String(email).toLowerCase());
}

function replaceAll(str, find, replace) {
	return str.replace(new RegExp(find, 'g'), replace);
}
