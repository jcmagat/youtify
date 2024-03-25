from app import app

if __name__ == "__main__":
    # app.run(debug=True, host="0.0.0.0", port=8080, ssl_context=(".cert/cert.pem", ".cert/key.pem"))
    app.run(host="0.0.0.0", port=8080)
