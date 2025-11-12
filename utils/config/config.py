import os
from dotenv import load_dotenv

load_dotenv(".env")

class Config:
    def __init__(self):

        self.emailStake = os.getenv("emailStake", None)
        self.passwordStake = os.getenv("passwordStake", None)

        self.tokenAPI = os.getenv("tokenAPI", '')
        self.baseUrlApi = os.getenv("baseUrlApi", None)

        self.PARTNER_ID = os.getenv("PARTNER_ID", None)
        self.CLICKID = os.getenv("CLICKID", None)


config = Config()
