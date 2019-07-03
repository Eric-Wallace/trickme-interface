For internal use only, you won't need these instructions:

Go to aqwi00 `ssh aqwi00`.


Get anaconda loaded. `cd /srv/www/aqwi`, then `source anaconda3/bin/activate`.

Start the front-end app `cd es_version/adversarial-interface-divided/adversarialQA`, then `screen gunicorn --bind 0.0.0.0:7000 adversarial:app --workers 4`, and quit the screen.

Then open to connection between aqwi00 and aqwi01. `screen ssh -L 8000:localhost:8000 aqwi01` and quit the screen. and then `screen ssh -L 5000:localhost:5000 aqwi01` and quit the screen.

Move to aqwi01, `ssh aqwi01`, and get anaconda on that machine `source /scratch0/anaconda3/bin/activate`.

start the non_qanta server (has the question DB and stuff), `cd /scratch0/es_interface/adversarial-interface-divided/non_qanta` and then `screen python non_qanta_server.py`.

Start elastic search for QANTA `cd /scratch0/qb/packer/bin/elasticsearch-5.6.2/bin` and then `./elasticsearch -d`

Start QANTA, `cd /scratch0/temp/qb/` and then `screen python runMeES.py`.
