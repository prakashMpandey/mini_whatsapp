from src import create_app
from src import io

app = create_app()
if __name__ == "__main__":
    print("server is starting")
    io.run(app,host="0.0.0.0",port=5000,debug=False)
