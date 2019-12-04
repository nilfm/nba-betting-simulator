from nbabetting import app
import os
from dotenv import load_dotenv

project_folder = '/root/nba-betting-simulator'
load_dotenv(os.path.join(project_folder, '.env'))

if __name__ == '__main__':
    app.run()
