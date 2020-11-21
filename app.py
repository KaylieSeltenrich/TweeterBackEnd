import mariadb
from flask import Flask, request, Response
import json 
import dbcreds
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/users', methods=['GET','POST','PATCH','DELETE'])
def users():
    if request.method == 'GET':
        conn = None
        cursor = None
        users = None
    try:
        conn = mariadb.connectconn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, user=dbcreds.user, port=dbcreds.port, database=dbcreds.database)