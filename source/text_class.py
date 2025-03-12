import time
import sys
import threading

class LoadingAnimation:
    def __init__(self, message="Processing"):
        self.message = message
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.animate)
        self.thread.start()

    def animate(self):
        chars = ["|", "/", "-", "\\"]
        i = 0
        while self.running:
            sys.stdout.write(f"\r{self.message} {chars[i % len(chars)]} ")
            sys.stdout.flush()
            i += 1
            time.sleep(0.2)

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        sys.stdout.write("\r" + " " * 50 + "\r")  # Temizle
        sys.stdout.flush()


def print_relevant_schemas(schema_data):
    print(f"Relevant Schema(s) Found: \n")
    for index, schema in enumerate(schema_data):
        print(f"--------------------\n{index + 1}.\n--------------------")
        print(f"DBName: {schema['DBName']}")
        print(f"Collection: {schema['Collection']}")
        print(f"Description: {schema['Description']}")
        print(f"Enums: {schema['Enums']}")
        print(f"Enums Description: {schema['EnumsDescription']}")
        print(f"Schema: {schema['Schema']}")
        print(f"Similarity Score: {schema['SimilarityScore']}\n")