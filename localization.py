
from pathlib import Path

class Localization():
    def __init__(self, language):

        self.string = {}
        try:
            f = open(f"{language}.txt", "r", encoding="utf-8")

            for line in f:
                l = line.replace('\n', '')
                tokens = l.split("=")
                if(len(tokens) == 2):
                    self.string[tokens[0]] = tokens[1]
                    
        except Exception as ex:
            print (ex)
