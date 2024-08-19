install:
	pip install --upgrade pip &&\
		pip install -r requirements.txt

# test:
# 	python -m pytest -vv tests/*.py

format:
	isort --profile=black --skip .venv_tg . &&\
	autopep8 --in-place ./*.py tools/*.py etl_feed/*.py &&\
	black --line-length 88 . --exclude .venv_tg


lint:
	pylint --disable=R,C *.py tools/*.py etl_feed/*.py


TODAY := $(shell date +%Y-%m-%d)
DATED_FOLDER := $(TODAY)_
STORAGE_DIR := $(shell pwd)/datasets
NEXT_NUM := $(shell bash enum_folder.sh $(STORAGE_DIR) $(DATED_FOLDER))
DATED_ENUM_FOLDER := $(DATED_FOLDER)$(NEXT_NUM)
DATED_ENUM_DIR := $(STORAGE_DIR)/$(DATED_ENUM_FOLDER)

create_enum_folder:
	mkdir -p $(DATED_ENUM_DIR)