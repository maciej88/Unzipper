import os
import time
from datetime import datetime
import queue
import logging
import threading
import shutil
import zipfile

basepath = '/builds'
targetpath = '/builds'
logpath = "/Logs"

thread_limit = 4

runtime = time.strftime("%H_%M_%S")
log_directory = os.path.join(logpath, time.strftime("%d-%m-%Y"))
log_file_path = os.path.join(log_directory, f"{runtime}.log")

# threads list initialize
threads = []


class CreateLogfile:
    def __init__(self, log_directory, log_file_path):
        self.log_directory = log_directory
        self.log_file_path = log_file_path

    def log_create(self, line):
        with open(self.log_file_path, 'a') as f:
            f.write(line.__repr__() + '\n')

    def create_log_directory_and_file(self):
        try:
            os.makedirs(self.log_directory, exist_ok=True)
            with open(self.log_file_path, 'x'):
                pass
        except FileExistsError:
            pass
        except Exception as create_error:
            self.log_error(f"Error while logfile creation: {create_error}")

    def log_error(self, error_message):
        try:
            with open(self.log_file_path, 'a') as logfile:
                logfile.write(f"{error_message}\n")
        except Exception as write_error:
            print(f"Error while writing to logfile: {write_error}")


class LogLine:
    def __init__(self, timestamp: datetime, source: str, message: str):
        self.message = message
        self.source = source
        self.timestamp = timestamp

    def __repr__(self):
        return f'LogLine[{self.timestamp}, src: {self.source}, message={self.message}]'


class Unzipper:
    queue = queue.Queue()

    @staticmethod
    def update_log(text, elapsed=""):
        print('start log')
        if elapsed:
            elapsed = f"- Time elapsed: {elapsed}"
        try:
            logging.info(f"[{time.strftime('%H:%M:%S')}] {text} {elapsed}")
        except Exception as e:
            print(f"Error writing to file - {e}")
        print(text)

        try:
            with open(log_file_path, 'a') as logfile:
                logfile.write(f"[{time.strftime('%H:%M:%S')}] {text} {elapsed}\n")
        except Exception as e:
            print(f"Error writing to logfile: {e}")

    @staticmethod
    def unzip(zip_path):
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                target_folder = os.path.join(targetpath, os.path.splitext(os.path.basename(zip_path))[0])
                if not os.path.exists(target_folder):
                    os.makedirs(target_folder)
                zip_ref.extractall(target_folder)

                unpacked_file_path = os.path.join(target_folder, 'unpacked.txt')
                with open(unpacked_file_path, 'x'):
                    pass

                # Remove file after unzip
                os.remove(zip_path)
        except zipfile.BadZipFile as e:
            Unzipper.update_log(f"[ERROR] Broken zipfile encountered for {os.path.basename(zip_path)} - {e}")
            CreateLogfile(log_directory, log_file_path).log_error(
                f"[ERROR] Broken zipfile encountered for {os.path.basename(zip_path)} - {e}")
        except FileExistsError as e:
            Unzipper.update_log(
                f"[ERROR] File already exists, please delete the files first if reunzipping {os.path.basename(zip_path)} - {e}")
        except Exception as e:
            Unzipper.update_log(f"[ERROR] Error unzipping a file - {e}")
            CreateLogfile(log_directory, log_file_path).log_error(
                f"[ERROR] Error unzipping a file - {e}")
        else:
            Unzipper.update_log(f"[COMPLETED] {os.path.basename(zip_path)}")

    @classmethod
    def process_queue(cls):
        while True:
            try:
                zip_path = cls.queue.get(block=False)
            except queue.Empty:
                break

            cls.unzip(zip_path)
            cls.queue.task_done()


def main():
    # logger initialization
    logger = logging.getLogger('log')
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(log_file_path)
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)

    # CreateLogfile initialization
    log_directory = os.path.join(logpath, time.strftime("%d-%m-%Y"))
    unpacking_instance = CreateLogfile(log_directory, log_file_path)
    unpacking_instance.create_log_directory_and_file()

    # Check if new zip file appears and add it to unzip queue
    for zip_file in os.listdir(basepath):
        if zip_file.lower().endswith('.zip'):
            Unzipper.queue.put(os.path.join(basepath, zip_file))

    while True:
        if Unzipper.queue.empty():
            break

        new_zip_file = Unzipper.queue.get()
        Unzipper.queue.task_done()
        Unzipper.process_queue()


if __name__ == "__main__":
    main()
