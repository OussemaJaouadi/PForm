from base64 import b64encode
from functools import wraps
from flask import abort, render_template, request, redirect, url_for
import jwt
import os
from dotenv import load_dotenv
import jwt
import os

load_dotenv()
SECRET_KEY = os.getenv('SECRET').strip()
SECRET_KEY = b64encode(SECRET_KEY.encode()).decode()
PORT=os.getenv('PORT')

def gen_token(username,role='student'):
    if role not in ['student','teacher','admin']:
        role = 'student'
    payload = {
        'sub': username,
        'role': role
    }
    secret = SECRET_KEY
    token = jwt.encode(payload, secret, algorithm='HS256')
    return token

def get_user_from_token():
    token = request.cookies.get('token')
    if not token:
        return None, None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        username = payload['sub']
        role = payload['role']
        return username, role
    except jwt.ExpiredSignatureError:
        return None, None
    except jwt.InvalidTokenError:
        return None, None

def require_role(role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user,userRole = get_user_from_token()
            if not user :
                return render_template("error.html",code="401",message="You have to login first")
            elif userRole in role :
                #print(userRole)
                return func(*args, **kwargs)
            else:
                return render_template("error.html",code="403",message="You don't have the privilege")  # Access forbidden
        return wrapper
    return decorator