FROM python
WORKDIR /sai
COPY req.txt .
RUN pip install -r req.txt
COPY . .
CMD ["python","app.py"]
