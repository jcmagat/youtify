from dotenv import load_dotenv
from flask import Flask
import os

load_dotenv(".env")

app = Flask(__name__)
app.secret_key: str = os.getenv("APP_SECRET_KEY")

# Home endpoint
@app.route("/")
def index():
  return "Welcome to YouTify <a href='/login'>Login with Spotify</a>"

if __name__ == "__main__":
  app.run(host="0.0.0.0", debug=True, port=8080)
