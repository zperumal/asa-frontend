from flask import Flask, session,  redirect, render_template,url_for, send_file, request, json


import os
from queue import Queue
import threading, time, datetime
import re , sys

from threading import Thread
from flaskext.mysql import MySQL
from flask_login import LoginManager , login_user , logout_user , current_user , login_required
from werkzeug import generate_password_hash, check_password_hash, secure_filename
from user import User
from utils import  zip_dir ,zip_name
from ASARunner import run, run_sampler
from OutputTable import OutputTable
app = Flask(__name__)

mysql = MySQL()
login_manager = LoginManager()

UPLOAD_FOLDER = './uploaded_data'
ALLOWED_EXTENSIONS = 'csv'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
DATA_DIR = "./static/data/aec_2016_data"
OUTPUT_DIR = "./static/data/output_data"


# MySQL configurations

app.secret_key = "super secret key"
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'ASAFrontend'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_TABLE'] = 'tbl_user'
app.config['MYSQL_OUTPUT_TABLE'] = 'output_data'
mysql.init_app(app)

# LoginManager configurations
login_manager.init_app(app)

# global variables
currentJobId = 0
lastJobId = 0
completed_jobs = []
select_regex = re.compile("Job ID:(\d+)")
# Threading
run_queue = Queue()
currentJobLock = threading.Lock()
auditThread = threading.Thread()

@app.route("/")
def main():
    return render_template('index.html')

#Account routes
@app.route("/showSignUp")
def showSignUp():
    return render_template('signUp.html')

@app.route("/showSignIn")
def showSignIn():
    return render_template('signIn.html')


@app.route("/showUserPortal")
def showUserPortal():
    if 'inputEmail' in session:
        if 'user_id' in session:
            n_jobs_completed = len(getJobsForID(user_id=session['user_id'], job_type='audit', status="'completed'"))
            n_jobs_submitted= len(getJobsForID(user_id=session['user_id'], job_type='audit', status="'submitted'"))
            audit_data = getJobsForID(user_id=session['user_id'], job_type='audit')
            sampler_data = getJobsForID(user_id=session['user_id'], job_type='sampler')
        return render_template('user_portal.html', dashboardHeader="Job Dashboard: "+str(session['inputEmail'])  , jobs_completed=n_jobs_completed, jobs_running=n_jobs_submitted,auditData=audit_data, samplerData=sampler_data)
    return redirect(url_for(''))

@app.route('/signUp', methods=['POST', 'GET'])
def signUp():
    conn = mysql.connect()
    cursor = conn.cursor()
    try:
        _name = request.form['inputName']
        _email = request.form['inputEmail']
        _password = request.form['inputPassword']
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
    conn = mysql.connect()
    cursor = conn.cursor()
    try:
        _email = request.form['inputEmail']
        _password = request.form['inputPassword']

        if _email and _password:
            cursor.execute("SELECT * from "+app.config['MYSQL_DATABASE_DB']+"."+app.config['MYSQL_DATABASE_TABLE']+" where user_username='" + _email + "'")
            data = cursor.fetchone()
            password_match = check_password_hash(data[3],str(_password))
            print(password_match)
            if data is not None and password_match:
                user = User(data[1], str(data[0]))
                login_user(user)
                session['inputEmail'] = user.name
                session['user_id'] = user.id
                #return json.dumps({'message': "Logged in successfully: " })
                return redirect(url_for('showUserPortal'))

            else:
                conn.commit()
                return json.dumps({'error': 'Username or Password is wrong'})
        else:
            return json.dumps({'html': '<span>Enter the required fields</span>'})

    except Exception as e:
        print(str(e))
        return json.dumps({'error': str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('inputEmail', None)
    return redirect(url_for('main'))


@login_manager.user_loader
def load_user(userid):
    conn = mysql.connect()
    cursor = conn.cursor()
    try:
        if userid :
            cursor.execute("SELECT * from "+app.config['MYSQL_DATABASE_DB']+"."+app.config['MYSQL_DATABASE_TABLE']+" where user_id='" + userid + "'")
            data = cursor.fetchone()
            if data is not None:
                user = User(data[1], str(data[0]))
                return user

    except Exception as e:
        print(str(e))
        return
    finally:
        cursor.close()
        conn.close()


#Job Routes
@app.route("/showRunAuditJob", methods=['GET'])
def showRunAuditJob():
    sampler_data = getJobsForID(user_id=session['user_id'], job_type='sampler', short_columns=False)
    return render_template('runAuditJob.html', samplerNames= sampler_data)

@app.route("/showRunSamplerJob", methods=['GET'])
def showRunSamplerJob():
    audit_data = getJobsForID(user_id=session['user_id'], job_type='audit' , short_columns=False)
    return render_template('runSamplerJob.html', auditNames= audit_data)


@app.route("/addSamplerJob", methods=['POST'])
def addSamplerJob():
    global currentJobLock
    global lastJobId
    with currentJobLock:
        request.get_data()
        config = request.form.to_dict()
        lastJobId =getMaxJobID() + 1
        print("Audit type: " + str(config['audit_type']) )
        print("Audit config: " + str(config) )



        print("Config: "+str(config))
        config['job_id'] = lastJobId
        config['user_id'] = session['user_id']
        config['status'] = 'submitted'

        if config['audit_type'] == 'existing_audit':
            (rounds , ballots,  auditJob) = config['auditJob'].split(",")
            config['data_dir'] =  auditJob
            print("New config: " + str(config))
            save_output(config,  rounds=rounds, ballots=ballots, data=auditJob )
        else:
            save_output(config)
        run_queue.put(config)
        print( "Job submitted with ID: %d" % lastJobId)
        return redirect(url_for('showUserPortal'))

@app.route("/addJob", methods=['POST'])
def addJob():
    global currentJobLock
    global lastJobId
    with currentJobLock:
        request.get_data()
        config = request.form.to_dict()
        lastJobId =getMaxJobID() + 1
        config['job_id'] = lastJobId
        print("Sampler config: " + str(config) )

        # check if the post request has the file part
        if 'ballotsToUpload' not in request.files:
            return redirect(request.url)
        file = request.files['ballotsToUpload']
        print("File: " + str(file))
        uploadFileName = ""
        print("Config: " +str(config))
        config['user_id'] = session['user_id']
        config['status'] = 'submitted'

        if config['ballot_type'] == 'upload_ballots':
            print("Config sampler job: " + str( config['samplerJob']))
            sjString = config['samplerJob']
            print(sjString)
            shortened = sjString[1:-1]
            print(shortened)
            (seed, increment, rounds, ballots, samplerJob) = shortened.split(",")
            rounds = rounds.strip().strip()[1:-1]
            ballots = ballots.strip().strip()[1:-1]
            samplerJob = samplerJob.strip()[1:-1]
            seed = seed.strip()[1:-1]
            increment = increment.strip()[1:-1]
            config['seed'] = seed
            config['incrementSize'] = increment
            print("Rounds: " + str(rounds))
            print("SamplerJob: " + str(samplerJob.strip()))
            config['data_dir'] =  samplerJob
            uploadFileName = os.path.join(OUTPUT_DIR ,  samplerJob , "sample_ballots.csv") #"rounds/round_"+rounds+".csv")

            print("Config: "+str(config))
            if file.filename != '' and file and allowed_file(file.filename):
                print("Upload filename: " + str(uploadFileName))
                filename =  secure_filename(file.filename) if uploadFileName == "" else uploadFileName
                print("Using filename: " + str(filename))
                #TODO: (zperumal) rename file
                file.save(uploadFileName)
                config['file'] = uploadFileName
            save_output(config, rounds=rounds, ballots=ballots, data=samplerJob)
        else:
            save_output(config)
        run_queue.put(config)
        print( "Job submitted with ID: %d" % lastJobId)
        return redirect(url_for('showUserPortal'))

def empty_queue():
    global current_job_id
    global completed_jobs
    while True:
        config = run_queue.get()
        #config = getNextJob()
        print("EMPTY QUEUE CONFIG: " + str(config))
        if config is not None:
            current_job_id = config['job_id']
            try:
                if config['type'] == 'audit':
                    print("%s Queue size is: %d" % (datetime.datetime.now(),
                                                    run_queue.qsize()))
                    print("%s Current job: %d" % (datetime.datetime.now(),
                                                  config['job_id']))
                    if 'data_dir' in config:
                        data_dir = config['data_dir']
                        output_info = run_aus_audit(config,data_dir=os.path.join(OUTPUT_DIR ,  data_dir))
                    else:
                        output_info = run_aus_audit(config)
                    print("EMPTY QUEUE OUTPUT INFO: " + str(output_info))
                    update_job(job_id=current_job_id, status='completed' , rounds=output_info['audit_stage'], ballots=output_info['sample_size'])
                else:
                    print("here")
                    if 'data_dir' in config:
                        print("Data dir")
                        data_dir = config['data_dir']
                        output_info = run_aus_sampler(config,data_dir=os.path.join(OUTPUT_DIR ,  data_dir))
                    else:
                        output_info = run_aus_sampler(config)
                    print("EMPTY QUEUE OUTPUT INFO m: " + str(output_info))
                    update_job(job_id=current_job_id, status='completed' , rounds=output_info['audit_stage'], ballots=output_info['sample_size'])
                #save_output(config, job_id = str(current_job_id), rounds=output_info['audit_stage'], ballots=output_info['sample_size'])
            except:
                print("Unexpected error:", sys.exc_info()[0])
                update_job(job_id=current_job_id,status='ERROR',rounds='', ballots='')
        else:
            time.sleep(0.5)
def save_output(run_config,  rounds='', ballots ='', data=''):
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        _user_id= run_config['user_id']
        _job_id= run_config['job_id']
        _job_name = run_config['name']
        _status = run_config['status']
        _type = run_config['type'] if 'type' in run_config  else ''
        _state = run_config['state'] if 'state' in run_config  else ''
        _seed = run_config['seed'] if 'seed' in run_config  else ''
        _increment = run_config['incrementSize']  if 'incrementSize' in run_config else ''
        _data = data if data != '' else _type+"_"+str(_job_id)
        print("SAVE OUTPUT: " + str((_job_id,_user_id,_job_name, _type,_status, _state,_seed,_increment,  rounds,ballots, _data)))
        cursor.callproc('addJob', (_job_id,_user_id,_job_name, _type,_status, _state,_seed,_increment,  rounds,ballots, _data))
        conn.commit()

    except Exception as e:
        print( "ERROR SAVE OUTPUT: "+str(e))
    finally:
        cursor.close()
        conn.close()

def update_job(job_id='',status='completed', rounds='', ballots =''):
    try:
        conn = mysql.connect()
        cursor = conn.cursor()
        print("Updatejob params: " + str((job_id,status, rounds,ballots )))
        cursor.callproc('updateJob', (job_id,status, rounds,ballots ))
        conn.commit()
    except Exception as e:
        print( "ERROR UPDATE JOB: "+str(e))
    finally:
        cursor.close()
        conn.close()

def run_aus_audit(config, data_dir=''):
    global lastJobId
    print(config)
    lastJobId = config['job_id']
    output_file =  data_dir if data_dir!= '' else OUTPUT_DIR + "/audit_{}".format(lastJobId)
    print("Output file: " + str(output_file))
    if config['ballot_type'] == 'existing_ballots':
        return run( config['state'], data=DATA_DIR, seed = config['seed'],sample_increment = int(config['incrementSize']), output_name=output_file)
    else:
        return run( config['state'], data=DATA_DIR, seed = config['seed'],sample_increment = int(config['incrementSize']), output_name=output_file, selected_ballots=config['file'])

def run_aus_sampler(config, data_dir=''):
    global lastJobId
    lastJobId = config['job_id']
    output_file = data_dir if data_dir!= '' else  OUTPUT_DIR + "/sampler_{}".format(lastJobId)
    print("Output file: " + str(output_file))
    return run_sampler(config['state'], data=DATA_DIR, seed=config['seed'],
                   sample_increment=int(config['incrementSize']), output_name=output_file)


#sql helpers
def getJobsForID(user_id="", job_type="" , job_id="", status="", short_columns = True):
    """SELECT * from ASAFrontend.output_data where user_id='2' AND job_type='audit'"""
    columns = "job_id, user_id, job_name, job_type, status, seed, increment, state, job_data" if job_type=='sampler' and short_columns  else "*"
    query = "SELECT "+columns+" from " + app.config['MYSQL_DATABASE_DB'] + "." + app.config[
        'MYSQL_OUTPUT_TABLE']

    param_dict ={"user_id" : user_id, "job_type":"'"+str(job_type)+"'","job_id":job_id, "status":status}
    param_list = [key+"="+value for key,value in param_dict.items() if value != ""]
    if len(param_list) > 0:
        query += " WHERE "+ " AND ".join(param_list)
    """
    if user_id != "" and job_type !="":
        query += " where user_id='"+user_id+"'" +" AND job_type='" + job_type +"'"
    elif user_id != "":
        query += " where user_id='"+user_id+"'"
    elif job_type != "":
        query += " where job_type='" + job_type +"'"
    """
    print("Query: " + str(query))
    conn = mysql.connect()
    cursor = conn.cursor()
    try:
        print("QUERY: " + str(query))
        cursor.execute(query)
        data = cursor.fetchall()
        print (data)
        return data
    finally:
        cursor.close()
        conn.close()
    return []

def getNextJob():
    job_colum_names = ('job_id','user_id','job_name','job_type','status','state','seed','increment','rounds','ballots','job_data')
    query = "SELECT * from ASAFrontend.output_data WHERE status='submitted' ORDER BY 'job_id' DESC"
    conn = mysql.connect()
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        data = cursor.fetchone()
        print(data)
        return dict(zip(job_colum_names,data))
    finally:
        cursor.close()
        conn.close()
    return None

def getMaxJobID():
    query = "SELECT job_id from ASAFrontend.output_data ORDER BY job_id DESC LIMIT 1;"
    conn = mysql.connect()
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        data = cursor.fetchone()
        return 0 if data is None or len(data) == 0  else int(data[0])
    finally:
        cursor.close()
        conn.close()
    return None
#Utils
@app.route('/uploads/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    path = os.path.join(OUTPUT_DIR, filename)
    if os.path.isdir(path):
        file_zip_name = zip_name(path)
        if not os.path.exists(file_zip_name):
            zip_dir(file_zip_name, path)
        path = file_zip_name
    return send_file(path)

def findIDFromSelectString(string):
    """
    Assumes that the input string is using the format:
    x ="Job ID: 12 Name: name"
    """
    global  select_regex
    return select_regex.findall(string)
def findDataDirFromID(job_id):
    print("data: " + str(getJobsForID(getJobsForID(job_id=job_id))[0]))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

if __name__ == "__main__":
    t = Thread(target=empty_queue, args=())
    t.setDaemon(True)
    t.start()
    app.run(host='0.0.0.0')