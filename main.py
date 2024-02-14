from app import app

# Home endpoint
@app.route("/")
def index():
  return "Welcome to YouTify <a href='/spotify/login'>Login with Spotify</a>"

if __name__ == "__main__":
  app.run(host="0.0.0.0", debug=True, port=8080)
