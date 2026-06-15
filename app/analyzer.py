import cv2
import numpy as np
from ultralytics import YOLO
import torch
import os
import json

from app.config import MODEL_PATH,TRACKED_VIDEO_NAME,SNAPSHOTS_DIR_NAME,EVENTS_JSON_NAME


def load_model():

    device = 0 if torch.cuda.is_available() else "cpu"

    print(f"Loading model from: {MODEL_PATH}")
    print(f"Using device: {device}")
    model = YOLO(MODEL_PATH)

    return model, device


def create_output_structure(output_dir: str):

    os.makedirs(output_dir, exist_ok=True)
    snapshots_dir = os.path.join(output_dir,SNAPSHOTS_DIR_NAME)
    os.makedirs(snapshots_dir,exist_ok=True)

    return {"output_dir": output_dir,"snapshots_dir": snapshots_dir}



def analyze_video(video_path, safe_zones, restricted_zones, output_dir):

    model, device = load_model()
    paths = create_output_structure(output_dir)
    video_info = open_video(video_path)

    writer, tracked_video_path = create_video_writer(
        paths["output_dir"],
        video_info["fps"],
        video_info["width"],
        video_info["height"]
    )

    cap = video_info["cap"]

    frame_count = 0
    last_results = None

    safe_polygons = convert_zones_to_numpy(safe_zones)
    restricted_polygons = convert_zones_to_numpy(restricted_zones)

    safe_polygons = scale_zones(
        safe_polygons,
        video_info["width"],
        video_info["height"]
    )

    restricted_polygons = scale_zones(
        restricted_polygons,
        video_info["width"],
        video_info["height"]
    )

    print(f"Safe Zones: {len(safe_polygons)}")
    print(f"Restricted Zones: {len(restricted_polygons)}")

    print(f"FPS: {video_info['fps']}")
    print(f"Resolution: {video_info['width']} x {video_info['height']}")



    timeline = {}
    current_second = -1
    latest_second_data = None
    previous_second_data = None
    last_saved_redzone_count = 0

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        frame_count += 1
        if frame_count % 5 == 0:

            last_results = model.track(frame,persist=True,device=device,verbose=False)

        results = last_results
        people_count = 0
        red_zone_count = 0
        safe_zone_count = 0

        if results is not None and results[0].boxes.id is not None:

            boxes = results[0].boxes.xyxy.cpu().numpy()
            ids = results[0].boxes.id.cpu().numpy().astype(int)
            classes = results[0].boxes.cls.cpu().numpy().astype(int)

            for box, track_id, cls in zip(boxes, ids, classes):
                class_name = model.names[cls]

                if class_name.lower() != "person":
                    continue

                people_count += 1
                x1, y1, x2, y2 = map(int, box)
                foot_x, foot_y = bbox_bottom_center(box)

                inside_red = False
                inside_safe = False

                for zone in restricted_polygons:
                    zone_polygon = zone["polygon"]

                    if cv2.pointPolygonTest(zone_polygon,(foot_x, foot_y),False) >= 0:
                        inside_red = True
                        break

                for zone in safe_polygons:
                    zone_polygon = zone["polygon"]

                    if cv2.pointPolygonTest(zone_polygon,(foot_x, foot_y),False) >= 0:
                        inside_safe = True
                        break
        
                if inside_red:
                    red_zone_count += 1
                    color = (0, 0, 255)
                    text = f"Person ID:{track_id} : RESTRICTED"

                elif inside_safe:
                    safe_zone_count += 1
                    color = (0, 255, 0)
                    text = f"Person ID:{track_id} : SAFE"

                else:
                    color = (0, 255, 255)
                    text = f"Person ID:{track_id}"

                cv2.rectangle(frame,(x1, y1),(x2, y2),color,2)
                cv2.putText(frame,text,(x1, y1 - 10),cv2.FONT_HERSHEY_SIMPLEX,0.6,color,2)

        current_time_sec = int(cap.get(cv2.CAP_PROP_POS_MSEC) / 1000)
        latest_second_data = {"total_persons": people_count,
                            "redzone_violations": red_zone_count,
                            "safezone_keep": safe_zone_count}


        overlay = frame.copy()

        for zone in restricted_polygons:
            cv2.fillPoly(overlay,[zone["polygon"]],(0, 0, 255))
            cv2.polylines(frame,[zone["polygon"]],True,(0, 0, 255),2)

        for zone in safe_polygons:
            cv2.fillPoly(overlay,[zone["polygon"]],(0, 255, 0))
            cv2.polylines(frame,[zone["polygon"]],True,(0, 255, 0),2)

        frame = cv2.addWeighted(overlay,0.20,frame,0.80,0)



        if current_second == -1:
            current_second = current_time_sec

        elif current_time_sec != current_second:
            if previous_second_data is not None:

                timeline_entry = previous_second_data.copy()

                if last_saved_redzone_count is not None:
                    alert = get_redzone_alert(
                        last_saved_redzone_count,
                        previous_second_data["redzone_violations"])

                    if alert:
                        snapshot_path = save_snapshot(frame,
                            paths["snapshots_dir"],current_second,alert)

                        timeline_entry["alert"] = alert
                        timeline_entry["snapshot"] = snapshot_path

                timeline[str(current_second)] = timeline_entry

                if last_saved_redzone_count is None:
                    last_saved_redzone_count = previous_second_data["redzone_violations"]
                else:
                    last_saved_redzone_count = previous_second_data["redzone_violations"]
                
            current_second = current_time_sec
        previous_second_data = latest_second_data.copy()


        print(f"Frame {frame_count} | "
            f"People={people_count} | "
            f"Restricted={red_zone_count} | "
            f"Safe={safe_zone_count}")


        writer.write(frame)


    if previous_second_data is not None:
        timeline_entry = previous_second_data.copy()

        if last_saved_redzone_count is not None:
            alert = get_redzone_alert(
                last_saved_redzone_count,
                previous_second_data["redzone_violations"])

            if alert:
                timeline_entry["alert"] = alert
        timeline[str(current_second)] = timeline_entry


    cap.release()
    writer.release()

    report_path = save_report(paths["output_dir"],timeline)

    return {
        "status": "completed",
        "device": str(device),
        "report_json": report_path,
        "tracked_video": tracked_video_path,
        "processed_frames": frame_count,
        "fps": video_info["fps"],
        "width": video_info["width"],
        "height": video_info["height"],
        "safe_zones": len(safe_polygons),
        "restricted_zones": len(restricted_polygons)
    }


def open_video(video_path: str):

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(
            f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    return {
        "cap": cap,
        "fps": fps,
        "width": width,
        "height": height,
        "total_frames": total_frames}


def convert_zones_to_numpy(zones):

    polygons = []
    for zone in zones:
        polygon = np.array(
            [[point.x, point.y] for point in zone.points],dtype=np.int32)

        polygons.append({"id": zone.id,"polygon": polygon,
                         "canvas_width": zone.canvas_width,
                         "canvas_height": zone.canvas_height})

    return polygons


def scale_zones(zones, video_width, video_height):

    scaled_zones = []
    for zone in zones:

        scale_x = video_width / zone["canvas_width"]
        scale_y = video_height / zone["canvas_height"]

        scaled_polygon = np.array([
            [int(x * scale_x), int(y * scale_y)]
            for x, y in zone["polygon"]
        ], dtype=np.int32)

        scaled_zones.append({
            "id": zone["id"],
            "polygon": scaled_polygon
        })

    return scaled_zones



def create_video_writer(output_dir, fps, width, height):

    output_path = os.path.join(output_dir,TRACKED_VIDEO_NAME)

    writer = cv2.VideoWriter(
        output_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height))

    return writer, output_path



def bbox_bottom_center(box):

    x1, y1, x2, y2 = box
    return int((x1 + x2) / 2), int(y2)


def save_report(output_dir, timeline):
    report_path = os.path.join(output_dir,EVENTS_JSON_NAME)

    with open(report_path, "w") as f:
        json.dump(timeline,f,indent=4)

    return report_path


def get_redzone_alert(previous_count, current_count):

    if current_count > previous_count:
        return "entry_in_restricted_area"

    if current_count < previous_count:
        return "exit_from_restricted_area"

    return None


def save_snapshot(frame, snapshots_dir, second, alert):

    filename = f"sec_{second}_{alert}.jpg"

    snapshot_path = os.path.join(snapshots_dir,filename)
    cv2.imwrite(snapshot_path, frame)

    return snapshot_path
