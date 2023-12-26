import cv2
import dlib
import time
import math
import numpy as np
import imutils
import time
from imutils import face_utils
from imutils.video import VideoStream
from scipy.spatial import distance as dist
def facemonitor():
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
    cap = VideoStream(src=0).start()
    time.sleep(2)

    LIP_OPEN_THRESH = 20
    LIP_CLOSE_THRESH = 20
    lip_motion_count = 0
    lip_motion = False
    warning=0
    while True:
        # Read a frame from the webcam
        frame = cap.read()
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
                # Calculate the position of the eye pupil
                pupil_x = x + ex + ew // 2
                pupil_y = y + ey + eh // 2

                # Calculate the distance between the center of the camera frame and the center of the eye
                distance = math.sqrt((pupil_x - camera_center_x)**2 + (pupil_y - camera_center_y)**2)

                # If the distance is smaller than the minimum distance, update the minimum distance and selected eye position
                if distance < min_distance:
                    min_distance = distance
                    selected_eye_position = (pupil_x, pupil_y)

                # Draw a circle at the position of the eye pupil
                cv2.circle(roi_color, (pupil_x, pupil_y), 3, (255, 0, 0), -1)

        # If an eye that is looking at the camera is found, print "seeing camera", else print "warning"
        if selected_eye_position is not None:
            warning=0
            # Draw a circle at the position of the eye pupil
            cv2.circle(frame, selected_eye_position, 3, (0, 255, 0), -1)
            # Display "seeing camera" in the window
            cv2.putText(frame, "seeing camera", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        else:
            # Display "warning" in the window
            warning+=1
            if warning>100:
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

        cv2.imshow('frame',frame)

        # Exit the loop if the 'q' key is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the webcam and close the window
    cap.stop()
    cv2.destroyAllWindows()


