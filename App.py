from flask import Flask, render_template, request, json

from flaskext.mysql import MySQL
from flask_login import LoginManager , login_user , logout_user , current_user , login_required
from werkzeug import generate_password_hash, check_password_hash
from user import User
app = Flask(__name__)

mysql = MySQL()
login_manager = LoginManager()

# MySQL configurations

app.secret_key = "super secret key"
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'ASAFrontend'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_TABLE'] = 'tbl_user'
mysql.init_app(app)

# LoginManager configurations
login_manager.init_app(app)

@app.route("/")
def main():
    return render_template('index.html')

@app.route("/showSignUp")
def showSignUp():
    return render_template('signUp.html')

@app.route("/showSignIn")
def showSignIn():
    return render_template('signIn.html')


@app.route('/signUp', methods=['POST', 'GET'])
def signUp():
    try:
        _name = request.form['inputName']
        _email = request.form['inputEmail']
        _password = request.form['inputPassword']
        conn = mysql.connect()
        cursor = conn.cursor()
        if _name and _email and _password:
            _hashed_password = generate_password_hash(_password)
            cursor.callproc('createUser', (_name, _email, _hashed_password))
            data = cursor.fetchall()

            if len(data) is 0:
                conn.commit()
                return json.dumps({'message': 'User created successfully !'})
            else:
                return json.dumps({'error': str(data[0])})
        else:
            return json.dumps({'html': '<span>Enter the required fields</span>'})

    except Exception as e:
        return json.dumps({'error': str(e)})
    finally:
        cursor.close()
        conn.close()


@app.route('/signIn', methods=['POST', 'GET'])
def signIn():
    try:
        _email = request.form['inputEmail']
        _password = request.form['inputPassword']

        conn = mysql.connect()
        cursor = conn.cursor()
        if _email and _password:
            cursor.execute("SELECT * from "+app.config['MYSQL_DATABASE_DB']+"."+app.config['MYSQL_DATABASE_TABLE']+" where user_username='" + _email + "'")
            data = cursor.fetchone()
            password_match = check_password_hash(data[3],str(_password))
            print(password_match)
            if data is not None and password_match:
                user = User(data[1], str(data[0]))
                login_user(user)
                return json.dumps({'message': "Logged in successfully: " +str(data[0])})

            else:
                conn.commit()
                return json.dumps({'error': 'Username or Password is wrong'})
        else:
            return json.dumps({'html': '<span>Enter the required fields</span>'})

    except Exception as e:
        return json.dumps({'error': str(e)})
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    app.run()