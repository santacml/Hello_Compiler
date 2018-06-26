from scanner import Scanner
from typeCheck import *
from irGenerator import IRGenerator
from parser import *

class Driver(object):
    def __init__(self, file):
        self.scanner = Scanner(file)
        self.parser = Parser(self.scanner)
        self.irGenerator = IRGenerator()

    def compile(self, file):
        parseGen = self.parser.parse(self.scanner)


        typeCheckGen = self.typeCheck(parseGen)
        irGen = self.irGenerator(typeCheckGen)




#scanner = Scanner("test.src")
#tokens = Parser().parse(scanner)
