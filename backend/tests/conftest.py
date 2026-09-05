import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["DEV_TRUST_HEADER"] = "1"
