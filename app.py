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
                users_info = []
                for user in users:
                    users_info.append({
                        "userId": user[5],
                        "email": user[1],
                        "username": user[0],
                        "bio": user[2],
                        "birthdate": user[4],})

                return Response(json.dumps(users_info, default=str), mimetype="application/json", status=200)
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
            cursor.execute("SELECT userId, email, password, bio, birthdate, username FROM user WHERE email=? AND password=?",[user_email,user_password,])
            user = cursor.fetchall()
        
            if(len(user) == 1):
                cursor.execute("INSERT INTO user_session(loginToken, userId) VALUES(?,?)", [token_result,user[0][0],])
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
                user_info = {
                    "userId": user[0][0],
                    "email": user[0][1],
                    "username": user[0][5],
                    "bio": user[0][3],
                    "birthdate": user[0][4],
                    "loginToken": token_result,
                }
                return Response(json.dumps(user_info, default=str), mimetype="application/json", status=201)
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
                cursor.execute("SELECT user.username, t.content, t.createdAt, t.tweetId, t.userId FROM user INNER JOIN tweet t ON user.userId=t.userId")
                tweets = cursor.fetchall()
                print(tweets)
            else: 
                cursor.execute("SELECT user.username, t.content, t.createdAt, t.tweetId, t.userId FROM user INNER JOIN tweet t ON user.userId=t.userId WHERE user.userId=?", [user_id,])
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
            if(tweets != None):
                tweets_info = []
                for tweet in tweets:
                    tweets_info.append({
                        "tweetId": tweet[3],
                        "userId": tweet[4],
                        "username": tweet[0],
                        "content": tweet[1],
                        "createdAt": tweet[2],
                        })
                return Response(json.dumps(tweets_info, default=str), mimetype="application/json", status=200)
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

###################### TWEET LIKES END POINT ######################

@app.route('/api/tweet-likes', methods=['GET','POST','DELETE'])
def tweetlikes():
    if request.method == 'GET':
        conn = None
        cursor = None
        tweet_likes = None
        tweet_id = request.args.get("tweetId")

        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, user=dbcreds.user, port=dbcreds.port, database=dbcreds.database)
            cursor = conn.cursor()
            if(tweet_id == None):
                cursor.execute("SELECT u.username, u.userId, tl.tweetId FROM user u INNER JOIN tweet_like tl ON u.userId=tl.userId")
                tweet_likes = cursor.fetchall()
            else:
                cursor.execute("SELECT u.username, u.userId, tl.tweetId FROM user u INNER JOIN tweet_like tl ON u.userId=tl.userId WHERE tl.tweetId=?", [tweet_id,])
                tweet_likes = cursor.fetchall()
 
        except Exception as error:
            print("Something went wrong: ")
            print(error)
        
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if(tweet_likes != None):
                tweetlike_info = []
                for tweet_like in tweet_likes:
                    tweetlike_info.append({
                        "tweetId": tweet_like[2],
                        "userId": tweet_like[1],
                        "username": tweet_like[0],
                        })
                return Response(json.dumps(tweetlike_info, default=str), mimetype="application/json", status=200)
            else: 
                return Response("Something went wrong!", mimetype="text/html", status=500)

    elif request.method == 'POST':
        conn = None
        cursor = None
        tweet_id = request.json.get("tweetId")
        login_token = request.json.get("loginToken")
        rows = None

        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, user=dbcreds.user, port=dbcreds.port, database=dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT userId from user_session WHERE loginToken=?", [login_token,])
            user = cursor.fetchone()
            cursor.execute("SELECT username FROM user WHERE userId=?", [user[0],])
            username = cursor.fetchone()
            cursor.execute("INSERT INTO tweet_like(tweetId,userId) VALUES (?,?)", [tweet_id,user[0],])
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
                return Response("Liked Tweet!", mimetype="text/html", status=201)
            else:
                return Response("Something went wrong!", mimetype="text/html", status=500)
    
    elif request.method == 'DELETE':
        conn = None
        cursor = None
        tweet_id = request.json.get("tweetId")
        login_token = request.json.get("loginToken")
        rows = None

        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, user=dbcreds.user, port=dbcreds.port, database=dbcreds.database)
            cursor = conn.cursor() 
            cursor.execute("SELECT us.userId FROM user_session us INNER JOIN tweet_like tl ON us.userId=tl.userId WHERE loginToken=?",[login_token,])
            user = cursor.fetchone()
            cursor.execute("DELETE FROM tweet_like WHERE tweetId=? AND userId=?", [tweet_id,user[0],])
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
                return Response("Tweet like removed successfully!", mimetype="text/html", status=204)
            else:
                return Response("Something went wrong!", mimetype="text/html", status=500)
    
###################### FOLLOWS END POINT ######################

@app.route('/api/follows', methods=['GET','POST','DELETE'])
def follows():
    if request.method == 'GET':
        conn = None
        cursor = None
        follows = None
        user_id = request.args.get("userId")
        
        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, user=dbcreds.user, port=dbcreds.port, database=dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT user.userId, user.email, user.username, user.bio, user.birthdate FROM user INNER JOIN follow ON user.userId=follow.userId WHERE follow.followId=?",[user_id,])
            follows = cursor.fetchall()
            print(follows)

        except Exception as error:
            print("Something went wrong: ")
            print(error)
            
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if(follows != None):
                follow_info = []
                for follow in follows:
                    follow_info.append({
                        "userId": follow[0],
                        "email": follow[1],
                        "username": follow[2],
                        "bio": follow[3],
                        "birthdate": follow[4],
                        })

                return Response(json.dumps(follow_info, default=str), mimetype="application/json", status=200)
            else: 
                return Response("Something went wrong!", mimetype="text/html", status=500)
    
    elif request.method == 'POST':
        conn = None
        cursor = None
        login_token = request.json.get("loginToken")
        follow_id = request.json.get("followId")
        user_id = None
        rows = None

        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, user=dbcreds.user, port=dbcreds.port, database=dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT u.userId FROM user u INNER JOIN user_session us ON u.userId=us.userId WHERE loginToken=?",[login_token,])
            user_id = cursor.fetchall()[0][0]
            cursor.execute("INSERT INTO follow(userId,followId) VALUES(?,?)",[user_id,follow_id,])
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
                return Response("Followed user succesfully!", mimetype="text/html", status=204)
            else:
                return Response("Something went wrong!", mimetype="text/html", status=500)
    
    elif request.method == 'DELETE':
        conn = None
        cursor = None
        login_token = request.json.get("loginToken")
        follow_id = request.json.get("followId")
        user_id = None
        rows = None

        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, user=dbcreds.user, port=dbcreds.port, database=dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT us.userId FROM user_session us WHERE us.loginToken=?",[login_token,])
            user_id = cursor.fetchall()[0][0]
            cursor.execute("DELETE FROM follow WHERE followId=? AND userId=?",[follow_id,user_id,])
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
                return Response("Deleted follow succesfully!", mimetype="text/html", status=204)
            else:
                return Response("Something went wrong!", mimetype="text/html", status=500)

###################### FOLLOWERS END POINT ######################

@app.route('/api/followers', methods=['GET'])
def followers():
    if request.method == 'GET':
        conn = None
        cursor = None
        follows = None
        user_id = request.args.get("userId")
        
        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, user=dbcreds.user, port=dbcreds.port, database=dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT user.userId, user.email, user.username, user.bio, user.birthdate FROM user INNER JOIN follow ON user.userId=follow.followId WHERE follow.userId=?",[user_id,])
            follows = cursor.fetchall()
            print(follows)

        except Exception as error:
            print("Something went wrong: ")
            print(error)
            
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if(follows != None):
                follow_info = []
                for follow in follows:
                    follow_info.append({
                        "userId": follow[0],
                        "email": follow[1],
                        "username": follow[2],
                        "bio": follow[3],
                        "birthdate": follow[4],
                        })

                return Response(json.dumps(follow_info, default=str), mimetype="application/json", status=200)
            else: 
                return Response("Something went wrong!", mimetype="text/html", status=500)

###################### COMMENTS END POINT ######################

@app.route('/api/comments', methods=['GET','POST','PATCH','DELETE'])
def comments():
    if request.method == 'GET':
        conn = None
        cursor = None
        tweet_id = request.args.get("tweetId")
        comments = None
    
        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, user=dbcreds.user, port=dbcreds.port, database=dbcreds.database)
            cursor = conn.cursor()
            if(tweet_id == None):
                cursor.execute("SELECT user.username, c.commentId, c.content, c.createdAt, c.tweetId, c.userId FROM user INNER JOIN comment c ON user.userId=c.userId")
                comments = cursor.fetchall()
            else: 
                cursor.execute("SELECT user.username, c.commentId, c.content, c.createdAt, c.tweetId, c.userId FROM user INNER JOIN comment c ON user.userId=c.userId WHERE c.tweetId=?", [tweet_id,])
                comments = cursor.fetchall()
           
        except Exception as error:
            print("Something went wrong: ")
            print(error)
        
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if(comments != None):
                comments_info = []
                for comment in comments:
                    comments_info.append({
                        "commentId": comment[1],
                        "tweetId": comment[4],
                        "userId": comment[5],
                        "username": comment[0],
                        "content": comment[2],
                        "createdAt": comment[3]
                        })
                return Response(json.dumps(comments_info, default=str), mimetype="application/json", status=200)
            else: 
                return Response("Something went wrong!", mimetype="text/html", status=500)
                
    elif request.method == 'POST':
        conn = None
        cursor = None
        comment_content = request.json.get("content")
        tweet_id = request.json.get("tweetId")
        login_token = request.json.get("loginToken")
        createdAt = datetime.datetime.now().strftime("%Y-%m-%d")
        rows = None

        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, user=dbcreds.user, port=dbcreds.port, database=dbcreds.database)
            cursor = conn.cursor() 
            cursor.execute("SELECT us.userId, u.username FROM user_session us INNER JOIN user u ON us.userId=u.userId WHERE loginToken=?",[login_token,])
            user = cursor.fetchone()
            cursor.execute("INSERT INTO comment(content,tweetId,userId) VALUES (?,?,?)", [comment_content,tweet_id,user[0]])
            conn.commit()
            rows = cursor.rowcount
            commentId = cursor.lastrowid

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
                comment_information = {
                    "commentId": commentId,
                    "tweetId": tweet_id,
                    "userId": user[0],
                    "username": user[1],
                    "content": comment_content,
                    "createdAt": createdAt,
                }
                return Response(json.dumps(comment_information, default=str), mimetype="application/json", status=201)
            else:
                return Response("Something went wrong!", mimetype="text/html", status=500)
    
    elif request.method == 'PATCH':
        conn = None
        cursor = None
        comment_content = request.json.get("content")
        login_token = request.json.get("loginToken")
        comment_id = request.json.get("commentId")
        rows = None

        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, user=dbcreds.user, port=dbcreds.port, database=dbcreds.database)
            cursor = conn.cursor() 
            cursor.execute("SELECT u.userId, u.username FROM user u INNER JOIN user_session us ON us.userId=u.userId WHERE loginToken=?", [login_token,])
            user = cursor.fetchall()[0][0]
            cursor.execute("SELECT userId FROM comment WHERE commentId=?", [comment_id,])
            comment_owner = cursor.fetchall()[0][0]
            if(user == comment_owner):
                cursor.execute("SELECT u.username, c.tweetId, c.userId, c.createdAt FROM user u INNER JOIN comment c ON u.userId=c.userId")
                owner = cursor.fetchone()
                cursor.execute("UPDATE comment SET content=? WHERE commentId=?", [comment_content,comment_id,])
                conn.commit()
                rows = cursor.rowcount
            else:
                print("Unable to update comment.")

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
                comment_information = {
                    "commentId": comment_id,
                    "tweetId": owner[1],
                    "userId": owner[2],
                    "username": owner[0],
                    "content": comment_content,
                    "createdAt": owner[3] ,
                }
                return Response(json.dumps(comment_information, default=str), mimetype="application/json", status=200)
            else:
                return Response("Something went wrong!", mimetype="text/html", status=500)

    elif request.method == 'DELETE':
        conn = None
        cursor = None
        login_token = request.json.get("loginToken")
        comment_id = request.json.get("commentId")
        rows = None

        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, user=dbcreds.user, port=dbcreds.port, database=dbcreds.database)
            cursor = conn.cursor() 
            cursor.execute("SELECT u.userId, u.username FROM user u INNER JOIN user_session us ON us.userId=u.userId WHERE loginToken=?", [login_token,])
            user = cursor.fetchall()[0][0]
            cursor.execute("SELECT userId FROM comment WHERE commentId=?", [comment_id,])
            comment_owner = cursor.fetchall()[0][0]
            if(user == comment_owner):
                cursor.execute("DELETE FROM comment WHERE commentId=?", [comment_id,])
                conn.commit()
                rows = cursor.rowcount
            else:
                print("Unable to delete comment.")

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
                return Response("Comment Deleted Succesfully!", mimetype="text/html", status=204)
            else:
                return Response("Comment not Deleted!", mimetype="text/html", status=500)

###################### COMMENT LIKES END POINT ######################

@app.route('/api/comment-likes', methods=['GET','POST','DELETE'])
def commentlikes():
    if request.method == 'GET':
        conn = None
        cursor = None
        comment_likes = None
        comment_id = request.args.get("commentId")

        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, user=dbcreds.user, port=dbcreds.port, database=dbcreds.database)
            cursor = conn.cursor()
            if(comment_id == None):
                cursor.execute("SELECT u.username, u.userId, cl.commentId FROM user u INNER JOIN comment_like cl ON u.userId=cl.userId")
                comment_likes = cursor.fetchall()
            else:
                cursor.execute("SELECT u.username, u.userId, cl.commentId FROM user u INNER JOIN comment_like cl ON u.userId=cl.userId WHERE cl.commentId=?", [comment_id,])
                comment_likes = cursor.fetchall()

        except Exception as error:
            print("Something went wrong: ")
            print(error)
        
        finally:
            if(cursor != None):
                cursor.close()
            if(conn != None):
                conn.rollback()
                conn.close()
            if(comment_likes != None):
                commentlike_info = []
                for comment_like in comment_likes:
                    commentlike_info.append({
                        "commentId": comment_like[2],
                        "userId": comment_like[1],
                        "username": comment_like[0],
                        })
                return Response(json.dumps(commentlike_info, default=str), mimetype="application/json", status=200)
            else: 
                return Response("Something went wrong!", mimetype="text/html", status=500)

    elif request.method == 'POST':
        conn = None
        cursor = None
        comment_id = request.json.get("commentId")
        login_token = request.json.get("loginToken")
        rows = None

        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, user=dbcreds.user, port=dbcreds.port, database=dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT userId from user_session WHERE loginToken=?", [login_token,])
            user = cursor.fetchone()
            cursor.execute("SELECT username FROM user WHERE userId=?", [user[0],])
            username = cursor.fetchone()
            cursor.execute("INSERT INTO comment_like(commentId,userId) VALUES (?,?)", [comment_id,user[0],])
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
                commentlike_information = {
                    "commentId": comment_id,
                    "userId": user[0],
                    "username": username[0],
                }
                return Response(json.dumps(commentlike_information, default=str), mimetype="application/json", status=201)
            else:
                return Response("Something went wrong!", mimetype="text/html", status=500)

    elif request.method == 'DELETE':
        conn = None
        cursor = None
        comment_id = request.json.get("commentId")
        login_token = request.json.get("loginToken")
        rows = None

        try:
            conn = mariadb.connect(host=dbcreds.host, password=dbcreds.password, user=dbcreds.user, port=dbcreds.port, database=dbcreds.database)
            cursor = conn.cursor()
            cursor.execute("SELECT us.userId FROM user_session us INNER JOIN comment_like cl ON us.userId=cl.userId WHERE loginToken=?",[login_token,])
            user = cursor.fetchone()
            cursor.execute("DELETE FROM comment_like WHERE commentId=? AND userId=?", [comment_id,user[0],])
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
                return Response("Comment like removed successfully!", mimetype="text/html", status=204)
            else:
                return Response("Something went wrong!", mimetype="text/html", status=500)