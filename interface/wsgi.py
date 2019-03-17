# this file is required by gunicorn so the web app can run on multiple cores. Shouldn't
# need to edit this

from web_server import app

if __name__ == "__main__":
    app.run(host=7000, port='0.0.0.0', debug=False)
