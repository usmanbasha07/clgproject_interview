import secrets
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
# pip install openpyxl
from flask_mail import Mail, Message
import cv2
import face_recognition
import setuptools
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from interview import facemonitor
import random

import dlib
import math
import imutils
import time
from imutils import face_utils
from imutils.video import VideoStream
from scipy.spatial import distance as dist

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
            cur.execute(f"SELECT job_desc,jobrole FROM admin_data where id='{ID}'")
            desc = cur.fetchone()
            cur.execute(f"SELECT * FROM user_data WHERE admin = '{UN}' ORDER BY resume_score DESC;")
            data = cur.fetchall()   
            return render_template('user_data.html', data=data, desc=desc, msg=msg)
        else:
            return redirect(url_for('admin_login'))
    except Exception as e:
        print(e)
        return redirect(url_for('admin_login'))
    # finally:
    #     mysql.close()
    #     return render_template('user_data.html', msg='No Data Found')


@app.route('/user_data/chart')
def chart():
    try:
        if 'loggedin' in session and session['loggedin']:
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            ID = session['id']
            UN = session['username']
            cur.execute(f"SELECT job_desc FROM admin_data where id='{ID}'")
            desc = cur.fetchone()
            cur.execute(f"SELECT resume_score FROM user_data WHERE admin = '{UN}' ORDER BY resume_score DESC;")
            data = cur.fetchall()
            li=[0,0,0,0,0]
            for i in data:
                ans=i["resume_score"]
                if ans>=0 and ans<=20:
                    li[0]=li[0]+1
                if ans>20 and ans<=40:
                    li[1]=li[1]+1
                if ans>40 and ans<=60:
                    li[2]=li[2]+1
                if ans>60 and ans<=80:
                    li[3]=li[3]+1
                if ans>80 and ans<=100:
                    li[4]=li[4]+1                  
            return render_template('chart.html', li=li,total=len(data))
        else:
            return redirect(url_for('admin_login'))
    except Exception as e:
        print(e)
    return render_template('chart.html')

@app.route('/user_data/interview_result')
def interview_result():
    try:
        if 'loggedin' in session and session['loggedin']:
            msg = request.args.get('msg', None)
            cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            ID = session['id']
            UN = session['username']
            cur.execute(f"SELECT job_desc,jobrole FROM admin_data where id='{ID}'")
            desc = cur.fetchone()
            cur.execute(f"SELECT * FROM user_data WHERE admin = '{UN}' and eligible = 1 ORDER BY interview_score DESC;")
            data = cur.fetchall()   
            return render_template('interview_result.html', data=data, desc=desc, msg=msg)
        else:
            return redirect(url_for('admin_login'))
    except Exception as e:
        print(e)
        return redirect(url_for('admin_login'))


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
            cursor.execute(f"SELECT Email_ID FROM user_data WHERE resume_score >= '{request.form['range']}' and admin='{session['admin']}'")
            data = cursor.fetchall()
            cursor.execute(f"UPDATE user_data SET eligible='1' WHERE resume_score >= '{request.form['range']}'and admin='{session['admin']}'")
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

The AI online interview will be held on '''+request.form['date']+'''  via virtual interviewer.

To prepare for the interview, please review the job description carefully and think about how your skills and experience match the requirements. You should also be prepared to answer questions about your skills and experience.

To join the interview, please click on the following link at the scheduled time: http://localhost:5000

We look forward to meeting you soon!

Sincerely,
AI Recruiter
'''+request.form['company']+''' 


Please note that this email is an automated message and does not require a response. If there are any issues with your account or if you need
further assistance, please contact us at 'helpsupport@gmail.com'
'''
            # print(msg.body )
            mail.send(msg)
            flash('Email sent successfully!')
            return redirect(url_for('user_data'))
    except Exception as e:
        flash('Error sending email: ' + str(e), 'danger')
        return redirect(url_for('user_data'))





@app.route('/interviewmail',methods=['GET','POST'])
def interviewmail():
    try:
        if request.method=='POST':
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(f"SELECT Email_ID FROM user_data WHERE interview_score >= '{request.form['range']}' and admin='{session['admin']} and eligible=1'")
            data = cursor.fetchall()
            cursor.execute(f"SELECT Email_ID FROM user_data WHERE interview_score < '{request.form['range']}'and admin='{session['admin']} and eligible=1'")
            regretdata = cursor.fetchall()
            # cursor.execute(f"UPDATE user_data SET eligible='1' WHERE resume_score >= '{request.form['range']}'")
            # mysql.connection.commit()
            li=[]
            rli=[]
            for i in range(len(data)):
                li.append(data[i]['Email_ID'])
            for i in range(len(regretdata)):
                rli.append(regretdata[i]['Email_ID'])
            
            app.config['MAIL_SERVER'] = 'smtp.hostinger.com'
            app.config['MAIL_PORT'] = 587
            app.config['MAIL_USERNAME'] ='recruiter@hackerbucket.com'
            app.config['MAIL_PASSWORD'] = 'Sad@dm1n'
            app.config['MAIL_USE_TLS'] = True
            app.config['MAIL_USE_SSL'] = False
            mail = Mail(app)

            msg = Message(subject='''Congratulations! You've been selected in AI online interview for '''+request.form['jobtitle']+''' at '''+request.form['company']+'''.''', sender='recruiter@hackerbucket.com', recipients=li)
            msg.body = '''
Dear Candidate,

I am excited to inform you that you have been Selected for an AI online interview for the '''+request.form['jobtitle']+''' role at '''+request.form['company']+''' .

The Face to Face HR interview At the  '''+request.form['company']+''' office on '''+request.form['date']+'''.

We look forward to meeting you soon!

Sincerely,
AI Recruiter
'''+request.form['company']+''' 


Please note that this email is an automated message and does not require a response. If there are any issues with your account or if you need
further assistance, please contact us at 'helpsupport@gmail.com'
'''

            rmsg = Message(subject='''Regretfully, you have not been selected for the '''+request.form['jobtitle']+''' position at '''+request.form['company']+'''.''', sender='recruiter@hackerbucket.com', recipients=rli)
            rmsg.body = '''
Dear Candidate,

We appreciate the effort and enthusiasm you have shown towards '''+request.form['company']+'''.

After careful consideration, we regret to inform you that we will not be moving forward with your profile.


We wish you the very best for your future endeavors and hope that our paths cross again.

Sincerely,
AI Recruiter
'''+request.form['company']+''' 


Please note that this email is an automated message and does not require a response. If there are any issues with your account or if you need
further assistance, please contact us at 'helpsupport@gmail.com'
'''
            # print(msg.body )
            
            mail.send(msg)
            mail.send(rmsg)
            flash('Email sent successfully!')
            return redirect(url_for('interview_result'))
    except Exception as e:
        flash('Error sending email: ' + str(e), 'danger')
        return redirect(url_for('interview_result'))
    



@app.route('/senddesc', methods=['GET', 'POST'])
def senddesc():
    try:
        if request.method=='POST':
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(f"UPDATE admin_data SET job_desc='{request.form['jobdesc']}', jobrole='{request.form['jobname']}' WHERE id='{session['id']}'")
            mysql.connection.commit()
            flash('Job Description Updated Successfully!')
            return redirect(url_for('user_data'))
    except Exception as e:
        flash('Error in Updating Job Description: ' + str(e), 'danger')
        return redirect(url_for('user_data'))

@app.route('/sendques', methods=['GET', 'POST'])
def sendques():
    try:
        if request.method=='POST':
            file=request.form['upload']
            data=pd.read_excel(file, header=None)
            data=data.to_dict()
            ques=[]
            ans=[]
            for i in range(1,len(data[0])):
                ques.append(data[0][i])
                ans.append(data[1][i])
            ques=json.dumps(ques)
            ans=json.dumps(ans)
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(f"UPDATE admin_data SET questions='{ques}', answers='{ans}' WHERE id='{session['id']}'")
            mysql.connection.commit()
            flash("Questions and Answers Added to the Database")
            return redirect(url_for('user_data'))
    except Exception as e:
        flash('Error in Updating Question: ' + str(e), 'danger')
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
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT username FROM admin_data ORDER BY username')
    admins = cursor.fetchall() 
    if request.method == 'POST' and 'company' in request.form and 'email' in request.form and 'phno' in request.form:
        email = request.form['email']
        phno = request.form['phno']
        company=request.form['company']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user_data WHERE Email_ID = % s AND mobile_number = % s AND admin = %s', (email, phno,company))
        user = cursor.fetchone()
        # print(user['admin'] == request.form['company']) 
        if user and user['eligible'] and user['admin'] == request.form['company']:
            session['loggedin'] = True
            session['user_id'] = user['ID']
            session['admin'] = user['admin']
            session['Name'] = user['Name']
            session['Email_ID'] = user['Email_ID']
            session['mobile_number'] = user['mobile_number']
            session['score']=user['interview_score']
            session['interview_status']=user['interview_status']
            session['image']=user['image']
            msg = 'Logged in successfully !'
            # print("session['score']")
            return redirect(url_for('face_auth'))
        else:
            msg = 'Sorry you are not shortlisted for interview.'
    return render_template('login.html', msg = msg,company=admins)


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
            if session['interview_status']==0:
                return render_template('interview.html', name=session['Name'],display_button=True)
            else:
                return redirect(url_for('feedback'))
        else:
            return redirect(url_for('login'))
    except Exception as e:
        print(e)
        return "error"
        
@app.route('/interview/monitor')
def monitor():
    try:
        if 'loggedin' in session and session['loggedin'] and session['face_auth']:
            if session['interview_status']==0:
                owner=session['admin']
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute(f"SELECT questions, answers FROM admin_data WHERE username = '{owner}'")
                # cursor.execute(f"UPDATE user_data set interview_score = '1' WHERE id='{session['id']}'")
                # mysql.connection.commit()
                ques = cursor.fetchone()
                questions = json.loads(ques['questions'])
                answers = json.loads(ques['answers'])
                numbers = random.sample(range(len(questions)), 5)
                session['quesid'] = numbers
                session['ques']=questions
                session['ans']=answers
                session['answered'] = 0
                length=len(questions[5].split(" "))//2
                print(numbers)
                print(session['ques'][numbers[0]])
                session['interview_status']=1
                # update it in database
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute(f"UPDATE user_data set interview_status = '1' WHERE id='{session['user_id']}'")
                mysql.connection.commit()

                return render_template('monitor.html', name=session['Name'], ques_id=numbers[0], display_button=True,len=length,ques=questions[numbers[0]], ans=answers[numbers[0]])
            else:
                session.pop('loggedin', None)
                session.pop('id', None)
                session.pop('Name',None)
                session.pop('Email_ID',None)
                session.pop('mobile_number',None)
                session.pop('image',None)
                return redirect(url_for('feedback'))
        else:
            return redirect(url_for('login'))
    except Exception as e:
        print(e)
        return "error"
    
    
@app.route('/evaluate',methods =['GET', 'POST'])
def evaluate():
    try:
        if 'loggedin' in session and session['loggedin'] and session['face_auth']:
            if request.method == 'POST':
                ques_id = int(request.form['question_id'])
                user_answer = request.form['answer']
                if 'answered' in session:
                    answered = session['answered']
                else:
                    answered = 0
                answered+=1
                session['answered'] = answered
                if session['answered'] == 5:
                    print(session['answered'])
                    totalscore=session['score']
                    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    cursor.execute(f"UPDATE user_data set interview_score = '{totalscore}' WHERE id='{session['user_id']}'")
                    mysql.connection.commit()
                    return json.dumps({'message':"completed"})
                else:
                    # Answer comparision code goes here
                    content = [user_answer, session['ans'][ques_id]]
                    cv = CountVectorizer()
                    count_matrix = cv.fit_transform(content)
                    mat = cosine_similarity(count_matrix)
                    currscore=round((mat[1][0]*100),2)
                    currscore=(currscore*20)//100
                    # Answer comparision code goes here

                    # cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                    # cursor.execute(f"SELECT interview_score FROM user_data WHERE id={session['user_id']}")

                    session['score']= session['score']+currscore
                    question_ids = session['quesid']
                    question_ids.remove(ques_id)
                    session['quesid'] = question_ids
                    
                    new_ques_id = session['quesid'][0]
                    length=len(session['ques'][new_ques_id].split(" "))//2
                    return json.dumps({'message':"success", 'ques':session['ques'][new_ques_id],'ques_id':new_ques_id,'len':length})
                    
        else:
            return redirect(url_for('login'))
    except Exception as e:
        print(e)
        return "error"



# @app.route('/interview_monitor')
# def interview_monitor():
#     facemonitor(session['image'],session['Name'])
#     return "hello monitor"


def gen_frames(face,name):
    camera = cv2.VideoCapture(0)
    def lip_distance(shape):
        top_lip = shape[50:53]
        top_lip = np.concatenate((top_lip, shape[61:64]))

        low_lip = shape[56:59]
        low_lip = np.concatenate((low_lip, shape[65:68]))

        top_mean = np.mean(top_lip, axis=0)
        low_mean = np.mean(low_lip, axis=0)

        distance = abs(top_mean[1] - low_mean[1])
        return distance

    # Load the Haar cascade for face detection
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

    # Load the Haar cascade for eye detection
    eye_cascade = cv2.CascadeClassifier('haarcascade_eye.xml')

    # Load the shape predictor for lip detection
    predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')

    # Start the webcam
    # cap = VideoStream(src=0).start()
    # time.sleep(2)
    frame_counter=0
    LIP_OPEN_THRESH = 20
    LIP_CLOSE_THRESH = 20
    lip_motion_count = 0
    lip_motion = False
    warning=0 
    result=False 
    while True:
        try:
            success, frame = camera.read()  # read the camera frame
            if not success:
                print("error in camera")
                break
            else:
                frame = imutils.resize(frame, width=450)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Detect faces in the grayscale frame
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            # Calculate the center of the camera frame
            camera_center_x = frame.shape[1] // 2
            camera_center_y = frame.shape[0] // 2

            # Initialize the minimum distance and selected eye position
            min_distance = float('inf')
            selected_eye_position = None

            # For each face, detect eyes and calculate the distance between the center of the camera frame and the center of each eye
            for (x,y,w,h) in faces:
                rect = dlib.rectangle(int(x), int(y), int(x + w),int(y + h))
                shape = predictor(gray, rect)
                shape = face_utils.shape_to_np(shape)

                distance = lip_distance(shape)
                lip = shape[48:60]
                cv2.drawContours(frame, [lip], -1, (0, 255, 0), 1)

                if distance > LIP_OPEN_THRESH and not lip_motion:
                    lip_motion = True
                    lip_motion_count += 1
                elif distance < LIP_CLOSE_THRESH and lip_motion:
                    lip_motion = False

                roi_gray = gray[y:y+h, x:x+w]
                roi_color = frame[y:y+h, x:x+w]
                eyes = eye_cascade.detectMultiScale(roi_gray)
                for (ex,ey,ew,eh) in eyes:
                    pupil_x = x + ex + ew // 2
                    pupil_y = y + ey + eh // 2
                    distance = math.sqrt((pupil_x - camera_center_x)**2 + (pupil_y - camera_center_y)**2)
                    if distance < min_distance:
                        min_distance = distance
                        selected_eye_position = (pupil_x, pupil_y)
                    cv2.circle(roi_color, (pupil_x, pupil_y), 3, (255, 0, 0), -1)

            if selected_eye_position is not None:
                warning=0
                cv2.circle(frame, selected_eye_position, 3, (0, 255, 0), -1)
                cv2.putText(frame, "seeing camera", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            else:
                warning+=1
                if warning>70:
                    print("\rwarning", end='')
                    cv2.putText(frame, "Warning", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    
            cv2.putText(frame, "LIP MOTION COUNT: {}".format(lip_motion_count), (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            if lip_motion:
                cv2.putText(frame, "LIP MOTION: 1", (10, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                cv2.putText(frame, "LIP MOTION: 0", (10, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            frame_counter += 1
            # Call facerecog function after every 70 frames
            try:
                if frame_counter == 70:
                    ##############################
                    img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    encode_img = face_recognition.face_encodings(img)
                    if len(encode_img) > 0:  # Ensure at least one face was found
                        encode_img = encode_img[0]

                        # Load the image from the session
                        decodedArrays = json.loads(face)
                        dbface = np.asarray(decodedArrays["array"])

                        # Compare faces
                        result = face_recognition.compare_faces([encode_img], dbface)
                        result=result[0]
                    ##############################
                    if result:
                        print("\r"+name, end='')
                        cv2.putText(frame, name, (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    else:
                        print("\rUnknown Person", end='')
                        cv2.putText(frame, "Unknown Person", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                    frame_counter = 0 
            except Exception as e:
                print(e)  
            
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        except GeneratorExit:
            # The client has disconnected, so stop the camera
            camera.release()
            break
        except Exception as e:
            print(e)

@app.route('/interview_monitor')
def interview_monitor():
    return Response(gen_frames(session['image'],session['Name']), mimetype='multipart/x-mixed-replace; boundary=frame')



@app.route('/feedback')
def feedback():
    cursor = mysql.connection.cursor()
    mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    print(session['user_id'])
    # cursor.execute(f"UPDATE user_data set interview_score = 1 WHERE id={session['user_id']}")
    # mysql.connection.commit() 
    cursor.execute(f"SELECT interview_status FROM user_data WHERE id={session['user_id']}")
    status=cursor.fetchall()
    # print(round(status[0][0]))
    if status[0][0]!=0:
        session.pop('loggedin', None)
        session.pop('id', None)
        session.pop('Name',None)
        session.pop('Email_ID',None)
        session.pop('mobile_number',None)
        session.pop('image',None)
        session.pop('interview_status',None)
        session.pop('score',None)
        return render_template('feedback.html')
    else:
        return render_template('index.html')




if __name__=="__main__":
    # app.run(debug=True,host= '192.168.134.227')
    app.run(debug=True,host= 'localhost')