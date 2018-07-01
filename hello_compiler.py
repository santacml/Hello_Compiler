from hc_scanner import Scanner
from hc_parser import Parser
from hc_typeCheck import TypeChecker
from hc_irGenerator import IRGenerator

import sys
import os

class Compiler(object):
    def __init__(self, file):
        self.file = file
        self.scanner = Scanner(file)
        self.parser = Parser(self.scanner)
        self.typeChecker = TypeChecker(self.scanner, self.parser)
        self.irGenerator = IRGenerator(self.scanner, self.parser)

    def compile(self):
        tokStream = self.parser.parse()
        
        # parser will return a stream of tokens
        for tok in tokStream:
            self.typeChecker.typeCheck(tok)
            self.irGenerator.addIR(tok)
        
        self.irGenerator.bindAndRun()



if __name__ == "__main__":
    if len(sys.argv) == 2:
        file = sys.argv[1]
    else:
        file = "test.src"
        
    if not os.path.exists(file):
        print("Cannot find provided filepath (defaults to test.src if none provided)")
    else:
        compiler = Compiler(file)
        compiler.compile()
