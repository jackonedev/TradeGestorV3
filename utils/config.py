import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASETS_PATH = os.path.join(PROJECT_ROOT, "datasets")

if not os.path.exists(os.path.join(PROJECT_ROOT, "datasets")):
    os.makedirs(os.path.join(PROJECT_ROOT, "datasets"))
