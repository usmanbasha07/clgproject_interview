from flask import Flask,flash, render_template, request, jsonify,Response,redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import numpy as np
from PIL import Image
import base64
import io
import json 
from json import JSONEncoder
import smtplib
import base64
# import requests
from flask_mail import Mail, Message
import cv2
import face_recognition

app = Flask(__name__)
app.secret_key = 'xyzsdfg'
# DATABASE CONNECTION
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'sra'

mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin_login', methods =['GET', 'POST'])
def admin_login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM admin_data WHERE username = % s AND password = % s', (username, password))
        user = cursor.fetchone()
        if user:
            session['loggedin'] = True
            session['id'] = user['id']
            session['username'] = user['username']
            msg = 'Logged in successfully !'
            return redirect(url_for('user_data'))
        else:
            msg = 'Invalid username/password !'
    return render_template('admin_login.html', msg = msg)

@app.route('/user_data')
def user_data():
    try:
        if 'loggedin' in session and session['loggedin']:
            msg = request.args.get('msg', None)
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            ID = session['id']
            UN = session['username']
            cur.execute(f"SELECT job_desc FROM admin_data where id='{ID}'")
            desc = cur.fetchone()
            cur.execute(f"SELECT * FROM user_data WHERE admin = '{UN}' ORDER BY resume_score DESC;")
            data = cur.fetchall()   
            return render_template('user_data.html', data=data, desc=desc, msg=msg)
        else:
            return redirect(url_for('admin_login'))
    except Exception as e:
        print(e)
    # finally:
    #     mysql.close()
    #     return render_template('user_data.html', msg='No Data Found')


@app.route('/user_data/chart')
def chart():
    # try:
    #     if 'loggedin' in session and session['loggedin']:
    #         cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    #         ID = session['id']
    #         UN = session['username']
    #         cur.execute(f"SELECT job_desc FROM admin_data where id='{ID}'")
    #         desc = cur.fetchone()
    #         cur.execute(f"SELECT * FROM user_data WHERE admin = '{UN}' ORDER BY resume_score DESC;")
    #         data = cur.fetchall()
    #         return render_template('chart.html', data=data, desc=desc)
    #     else:
    #         return redirect(url_for('admin_login'))
    # except Exception as e:
    #     print(e)
    # finally:
    #     mysql.close()
    return render_template('chart.html')


@app.route('/delete', methods=['GET', 'POST'])
def delete():
    cursor = mysql.connection.cursor()
    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    if request.method == 'POST': 
        for getid in request.form.getlist('mycheckbox'):
            print(getid)
            cur.execute('DELETE FROM user_data WHERE id = {0}'.format(getid))
            mysql.connection.commit()
        flash('Successfully Deleted!')
    return redirect('/user_data')


@app.route('/sendmail',methods=['GET','POST'])
def sendmail():
    try:
        if request.method=='POST':
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(f"SELECT Email_ID FROM user_data WHERE resume_score >= '{request.form['range']}'")
            data = cursor.fetchall()
            cursor.execute(f"UPDATE user_data SET eligible='1' WHERE resume_score >= '{request.form['range']}'")
            mysql.connection.commit()
            li=[]
            for i in range(len(data)):
                li.append(data[i]['Email_ID'])
            app.config['MAIL_SERVER'] = 'smtp.hostinger.com'
            app.config['MAIL_PORT'] = 587
            app.config['MAIL_USERNAME'] ='recruiter@hackerbucket.com'
            app.config['MAIL_PASSWORD'] = 'Sad@dm1n'
            app.config['MAIL_USE_TLS'] = True
            app.config['MAIL_USE_SSL'] = False
            mail = Mail(app)
            msg = Message(subject='''Congratulations! You've been shortlisted for an AI online interview for '''+request.form['jobtitle']+''' at '''+request.form['company']+'''.''', sender='recruiter@hackerbucket.com', recipients=li)
            msg.body = '''
Dear Candidate,

I am excited to inform you that you have been shortlisted for an AI online interview for the '''+request.form['jobtitle']+''' role at '''+request.form['company']+''' . We were very impressed with your resume and your qualifications, and we believe that you have the potential to be a valuable asset to our team.

The AI online interview will be held on '''+request.form['date']+'''  via virtual interview. During the interview, you will be asked a series of questions about your skills, experience, and motivation for the role. You will also have the opportunity to ask questions about the role and the company.

To prepare for the interview, please review the job description carefully and think about how your skills and experience match the requirements. You should also be prepared to answer questions about your skills and experience.

To join the interview, please click on the following link at the scheduled time: http://localhost:5000

We look forward to meeting you soon!

Sincerely,
AI Recruiter
'''+request.form['company']+''' 


Please note that this email is an automated message and does not require a response. If there are any issues with your account or if you need
further assistance, please contact us at 'helpsupport@gmail.com'
'''
            print(msg.body )
            mail.send(msg)
            flash('Email sent successfully!')
            return redirect(url_for('user_data'))
    except Exception as e:
        flash('Error sending email: ' + str(e), 'danger')
        return redirect(url_for('user_data'))

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username',None)
    return redirect(url_for('admin_login'))



# @app.route('/user_data')
# def user_data():
#     msg = request.args.get('msg', None)
#     return render_template('user_data.html', msg = msg)

@app.route('/login', methods =['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'email' in request.form and 'phno' in request.form:
        email = request.form['email']
        phno = request.form['phno']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user_data WHERE Email_ID = % s AND mobile_number = % s', (email, phno))
        user = cursor.fetchone()
        if user and user['eligible']:
            session['loggedin'] = True
            session['id'] = user['ID']
            session['Name'] = user['Name']
            session['Email_ID'] = user['Email_ID']
            session['mobile_number'] = user['mobile_number']
            session['image']=user['image']
            msg = 'Logged in successfully !'
            return redirect(url_for('face_auth'))
        else:
            msg = 'Sorry you are not shortlisted for interview.'
    return render_template('login.html', msg = msg)


@app.route('/face_auth',methods =['GET', 'POST'])
def face_auth():
    try:
        if 'loggedin' in session and session['loggedin'] :
            if request.method == 'POST':
                img=request.form["image"]
                img=img[23:].encode('utf-8')
                image_data = base64.b64decode(img)
                image = Image.open(io.BytesIO(image_data))
                image_np = np.array(image)
                im=Image.fromarray(image_np)
                im.save("test.jpg")
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                img = cv2.imread('test.jpg')
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                for (x, y, w, h) in faces:
                    cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                encode_img = face_recognition.face_encodings(img)[0]
                # print(encode_img)
                decodedArrays = json.loads(session['image'])
                dbface = np.asarray(decodedArrays["array"])
                # print(dbface)
                img=Image.fromarray(img)
                img.save('res.jpg')
                result=face_recognition.compare_faces([encode_img],dbface)
                print(result[0])
                if result[0]:
                    session['face_auth']=True
                    return "success"
                else:
                    return "Failed"
        else:
            return redirect(url_for('login'))
    except Exception as e:
        print(e)
        return "Failed"
    return render_template('face_auth.html')


@app.route('/interview')
def interview():
    try:
        if 'loggedin' in session and session['loggedin'] and session['face_auth']:
            return render_template('interview.html', display_button=True)
        else:
            return redirect(url_for('login'))
    except Exception as e:
        print(e)
        return redirect(url_for('face_auth'))

if __name__=="__main__":
    app.run(debug=True)
