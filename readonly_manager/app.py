from src import app, os

if __name__ == "__main__":
    print(os.environ["HOSTNAME"])
    app.run(host=os.environ["HOSTNAME"],port=5000)