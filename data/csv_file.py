import csv

class CSVFile:
    def __init__(self, filepath):
        self.filepath = filepath

    def write_csv(self, data):
        with open(self.filepath, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(data)
