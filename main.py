from app import app

# Home endpoint
@app.route("/")
def index():
  return "Welcome to YouTify API"

if __name__ == "__main__":
  app.run(debug=True, host="0.0.0.0", port=8080, ssl_context=(".cert/cert.pem", ".cert/key.pem"))
