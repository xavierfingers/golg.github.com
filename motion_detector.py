import cv2
import numpy as np

# --- Configuration ---
MIN_AREA = 500  # Minimum area (in pixels) to consider a contour as motion
BLUR_SIZE = (21, 21) # Size of the Gaussian blur kernel
THRESHOLD_DELTA = 25 # Threshold value for the difference image

# --- Initialize Camera ---
print("[INFO] Starting video stream for motion detection...")
cap = cv2.VideoCapture(0) # 0 for default webcam, change if you have multiple cameras

if not cap.isOpened():
    print("Error: Could not open video stream.")
    exit()

# Read the first frame and initialize the 'previous frame'
# This frame will be used for comparison to detect motion
ret, frame1 = cap.read()
if not ret:
    print("Error: Failed to grab initial frame.")
    exit()

# Convert to grayscale and blur to reduce noise
prev_gray = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
prev_gray = cv2.GaussianBlur(prev_gray, BLUR_SIZE, 0)

print("[INFO] Ready. Press 'q' to quit.")

# --- Main Loop for Motion Detection ---
while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to grab frame.")
        break

    # Convert current frame to grayscale and blur
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, BLUR_SIZE, 0)

    # Compute the absolute difference between the current frame and previous frame
    frame_delta = cv2.absdiff(prev_gray, gray)

    # Threshold the delta image to reveal areas of significant change
    thresh = cv2.threshold(frame_delta, THRESHOLD_DELTA, 255, cv2.THRESH_BINARY)[1]

    # Dilate the thresholded image to fill in holes, then find contours
    thresh = cv2.dilate(thresh, None, iterations=2)
    contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Loop over the contours
    for contour in contours:
        # If the contour is too small, ignore it
        if cv2.contourArea(contour) < MIN_AREA:
            continue

        # Compute the bounding box for the contour, and draw it on the original frame
        (x, y, w, h) = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2) # Green rectangle
        cv2.putText(frame, "Motion Detected", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Display the original frame with motion rectangles and the thresholded difference image
    cv2.imshow("Motion Detector", frame)
    cv2.imshow("Thresh", thresh)
    # cv2.imshow("Frame Delta", frame_delta) # Uncomment to see the raw difference

    # Update the previous frame for the next iteration
    prev_gray = gray.copy()

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- Cleanup ---
cap.release()
cv2.destroyAllWindows()
print("[INFO] Video stream stopped and windows closed.")
