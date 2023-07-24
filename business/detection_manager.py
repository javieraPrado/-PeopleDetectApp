from app.business.YOLOv7.track import TrackClass

class DetectionManager:
    def __init__(self, video_path):
        self.video_path = video_path
        self.detections = []
        self.centroids = []
        self.speeds = []
        self.track_instance = TrackClass()

    """def detect_people(self):
        self.track_instance.run_detection(source=self.video_path, 
                      yolo_weights='app/business/YOLOv7/yolov7.pt', 
                      classes=0,
                      conf_thres=0.4,
                      iou_thres=0.5,)"""
                      

    def calculate_centroids(self):
        # Add your centroid calculation code here...
        pass

    def calculate_speeds(self):
        # Add your speed calculation code here...
        pass

    def export_to_csv(self):
        # Add your csv export code here...
        pass
