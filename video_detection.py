import os
import cv2
import numpy as np
import tensorflow as tf
from ultralytics import YOLO
import pandas as pd
from collections import deque

def create_directories():
    UPLOAD_FOLDER = 'uploads'
    PROCESSED_FOLDER = 'processed'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(PROCESSED_FOLDER, exist_ok=True)

    return UPLOAD_FOLDER, PROCESSED_FOLDER

def load_models():
    IMAGE_HEIGHT, IMAGE_WIDTH = 64, 64
    SEQUENCE_LENGTH = 20
    CLASSES_LIST = ['TaiChi', 'JugglingBalls', 'Basketball', 'PommelHorse']

    LRCN_model = tf.keras.models.load_model('LRCN.h5')
    yolo_model = YOLO('yolov8s.pt')
    with open("coco.txt", "r") as my_file:
        object_list = my_file.read().split("\n")

    return LRCN_model, yolo_model, object_list, IMAGE_HEIGHT, IMAGE_WIDTH, SEQUENCE_LENGTH, CLASSES_LIST

def initialize():
    """
    Initialize the directories, models, and configurations.
    """
    UPLOAD_FOLDER, PROCESSED_FOLDER = create_directories()
    LRCN_model, yolo_model, object_list, IMAGE_HEIGHT, IMAGE_WIDTH, SEQUENCE_LENGTH, CLASSES_LIST = load_models()
    return UPLOAD_FOLDER, PROCESSED_FOLDER, LRCN_model, yolo_model, object_list, IMAGE_HEIGHT, IMAGE_WIDTH, SEQUENCE_LENGTH, CLASSES_LIST

def dis(pt1, pt2):
    cx1 = int((pt1[0] + pt1[2]) / 2)
    cy1 = int((pt1[1] + pt1[3]) / 2)
    cx2 = int((pt2[0] + pt2[2]) / 2)
    cy2 = int((pt2[1] + pt2[3]) / 2)
    distance = np.hypot(cx2 - cx1, cy2 - cy1)
    return distance

def get_area(x1, y1, x2, y2):
    w = x2 - x1
    h = y2 - y1
    area = w * h
    return area

def bigger_frame(pt, w, h):
    val = 80
    x1, y1, x2, y2 = pt[0], pt[1], pt[2], pt[3]
    x1 -= val if x1 - val >= 0 else 0
    y1 -= val if y1 - val >= 0 else 0
    x2 += val if x2 + val <= w else w
    y2 += val if y2 + val <= h else h
    return (x1, y1, x2, y2)

def process_video(input_file_path, output_file_path, LRCN_model, yolo_model, object_list, IMAGE_HEIGHT, IMAGE_WIDTH, SEQUENCE_LENGTH, CLASSES_LIST):
    prev_frames = []
    track_id = 0
    frame_list = {}
    tracking_object = {}
    predicted_class_name = {}
    count = 0

    video_reader = cv2.VideoCapture(input_file_path)
    original_video_width = int(video_reader.get(cv2.CAP_PROP_FRAME_WIDTH))
    original_video_height = int(video_reader.get(cv2.CAP_PROP_FRAME_HEIGHT))
    video_writer = cv2.VideoWriter(output_file_path, cv2.VideoWriter_fourcc('M', 'P', '4', 'V'),
                                   video_reader.get(cv2.CAP_PROP_FPS), (original_video_width, original_video_height))

    i = 0
    prev_frames_id = []
    while True:
        res, frame = video_reader.read()
        if not res:
            break
        
        if i % 3 == 0:
            count += 1
            results = yolo_model.predict(frame)
            a = results[0].boxes.data
            px = pd.DataFrame(a).astype("float")
            cur_frames = []
            sq_len = SEQUENCE_LENGTH
            for ind, box in px.iterrows():
                (x1, y1, x2, y2, d) = (int(box[0]), int(box[1]), int(box[2]), int(box[3]), int(box[5]))
                c = object_list[d]
                if 'person' in c and get_area(x1, y1, x2, y2) >= 30000:
                    cur_frames.append((x1, y1, x2, y2))

            curr_frames_id = []
            if count <= 2:
                for pt1 in cur_frames:
                    for pt2 in prev_frames:
                        distance = dis(pt1, pt2)
                        if distance < 40:
                            tracking_object[track_id] = pt1
                            curr_frames_id.append(track_id)
                            frame_list[track_id] = deque(maxlen=20)

                            x1, y1, x2, y2 = bigger_frame(pt1, original_video_width, original_video_height)
                            new_frame = frame[y1:y2, x1:x2]

                            resized_frame = cv2.resize(new_frame, (IMAGE_HEIGHT, IMAGE_WIDTH))
                            normalized_frame = resized_frame / 255
                            frame_list[track_id].append(normalized_frame)
                            track_id += 1
                            break
                prev_frames = cur_frames.copy()
            else:
                tracking_object_copy = tracking_object.copy()
                curr_frames_copy = cur_frames.copy()
                for id, pt2 in tracking_object_copy.items():
                    id_exists = False
                    for pt in curr_frames_copy:
                        distance = dis(pt, pt2)
                        if distance < 40:
                            tracking_object[id] = pt
                            curr_frames_id.append(id)

                            x1, y1, x2, y2 = bigger_frame(pt, original_video_width, original_video_height)
                            new_frame = frame[y1:y2, x1:x2]

                            resized_frame = cv2.resize(new_frame, (IMAGE_HEIGHT, IMAGE_WIDTH))
                            normalized_frame = resized_frame / 255
                            frame_list[id].append(normalized_frame)

                            id_exists = True
                            if pt in cur_frames:
                                cur_frames.remove(pt)
                            break
                    if not id_exists:
                        tracking_object.pop(id)
                        frame_list.pop(id)

                for pt in cur_frames:
                    tracking_object[track_id] = pt
                    curr_frames_id.append(track_id)
                    frame_list[track_id] = deque(maxlen=SEQUENCE_LENGTH)

                    x1, y1, x2, y2 = bigger_frame(pt, original_video_width, original_video_height)
                    new_frame = frame[y1:y2, x1:x2]

                    resized_frame = cv2.resize(new_frame, (IMAGE_HEIGHT, IMAGE_WIDTH))
                    normalized_frame = resized_frame / 255
                    frame_list[track_id].append(normalized_frame)
                    track_id += 1

            for id in curr_frames_id:
                frame_queue = frame_list[id]
                if len(frame_queue) == SEQUENCE_LENGTH:
                    predicted_labels_probabilities = LRCN_model.predict(np.expand_dims(frame_queue, axis=0))[0]
                    predicted_label = np.argmax(predicted_labels_probabilities)
                    predicted_class_name[id] = CLASSES_LIST[predicted_label]
                    frame_list[id] = deque(maxlen=SEQUENCE_LENGTH)
            prev_frames_id = curr_frames_id
        else:
            curr_frames_id = prev_frames_id

        for id in curr_frames_id:
            font = cv2.FONT_HERSHEY_DUPLEX
            name = ''
            if predicted_class_name.get(id) is not None:
                name = predicted_class_name[id]
            x1, y1, x2, y2 = tracking_object[id]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, name, (x1 + 6, y1 - 6), font, 1.0, (255, 0, 0), 1)

        i += 1
        video_writer.write(frame)

    video_reader.release()
    video_writer.release()
    