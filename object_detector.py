import cv2
import numpy as np
import os

# --- Configuration --- 
# Path to the directory where you saved the model files
MODEL_DIR = "models"
PROTOTXT_PATH = os.path.join(MODEL_DIR, "MobileNetSSD_deploy.prototxt")
MODEL_PATH = os.path.join(MODEL_DIR, "MobileNetSSD_deploy.caffemodel")
LABELS_PATH = os.path.join(MODEL_DIR, "class_labels.txt")

CONFIDENCE_THRESHOLD = 0.2 # Minimum confidence to display a detection

# --- Load Class Labels ---
CLASSES = []
with open(LABELS_PATH, 'r') as f:
    CLASSES = f.read().strip().split("\n")

# Generate random colors for each class for bounding boxes
COLORS = np.random.uniform(0, 255, size=(len(CLASSES), 3))

# --- Load Pre-trained Model ---
print("[INFO] Loading model...")
net = cv2.dnn.readNetFromCaffe(PROTOTXT_PATH, MODEL_PATH)
print("[INFO] Model loaded.")

# --- Initialize Camera ---
print("[INFO] Starting video stream...")
cap = cv2.VideoCapture(0) # 0 for default webcam, change if you have multiple cameras

if not cap.isOpened():
    print("Error: Could not open video stream.")
    exit()

# --- Main Loop for Object Detection ---
while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to grab frame.")
        break

    # Resize frame to a fixed width and height (300x300 is common for MobileNet SSD)
    # and create a blob for the neural network input
    (h, w) = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)

    # Pass the blob through the network and obtain the detections
    net.setInput(blob)
    detections = net.forward()

    # Loop over the detections
    for i in np.arange(0, detections.shape[2]):
        # Extract the confidence (probability) of the detection
        confidence = detections[0, 0, i, 2]

        # Filter out weak detections by ensuring the confidence is greater than the minimum threshold
        if confidence > CONFIDENCE_THRESHOLD:
            # Extract the index of the class label and the bounding box coordinates
            idx = int(detections[0, 0, i, 1])
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")

            # Draw the prediction on the frame
            label = f"{CLASSES[idx]}: {confidence:.2f}%"
            cv2.rectangle(frame, (startX, startY), (endX, endY), COLORS[idx], 2)
            y = startY - 15 if startY - 15 > 15 else startY + 15
            cv2.putText(frame, label, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS[idx], 2)

    # Show the output frame
    cv2.imshow("Object Detection", frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- Cleanup ---
cap.release()
cv2.destroyAllWindows()
print("[INFO] Video stream stopped and windows closed.")
