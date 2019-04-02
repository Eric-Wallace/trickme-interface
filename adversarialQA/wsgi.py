# this file is required by gunicorn which enables the web app to run on multiple cores. Shouldn't
# need to edit this

from adversarial import app

if __name__ == "__main__":
    app.run(host=7000, port='0.0.0.0', debug=False)
