import os
from dotenv import load_dotenv

load_dotenv()

AZDO_ORG = os.getenv("AZDO_ORG")
AZDO_PROJECT = os.getenv("AZDO_PROJECT")
AZDO_PAT = os.getenv("AZDO_PAT")

if not all([AZDO_ORG, AZDO_PROJECT, AZDO_PAT]):
    raise ValueError("Missing Azure DevOps configuration in .env")