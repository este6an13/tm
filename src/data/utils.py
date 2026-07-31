from os import remove
from shutil import rmtree


def cleanup(folders=None, files=None):
    if folders is not None:
        for folder in folders:
            rmtree(folder)
    if files is not None:
        for file in files:
            remove(file)
