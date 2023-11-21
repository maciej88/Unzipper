import os, zipfile, threading, time, logging, shutil
from queue import Queue

# basepath = r'//ktw-bs2/FQA/builds/'
# targetpath = r'//ktw-bd4/FQA/builds/'
# logpath = r"//ktw-bs2/FQA/builds/Logs"

basepath = r'/builds/'
targetpath = r'/builds/'
logpath = (r"/Logs")

thread_limit = 4  # set thread limit for unzipping (note that the script is running as a separate thread as well, meaning the amount of threads actually used is x+1).
# The operations are limited by the disk speed, so using more threads won't necessarily provide better results.

runtime = time.strftime("%H_%M_%S")

if not os.path.isdir(fr'{logpath}/{time.strftime("%d-%m-%Y")}'):
    try:
        os.mkdir(fr'{logpath}/{time.strftime("%d-%m-%Y")}')
    except Exception as e:
        try:
            with open(fr'{logpath}/{time.strftime("%d-%m-%Y")}/{runtime}.log', 'a') as logfile:
                logfile.write(str(e) + "\n")
        except:
            pass
try:
    # create session log
    f = open(fr'{logpath}/{time.strftime("%d-%m-%Y")}/{runtime}.log', 'x')
    f.close()
except FileExistsError:
    pass
except Exception as e:
    try:
        with open(fr'{logpath}/{time.strftime("%d-%m-%Y")}/{runtime}.log', 'a') as logfile:
            logfile.write(str(e) + "\n")
    except:
        pass

logger = logging.getLogger('log')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(fr'{logpath}/{time.strftime("%d-%m-%Y")}/{runtime}.log')
handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(handler)


def update_log(text, elapsed=""):
    if elapsed:
        elapsed = f"- Time elapsed: {elapsed}"
    try:
        logger.info(f"[{time.strftime('%H:%M:%S')}] {text} {elapsed}")
    except Exception as e:
        print(f"Error writing to file - {e}")
    print(text)


class Unzipper:
    queue = Queue()

    def unzip(self):
        update_log(f"[EXTRACTING] {self.path.name}")
        self.__start = time.time()
        try:
            with zipfile.ZipFile(self.unzip_path, 'r') as zip_ref:
                zip_ref.extractall(f"{targetpath}/{self.path.name[:-4]}")  # unzip the file
        except zipfile.BadZipFile as e:
            update_log(f"[ERROR] Broken zipfile encountered for {self.path.name} - {e}")
        except FileExistsError as e:
            update_log(
                f"[ERROR] File already exists, please delete the files first if reunzipping {self.path.name} - {e}")
        except Exception as e:
            update_log(f"[ERROR] Error unzipping a file - {e}")
        else:
            update_log(f"[COMPLETED] {self.path.name}", time.time() - self.__start)
            try:  # try creating a textfile
                f = open(f"{self.path.path.replace(self.path.name, '')}/unpacked.txt", 'x')
                f.close()
            except Exception as e:
                update_log(f"[ERROR] Error creating a file - {e}")

    def __init__(self, path):
        self.path = path
        self.__start = 0
        self.unzip_path = self.path.path
        Unzipper.queue.put(self)


def unzip_all():
    while not Unzipper.queue.empty():
        zip = Unzipper.queue.get()
        try:
            os.mkdir(f"{targetpath}/{zip.path.name[:-4]}")
        except FileExistsError as e:
            folder_count = len(os.listdir(path=f"{targetpath}/{zip.path.name[:-4]}"))
            if folder_count > 1:
                update_log(
                    f"[ERROR] Looks like the build was already unzipped; Dir Folder Count = {folder_count} - {e}")
                continue
        except Exception as e:
            update_log(f"[ERROR] Error creating folder for the zip - {e}")
            continue
        update_log(f"[COPY] Copying the zip file - {zip.path.name[:-4]}")
        copy_start = time.time()
        shutil.copyfile(zip.path.path, f"{targetpath}/{zip.path.name[:-4]}/{zip.path.name}")
        update_log(f"[COPY_COMPLETE] {zip.path.name[:-4]} - {time.time() - copy_start}")
        zip.unzip_path = f"{targetpath}/{zip.path.name[:-4]}/{zip.path.name}"
        zip.unzip()

        try:
            os.remove(f"{targetpath}/{zip.path.name[:-4]}/{zip.path.name}")
        except FileNotFoundError as e:
            update_log(f"[ERROR] Tried deleting zip after extracting but the file was already deleted - {e}")
        except Exception as e:
            update_log(f"[ERROR] Error removing the zip file - {e}")


def main():
    with os.scandir(basepath) as entries:
        for entry in entries:
            if not entry.is_dir():
                continue

            with os.scandir(basepath + entry.name) as subentries:  # scan each folder for files
                for subentry in subentries:
                    if not subentry.name.endswith(".zip"):
                        continue
                    if os.path.isfile(f"{basepath}{entry.name}/unpacked.txt"):
                        update_log(f"[INFO] Unzipped already - {subentry.name} ")
                        continue

                    Unzipper(subentry)

    for _ in range(thread_limit):
        _ = threading.Thread(target=unzip_all).start()


if __name__ == "__main__":
    main()