FROM python:3
ADD . /
RUN pip3 install discord
RUN pip3 install nltk
RUN pip3 install python-dotenv
RUN pip3 install pynacl
RUN pip3 install gino
CMD ["python3", "./bot.py"]