from app import create_app

app = create_app()

if __name__ == "__main__":
    # debug=True giúp server tự tải lại khi bạn thay đổi code
    app.run(debug=True, port=5000)