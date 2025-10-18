To host the web server, I used a combination of Gunicorn and ngrok. In order to do this on any device, you need a Linux environment, gunicorn installed, ngrok, and whitenosie installed. White noise is needed for static files to be rendered properly 
Python pip install gunicorn
snap install ngrok (may need sudo)
pip install whitenoise

curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
  | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
  && echo "deb https://ngrok-agent.s3.amazonaws.com bookworm main" \
  | sudo tee /etc/apt/sources.list.d/ngrok.list \
  && sudo apt update \
  && sudo apt install ngrok

you will also need to make an ngrok account, get the authentication token, and run:
 ngrok config add-authtoken [authentication token]

Changes to the code: 
Import OS
Add to middle wear: 'whitenoise.middleware.WhiteNoiseMiddleware',
change to static files: STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
run: python manage collect static
to start the server:
gunicorn Harmonet.wsgi:application --bind 0.0.0.0:8000
in another terminal run: ngrok http 8000

this should give you a link to a webpage
