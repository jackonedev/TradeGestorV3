install:
	pip install --upgrade pip &&\
		pip install -r requirements.txt

# test:
# 	python -m pytest -vv tests/*.py

format:
	isort --profile=black --skip .venv_tg --skip .env_aux . &&\
	autopep8 --in-place ./*.py tools/*.py etl_feed/*.py &&\
	black --line-length 88 . --exclude '(\.venv_tg|\.env_aux)'


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

install_talib:
	apt-get install -y build-essential
	cd ~
	wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
	tar -xzf ta-lib-0.4.0-src.tar.gz
	cd ta-lib
	./configure -prefix=/usr
	make
	sudo make install
	pip install TA-Lib
	pip install numpy==1.26.4