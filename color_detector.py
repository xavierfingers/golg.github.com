import cv2
import numpy as np

# --- Configuration ---
# Define the lower and upper bounds for the color you want to detect in HSV color space.
# These values are for BLUE. You can find HSV color ranges online or using a color picker tool.
# Example HSV ranges:
# Blue:    H: 100-140, S: 50-255, V: 50-255
# Green:   H: 40-80, S: 50-255, V: 50-255
# Red:     H: 0-10 (and 170-180), S: 50-255, V: 50-255 (Red wraps around 0/180)
# Yellow:  H: 20-40, S: 50-255, V: 50-255

# Default to Blue
LOWER_COLOR_BOUND = np.array([100, 50, 50])
UPPER_COLOR_BOUND = np.array([140, 255, 255])

MIN_CONTOUR_AREA = 500 # Minimum area (in pixels) to consider a contour as a detected object

# --- Initialize Camera ---
print("[INFO] Starting video stream for color detection...")
cap = cv2.VideoCapture(0) # 0 for default webcam, change if you have multiple cameras

if not cap.isOpened():
    print("Error: Could not open video stream.")
    exit()

print("[INFO] Ready. Press 'q' to quit.")

# --- Main Loop for Color Detection ---
while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to grab frame.")
        break

    # Convert the frame from BGR to HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Create a mask for the specified color range
    mask = cv2.inRange(hsv, LOWER_COLOR_BOUND, UPPER_COLOR_BOUND)

    # Perform morphological operations to clean up the mask
    # Erode removes small blobs, dilate fills in small holes
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    # Find contours in the mask
    contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Loop over the detected contours
    for contour in contours:
        # If the contour is too small, ignore it
        if cv2.contourArea(contour) < MIN_CONTOUR_AREA:
            continue

        # Compute the bounding box for the contour and draw it on the original frame
        (x, y, w, h) = cv2.boundingRect(contour)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2) # Blue rectangle
        cv2.putText(frame, "Color Detected", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    # Display the original frame with detected colors and the mask
    cv2.imshow("Color Detector", frame)
    cv2.imshow("Mask", mask)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- Cleanup ---
cap.release()
cv2.destroyAllWindows()
print("[INFO] Video stream stopped and windows closed.")
