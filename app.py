import mariadb
from flask import Flask, request, Response
import json 
import dbcreds
import random
import string
import datetime
from flask_cors import CORS

def createLoginToken():
    letters = string.ascii_letters
    token_result = ''.join(random.choice(letters) for i in range(20))
    return token_result

app = Flask(__name__)
CORS(app)

###################### USERS END POINT ######################
@app.route('/api/users', methods=['GET','POST','PATCH','DELETE'])
def users():
    if request.method == 'GET':
        conn = None
        cursor = None
        users = None
        user_id = request.args.get("userId")
    
        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, user=dbcreds.user, port=dbcreds.port, database=dbcreds.database)
            cursor = conn.cursor()
            if(user_id == None):
                cursor.execute("SELECT * FROM user")
                users = cursor.fetchall()
            else: 
                cursor.execute("SELECT * FROM user WHERE userId=?",[user_id,])
                users = cursor.fetchall()
           
        except Exception as error:
            print("Something went wrong (this is lazy): ")
            print(error)
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if(users != None):
                return Response(json.dumps(users, default=str), mimetype="application/json", status=200)
            else: 
                return Response("Something went wrong!", mimetype="text/html", status=500)

    elif request.method == 'POST':
        conn = None
        cursor = None
        user_username = request.json.get("username")
        user_email = request.json.get("email")
        user_bio = request.json.get("bio")
        user_password = request.json.get("password")
        user_birthdate = request.json.get("birthdate")
        rows = None

        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, user=dbcreds.user, port=dbcreds.port, database=dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO user(username,email,bio,password,birthdate) VALUES (?,?,?,?,?)", [user_username,user_email,user_bio,user_password,user_birthdate,])
            rows = cursor.rowcount
            
            if(rows == 1):
                token_result = createLoginToken()
                userId = cursor.lastrowid
                cursor.execute("INSERT INTO user_session(loginToken,userId) VALUES (?,?)", [token_result, userId,])
                conn.commit()
                rows = cursor.rowcount

        except Exception as error:
            print("Something went wrong: ")
            print(error)
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if(rows == 1):
                user_information = {
                    "userId": userId,
                    "email":  user_email,
                    "username": user_username,
                    "bio": user_bio,
                    "birthdate": user_birthdate,
                    "loginToken": token_result,
                }
                return Response(json.dumps(user_information, default=str), mimetype="application/json", status=201)
            else:
                return Response("Something went wrong!", mimetype="text/html", status=500)

    
    elif request.method == 'PATCH':
        conn = None
        cursor = None
        user_username = request.json.get("username")
        user_email = request.json.get("email")
        user_bio = request.json.get("bio")
        user_password = request.json.get("password")
        user_birthdate = request.json.get("birthdate")
        user_logintoken = request.json.get("loginToken")
        rows = None

        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, user=dbcreds.user, port=dbcreds.port, database=dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT userId FROM user_session WHERE loginToken=?",[user_logintoken,])
            user = cursor.fetchone()
            
            if user_username != "" and user_username != None:
                cursor.execute("UPDATE user SET username=? WHERE userId=?", [user_username,user[0],])
            if user_email != "" and user_email != None:
                cursor.execute("UPDATE user SET email=? WHERE userId=?", [user_email,user[0],])
            if user_bio != "" and user_bio != None:
                cursor.execute("UPDATE user SET bio=? WHERE userId=?", [user_bio,user[0],])
            if user_password != "" and user_password != None:
                cursor.execute("UPDATE user SET password=? WHERE userId=?", [user_password,user[0],])
            if user_birthdate != "" and user_birthdate != None:
                cursor.execute("UPDATE user SET birthdate=? WHERE userId=?", [user_birthdate,user[0],])
            conn.commit()
            rows = cursor.rowcount
            print(rows)
            cursor.execute("SELECT * FROM user WHERE userId=?", [user[0],])
            user = cursor.fetchone()

           
        except Exception as error:
            print("Something went wrong: ")
            print(error)
        finally:
            if cursor != None:
                cursor.close()
            if conn != None:
                conn.rollback()
                conn.close()
            if(rows == 1):
                user_information = {
                    "userId": user[5],
                    "email": user[1],
                    "username": user[0],
                    "bio": user[2],
                    "birthdate": user[3]
                }
                return Response(json.dumps(user_information, default=str), mimetype="application/json", status=200)
            else:
                return Response("Updating User Failed", mimetype="text/html", status=500)

    
    elif request.method == 'DELETE':
        conn = None
        cursor = None
        user_password = request.json.get("password")
        user_logintoken = request.json.get("loginToken")
        rows = None

        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, user=dbcreds.user, port=dbcreds.port, database=dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT userId FROM user_session WHERE loginToken=?",[user_logintoken,])
            user = cursor.fetchone()
            cursor.execute("DELETE FROM user WHERE password=? AND userId=?",[user_password,user[0],])
            conn.commit()
            rows = cursor.rowcount

        except Exception as error:
            print("Something went wrong: ")
            print(error)
        finally:
            if cursor != None:
                cursor.close()
            if conn != None:
                conn.rollback()
                conn.close()
            if(rows == 1):
                return Response("Deleted User Successfully!", mimetype="text/html", status=204)
            else:
                return Response("Deleting User Failed", mimetype="text/html", status=500)

###################### LOGIN END POINT ######################
@app.route('/api/login', methods=['POST','DELETE'])
def login():
    if request.method == 'POST':
        conn = None
        cursor = None
        rows = None
        user = None
        user_email = request.json.get("email")
        user_password = request.json.get("password")
        token_result = createLoginToken()
        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, user=dbcreds.user, port=dbcreds.port, database=dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT userId, email, password FROM user WHERE email=? AND password=?",[user_email,user_password,])
            user = cursor.fetchall()
            if(len(user) == 1):
                cursor.execute("INSERT INTO user_session(loginToken, userId) VALUES(?,?)", [token_result,user[0][0]])
                conn.commit()
                rows = cursor.rowcount
        
        except Exception as error:
            print("Something went wrong: ")
            print(error)
        finally:
            if cursor != None:
                cursor.close()
            if conn != None:
                conn.rollback()
                conn.close()
            if(rows == 1):
                return Response(json.dumps(user, default=str), mimetype="application/json", status=204)
            else:
                return Response("Login User Failed.", mimetype="text/html", status=500)

    if request.method == 'DELETE':
        conn = None
        cursor = None
        rows = None
        user = None
        user_loginToken = request.json.get("loginToken")
        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, user=dbcreds.user, port=dbcreds.port, database=dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_session WHERE loginToken=?",[user_loginToken,])
            conn.commit()
            rows = cursor.rowcount
            print(rows)

        except Exception as error:
            print("Something went wrong: ")
            print(error)
        finally:
            if cursor != None:
                cursor.close()
            if conn != None:
                conn.rollback()
                conn.close()
            if(rows == 1):
                return Response("Logged Out Succesfully!", mimetype="text/html", status=204)
            else:
                return Response("Logging Out Failed.", mimetype="text/html", status=500)

###################### TWEETS END POINT ######################
@app.route('/api/tweets', methods=['GET','POST','PATCH','DELETE'])
def tweets():
    if request.method == 'GET':
        conn = None
        cursor = None
        tweets = None
        user_id = request.args.get("userId")
    
        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, user=dbcreds.user, port=dbcreds.port, database=dbcreds.database)
            cursor = conn.cursor()
            if(user_id == None):
                cursor.execute("SELECT * FROM tweet")
                tweets = cursor.fetchall()
            else: 
                cursor.execute("SELECT * FROM tweet WHERE userId=?",[user_id,])
                tweets = cursor.fetchall()
           
        except Exception as error:
            print("Something went wrong: ")
            print(error)
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if(users != None):
                return Response(json.dumps(tweets, default=str), mimetype="application/json", status=200)
            else: 
                return Response("Something went wrong!", mimetype="text/html", status=500)
    
    elif request.method == 'POST':
        conn = None
        cursor = None
        tweet_content = request.json.get("content")
        login_token = request.json.get("loginToken")
        createdAt = datetime.datetime.now().strftime("%Y-%m-%d")
        rows = None

        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, user=dbcreds.user, port=dbcreds.port, database=dbcreds.database)
            cursor = conn.cursor() 
            cursor.execute("SELECT us.userId, u.username FROM user_session us INNER JOIN user u ON us.userId=u.userId WHERE loginToken=?",[login_token,])
            user = cursor.fetchone()
            cursor.execute("INSERT INTO tweet(content,userId) VALUES (?,?)", [tweet_content,user[0],])
            conn.commit()
            rows = cursor.rowcount
            tweetId = cursor.lastrowid

        except Exception as error:
            print("Something went wrong: ")
            print(error)
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if(rows == 1):
                tweet_information = {
                    "content": tweet_content,
                    "createdAt": createdAt,
                    "username": user[1],
                    "userId": user[0],
                    "tweetId": tweetId,
                }
                return Response(json.dumps(tweet_information, default=str), mimetype="application/json", status=201)
            else:
                return Response("Something went wrong!", mimetype="text/html", status=500)

    elif request.method == 'PATCH':
        conn = None
        cursor = None
        tweet_content = request.json.get("content")
        login_token = request.json.get("loginToken")
        tweet_id = request.json.get("tweetId")
        rows = None

        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, user=dbcreds.user, port=dbcreds.port, database=dbcreds.database)
            cursor = conn.cursor() 
            cursor.execute("SELECT userId FROM user_session WHERE loginToken=?", [login_token,])
            user = cursor.fetchall()[0][0]
            cursor.execute("SELECT userId FROM tweet WHERE tweetId=?", [tweet_id,])
            tweet_owner = cursor.fetchall()[0][0]
            if(user == tweet_owner):
                cursor.execute("UPDATE tweet SET content=? WHERE tweetId=?", [tweet_content,tweet_id,])
                conn.commit()
                rows = cursor.rowcount
                tweetId = cursor.lastrowid
            else:
                print("Unable to update tweet")

        except Exception as error:
            print("Something went wrong: ")
            print(error)
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if(rows == 1):
                tweet_information = {
                    "tweetId": tweet_id,
                    "content": tweet_content,
                }
                return Response(json.dumps(tweet_information, default=str), mimetype="application/json", status=200)
            else:
                return Response("Something went wrong!", mimetype="text/html", status=500)


    elif request.method == 'DELETE':
        conn = None
        cursor = None
        login_token = request.json.get("loginToken")
        tweet_id = request.json.get("tweetId")
        rows = None

        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, user=dbcreds.user, port=dbcreds.port, database=dbcreds.database)
            cursor = conn.cursor() 
            cursor.execute("SELECT userId FROM user_session WHERE loginToken=?", [login_token,])
            user = cursor.fetchall()[0][0]
            cursor.execute("SELECT userId FROM tweet WHERE tweetId=?", [tweet_id,])
            tweet_owner = cursor.fetchall()[0][0]
            if(user == tweet_owner):
                cursor.execute("DELETE FROM tweet WHERE tweetId=?", [tweet_id,])
                conn.commit()
                rows = cursor.rowcount
                tweetId = cursor.lastrowid
            else:
                print("Unable to delete tweet.")

        except Exception as error:
            print("Something went wrong: ")
            print(error)
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if(rows == 1):
                return Response("Tweet Deleted Succesfully!", mimetype="text/html", status=204)
            else:
                return Response("Tweet not Deleted!", mimetype="text/html", status=500)






 
    
    