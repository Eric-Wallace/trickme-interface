For internal use only, you won't need these instructions:

```
ssh aqwi00
cd /srv/www/aqwi
source anaconda3/bin/activate
cd es_version/adversarial-interface-divided/adversarialQA
screen gunicorn --bind 0.0.0.0:7000 adversarial:app --workers 4
screen ssh -L 8000:localhost:8000 aqwi01
screen ssh -L 5000:localhost:5000 aqwi01

ssh aqwi01`
cd /scratch0/es_interface/adversarial-interface-divided/non_qanta
source /scratch0/anaconda3/bin/activate
screen python non_qanta_server.py
cd /scratch0/qb/packer/bin/elasticsearch-5.6.2/bin
./elasticsearch -d
cd /scratch0/temp/qb/
screen python runMeES.py
```
