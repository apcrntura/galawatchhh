import os
import time
from datetime import datetime, timezone, timedelta

import cv2
from ultralytics import YOLO
from supabase import create_client

# ==========================================
# SETTINGS
# ==========================================
SUPABASE_URL = "https://uftbfpzedfnuruycunby.supabase.co"
# Secret (service_role) key, read from an environment variable.
# Never paste it into this file or upload it to GitHub.
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
DESTINATION_ID = "apc"

MANILA = timezone(timedelta(hours=8))
DEAD_BAND = 25           # pixels on each side of the line that are ignored (stops jitter)
HEARTBEAT_SECONDS = 5    # send an update at least this often so the dashboard knows the camera is alive

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
model = YOLO("yolo11n.pt")
camera = cv2.VideoCapture(0)


def today():
    return datetime.now(MANILA).date()


# ==========================================
# RESUME TODAY'S TOTALS AFTER A RESTART
# ==========================================
def load_today_counts():
    res = (supabase.table("camera_counts").select("*")
           .eq("destination_id", DESTINATION_ID).limit(1).execute())
    if not res.data:
        raise SystemExit("No camera_counts row with destination_id 'apc'. Create it in Supabase first.")
    row = res.data[0]
    stamp = datetime.strptime(row["updated_at"][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    if stamp.astimezone(MANILA).date() == today():
        return row["people_in"] or 0, row["people_out"] or 0
    return 0, 0


people_in, people_out = load_today_counts()
current_day = today()
print(f"Starting from IN: {people_in} | OUT: {people_out}")

sides = {}               # track id -> "L" or "R"
last_sent = (None, None)
last_attempt = 0


def send_to_supabase():
    global last_sent, last_attempt
    last_attempt = time.time()
    inside = max(people_in - people_out, 0)
    try:
        supabase.table("camera_counts").update({
            "people_in": people_in,
            "people_out": people_out,
            "current_inside": inside,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("destination_id", DESTINATION_ID).execute()
        last_sent = (people_in, people_out)
        print(f"Supabase updated | IN: {people_in} | OUT: {people_out} | INSIDE: {inside}")
    except Exception as e:
        print("Supabase update failed:", e)


# ==========================================
# CAMERA LOOP
# ==========================================
while True:
    ok, frame = camera.read()
    if not ok:
        print("Could not access camera")
        break

    # New day in Manila time: start the daily totals again
    if today() != current_day:
        current_day = today()
        people_in = people_out = 0
        send_to_supabase()

    height, width = frame.shape[:2]
    middle_x = width // 2

    results = model.track(frame, classes=[0], conf=0.30, persist=True, verbose=False)
    result = results[0]

    cv2.line(frame, (middle_x, 0), (middle_x, height), (0, 0, 255), 3)
    cv2.putText(frame, "EXIT LINE", (middle_x + 10, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    if result.boxes is not None and result.boxes.id is not None:
        boxes = result.boxes.xyxy.cpu().numpy()
        ids = result.boxes.id.int().cpu().tolist()

        for box, pid in zip(boxes, ids):
            x1, y1, x2, y2 = map(int, box)
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            # Which side of the line is this person on? Inside the dead band, keep the old side.
            if cx < middle_x - DEAD_BAND:
                side = "L"
            elif cx > middle_x + DEAD_BAND:
                side = "R"
            else:
                side = sides.get(pid)

            if side:
                old = sides.get(pid)
                if old == "R" and side == "L":      # right -> left = enters
                    people_in += 1
                    print(f"PERSON ENTERED | IN: {people_in}")
                elif old == "L" and side == "R":    # left -> right = exits
                    people_out += 1
                    print(f"PERSON EXITED | OUT: {people_out}")
                sides[pid] = side

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
            cv2.putText(frame, f"PERSON {pid}", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 5, (255, 0, 0), -1)

    inside = max(people_in - people_out, 0)
    cv2.putText(frame, f"Inside: {inside}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
    cv2.putText(frame, f"IN: {people_in}", (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 3)
    cv2.putText(frame, f"OUT: {people_out}", (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 165, 255), 3)

    # Send when a number changed (at most once a second), and as a heartbeat every few seconds
    now = time.time()
    changed = (people_in, people_out) != last_sent
    if (changed and now - last_attempt >= 1) or now - last_attempt >= HEARTBEAT_SECONDS:
        send_to_supabase()

    cv2.imshow("AI People Counter", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
