from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from nbabetting import app as application

if __name__ == '__main__':
    application.run()
