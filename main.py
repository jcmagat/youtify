from app import app

# Home endpoint
@app.route("/")
def index():
  return "Welcome to YouTify <a href='oauth/spotify/login'>Spotify</a> <a href='oauth/youtube/login'>YouTube</a>"

if __name__ == "__main__":
  app.run(debug=True, port=8080, ssl_context=(".cert/cert.pem", ".cert/key.pem"))
