import os

class TextUserInterface:
    pass

if __name__ == "__main__":
    rows, columns = os.popen("stty size", "r").read().split()
    print(rows, columns)
