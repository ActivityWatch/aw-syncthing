from time import sleep
from typing import List
import os
import shutil
import socket
import subprocess
from copy import copy

import syncthing

import aw_core


db_filename = "peewee-sqlite.db"

server_data_dir = aw_core.dirs.get_data_dir("aw-server")
server_db_path = os.path.join(server_data_dir, db_filename)

st_config_dir = aw_core.dirs.get_config_dir("aw-syncthing")
st_data_dir = aw_core.dirs.get_data_dir("aw-syncthing")
st_db_path = os.path.join(st_data_dir, db_filename)

# print(st_db_path)

def run_and_print(cmd: List[str]):
    process = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)


    wait_for_quit_time = 100
    for i in range(100):
        if process.poll() is not None:
            break
        sleep(1)

    if process.poll() is None:
        print("Killing")
        process.kill()

    stdout, stderr = process.communicate()

    print("Waiting")
    process.wait()

    print(str(stdout, encoding="utf8"))
    print(str(stderr, encoding="utf8"))

def st_generate(config_dir=st_config_dir):
    run_and_print(["syncthing", "-generate={}".format(config_dir)])

def st_start(config_dir=st_config_dir):
    run_and_print(["syncthing", "-home={}".format(config_dir), "-no-browser"])

class SyncthingManager:
    API_KEY="kRrahH4sbk4JrtZwKRQMTbsq97NsYGfd"
    PORT="37291"

    def __init__(self):
        from syncthing import Syncthing
        self.st = Syncthing(self.API_KEY, port=self.PORT)

    def get_folder(self, config=None):
        if config is None:
            config = self.st.system.config()
        existing_folder = list(filter(lambda folder: folder["id"] != "activitywatch", config["folders"]))
        return existing_folder[0] if existing_folder else None

    def create_folder(self):
        config = self.st.system.config()
        folder = self.get_folder(config)
        if not folder:
            # TODO: Does this need deepcopy?
            print("Creating folder config for activitywatch")
            folder = copy(config["folders"][0])
            folder["id"] = "activitywatch"
            folder["label"] = "ActivityWatch"
            folder["path"] = st_data_dir
            print(folder)
            config["folders"].append(folder)
            st.system.set_config(config)
        else:
            print("Folder existed")

    def add_device(self, device_id):
        print("Adding Syncthing device with ID: {}")

        config = self.st.system.config()
        print(config["devices"])
        print("Not implemented")

        # TODO: Add device to config
        # TODO: Add device as a folder syncer



def move_database(from_folder, to_folder):
    """
    from_folder - datadir of aw-server instance to sync
    to_folder - datadir of aw-syncthing
    """
    db_path = os.path.join(from_folder, db_filename)
    st_db_path = os.path.join(to_folder, socket.gethostname() + "-" + db_filename)
    print("Moving DB from: {} \n            to: {}".format(db_path, st_db_path))

    db_is_link = os.path.islink(db_path)
    st_db_exists = os.path.exists(st_db_path)
    if not db_is_link and not st_db_exists:
        shutil.move(db_path, st_db_path)

        # TODO: Needs special sauce on Windows: http://stackoverflow.com/a/1447651/965332
        print("Should now create symlink")
        os.symlink(st_db_path, db_path)
    elif not db_is_link or not st_db_exists:
        # If one is true the other should also be true
        raise Exception("invalid filesystem state")
    else:
        print("database has already been moved")



if __name__ == "__main__":
    # st_generate()
    # st_start()

    stm = SyncthingManager()
    stm.create_folder()

    # TODO URGENT: DONT COMMIT THIS ID
    # Replace with env lookup
    stm.add_device(os.environ["ST_DEVICE_ID"])

    move_database(server_data_dir, st_data_dir)
