from src import create_app
from src import io

app = create_app()
if __name__ == "__main__":
    io.run(app)

    #     server = pywsgi.WSGIServer(
    #     ("0.0.0.0", 5000),
    #     app,
    #     handler_class=WebSocketHandler   # 🔥 THIS IS THE FIX
    # )

    #     server.serve_forever()
    # app.run(host= '0.0.0.0',
    #         port=3000,
    #         debug=True
    #         )
