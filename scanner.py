import os

'''
tokens:
number: [[0-9][0-9_]*[.[0-9_]*]
string: “[a-zA-Z0-9 _,;:.']*”
char:   '[a-zA-Z0-9 _;:.”]'
ident:  [a-zA-Z][a-zA-Z0-9_]*
ifstmt: if, then, else, end if
loop:   for, end for
expr:   &, |, not
arithm: +, -
destin: [, ]
term:   *, /
assign: :=
rltn:   <, >=, <=, >, ==, !=
factor: (,), true, false
type:   integer, float, bool, char
proc:   procedure
param:  in, out, inout
pbody:  begin, end procedure
body:   begin, end program
program:program, is
decl:   global

reserved words:
("if", "then", "else", "end", "for", "not", "true", "false", "integer", "float", "bool",
 "char", "procedure", "in", "out", "inout", "begin", "program", "is", "global")
'''
class ScanError(Exception): pass

alphabet = "abcdefghijklmnopqrstuvwxyz"
nums = "0123456789"


class StateMachine(object):
    def __init__(self, name):
        self.states = {}
        self.name = name
        self.currStr = ""
        self.ended = False
        
    def accept(self, newChar):
        # self.currChar = char
        nextState = None
        
        for key, state in self.states.items():
            # print("checking key", key)
            # print(newChar)
            if newChar in key:
                # print("found " + repr(newChar) + " in " + key)
                state.currStr = self.currStr + newChar
                nextState = state
                # self.currStr = ""  #doesn't matter->gets overwritten 2 lines above when it matters
        
        if not nextState:
            nextState = self
            self.ended = True
        
        return nextState
        
    def clear(self):
        self.currStr = ""
        self.ended = False
        
        
    def terminate(self, retVal=None):
        if not retVal: 
            retVal = (self.name, self.currStr) 
        self.clear()
        return retVal
        
class Identifier(StateMachine):
    def __init__(self):
        StateMachine.__init__(self, "identifier")
        self.states = {
            "_": self
        }
        for letter in alphabet:
            self.states[letter] = self
        for num in nums:
            self.states[num] = self
        
        self.keywords = ("if", "then", "else", "end", "for", "not", "true", "false", 
                         "integer", "float", "bool", "char", "procedure", "in", "out", "inout", 
                         "begin", "program", "is", "global",
                         "return")
        
    def terminate(self):
        retVal = None
        if self.currStr in self.keywords:
            retVal = (self.currStr, self.currStr)
        else:
            retVal =(self.name, self.currStr)
        
        return super().terminate(retVal)
        
class Number(StateMachine):
    def __init__(self):
        StateMachine.__init__(self, "number")
        self.states = {
            ".": DecimalNum()
        }

        for num in nums:
            self.states[num] = self
        
class DecimalNum(StateMachine):
    def __init__(self):
        StateMachine.__init__(self, "decimalnum")
        self.states = {}

        for num in nums:
            self.states[num] = self
        
class End(StateMachine):
    def __init__(self, name):
        StateMachine.__init__(self, name)
        
    def terminate(self):
        # print(self.currStr)
        if self.name == "char":
            if self.currStr[-1] is not "'":
                raise ScanError("Ending needs to match")
            if len(self.currStr) is not 3:
                raise ScanError("Char can only be one character")
                
        return super().terminate()
        
class String(StateMachine):
    def __init__(self):
        # DOES NOT ALLOW UNDERSCORE... ???
        StateMachine.__init__(self, "string")
        self.states = {
            " ": self,
            ",": self,
            ";": self,
            ":": self,
            ".": self,
            "'": self,
            "\"": End(self.name)
        }
        for letter in alphabet:
            self.states[letter] = self
        for num in nums:
            self.states[num] = self
        
    def terminate(self):
        raise ScanError("String must end with \"")
        
class Char(StateMachine):
    def __init__(self):
        StateMachine.__init__(self, "char")
        self.states = {
            "\'": End(self.name)
        }
        
        for letter in alphabet:
            self.states[letter] = self
        
    def terminate(self):
        raise ScanError("Char must end with '")
        
class Relation(StateMachine):
    def __init__(self, name):
        StateMachine.__init__(self, name)
        self.states = {
            "=": End(self.name + "equal")
        }
    
    def terminate(self):
        if self.name == "not":
            raise ScanError("NotEqual must be exactly '!='")
        return super().terminate()
        
class Assignment(StateMachine):
    def __init__(self):
        StateMachine.__init__(self, "assignment")
        self.states = {
            "=": End("assignment")
        }
        
    def terminate(self):
        raise ScanError("Assignment must be exactly ':='")
        
class DivideOrComment(StateMachine):
    def __init__(self):
        StateMachine.__init__(self, "divide")
        self.states = {}
        self.acceptedOneChar = False
        
    def accept(self, newChar):
        nextState = None
        if not self.acceptedOneChar:
            
            #only goes in here once 
            self.acceptedOneChar = True
            # possibly a comment, need to check
            if newChar == "/":
                # we have found a comment! //
                self.name = "comment"
                self.currStr = self.currStr + newChar
                nextState = self
            elif newChar == "*":
                # found a block comment opening! /* 
                self.acceptedOneChar = False
                nextState = BlockComment()
                # next str is /*
                nextState.currStr = self.currStr + newChar
            else:
                # next char is something else, so this is a divide
                self.acceptedOneChar = False
                nextState = End("divide")
                nextState.currStr = "/"
                nextState.ended = True
        else:
            #this will only happen if we are in a single line comment
            #accept everything, forever
            self.currStr = self.currStr + newChar
            nextState = self
        
        return nextState
        
    def terminate(self):
        self.acceptedOneChar = False
        return super().terminate()
        
class BlockComment(StateMachine):
    def __init__(self):
        StateMachine.__init__(self, "block_comment")
        self.states = {}
        self.level = 1
        self.upLevelStart = False
        self.downLevelStart = False
        self.endNextPass = False
        
    def accept(self, newChar):
        nextState = self
        
        if self.endNextPass:
            self.ended = True
            return nextState
        
        if self.upLevelStart:
            # check if adding a new level
            if newChar == "*":
                self.level += 1
            self.upLevelStart = False
        elif self.downLevelStart:
            # check if going down a level
            if newChar == "/":
                self.level -= 1
                
                if self.level == 0: self.endNextPass = True
            self.downLevelStart = False
        else:
            if newChar == "/":
                self.upLevelStart = True
            elif newChar == "*":
                self.downLevelStart = True
        
        
        self.currStr = self.currStr + newChar
        return nextState

class MasterMachine(StateMachine):
    def __init__(self):
        StateMachine.__init__(self, "do not see")
        self.states = {
            "\"": String(),
            "'": Char(),
            ":": Assignment(),
            "/": DivideOrComment(),
            "<": Relation("less"),
            ">": Relation("greater"),
            "=": Relation("equal"),
            "!": Relation("not"),
            "*": End("multiply"),
            "[": End("lbracket"),
            "]": End("rbracket"),
            "&": End("and"),
            "|": End("or"),
            "-": End("minus"),
            "+": End("plus"),
            "(": End("lparen"),
            ")": End("rparen"),
            ";": End("semic"),
            ".": End("period"),
            ",": End("comma"),
        }
        for letter in alphabet:
            self.states[letter] = Identifier()
        for num in nums:
            self.states[num] = Number()
        
    def clear(self):
        self.currStr = ""
        self.ended = False
        return self
        
# with open("test.src", 'r', newline="\n") as f:
class Scanner(object):
    def __init__(self, file):
        self.file = file
        
    def scan(self):
        with open(self.file, 'rb') as f:
            currLine = 0
            masterMachine = MasterMachine()
            machine = masterMachine.clear()
            for line in f:
                currCol = 0
                try:
                    if not (machine.name == "block_comment"):
                        # if we are in a block comment, persist, otherwise reset
                        machine = masterMachine.clear()
                    
                    currLine += 1
                    line = line.lower()
                    # replace with bytes as file open in byte format
                    line = line.replace(b"\t", b" ")
                    # print(repr(line))
                    
                    for char in line.decode('ascii'):
                        currCol += 1
                        if char in ("\r\n", "\r", "\n"): continue #gets rid of newlines!
                        
                        # print("now accepting", char)
                        machine = machine.accept(char)
                        
                        if machine.ended: 
                            # print(machine.ended, machine.currStr, char)
                            if machine.currStr:
                                # tokens.append(machine.terminate())
                                yield machine.terminate()
                            
                            
                            machine = masterMachine.clear().accept(char)
                            if not machine.currStr and char is not " " :  
                                # token not found, also discard whitespace
                                raise ScanError("Unexpected Token", char)
                                
                            # print("made new machine with: " + char)
                    
                    
                    # at end of line, terminate machine
                    if not (machine.name == "block_comment") and machine.currStr:
                        # tokens.append(machine.terminate())
                        yield machine.terminate()
                        
                except ScanError as e:
                    print("Encountered error while scanning line: " + str(currLine )+ ".")
                    print(e)
                    print(line.decode('ascii'), " " * (currCol-2) + "^")
                    print()
                    return
                    
            # this is specifically for files that end in a block comment... 
            # I guess I don't really need this...
            if (machine.name == "block_comment") and machine.currStr:
                yield machine.terminate()
            
        yield
        yield
        
    def oldScan(self):
        tokens = []
        with open(self.file, 'rb') as f:
            currLine = 0
            masterMachine = MasterMachine()
            machine = masterMachine.clear()
            for line in f:
                currCol = 0
                try:
                    if not (machine.name == "block_comment"):
                        # if we are in a block comment, persist, otherwise reset
                        machine = masterMachine.clear()
                    
                    currLine += 1
                    line = line.lower()
                    # replace with bytes as file in byte format
                    line = line.replace(b"\t", b" ")
                    # print(repr(line))
                    
                    for char in line.decode('ascii'):
                        currCol += 1
                        if char in ("\r\n", "\r", "\n"): continue #gets rid of newlines!
                        
                        # print("now accepting", char)
                        machine = machine.accept(char)
                        
                        if machine.ended: 
                            # print(machine.ended, machine.currStr, char)
                            if machine.currStr:
                                tokens.append(machine.terminate())
                            
                            
                            machine = masterMachine.clear().accept(char)
                            if not machine.currStr and char is not " " :  
                                # token not found, also discard whitespace
                                raise ScanError("Unexpected Token", char)
                                
                            # print("made new machine with: " + char)
                    
                    
                    # at end of line, terminate machine
                    if not (machine.name == "block_comment") and machine.currStr:
                        tokens.append(machine.terminate())
                        
                except ScanError as e:
                    print("Encountered error while scanning line: " + str(currLine )+ ".")
                    print(e)
                    print(line.decode('ascii'), " " * (currCol-2) + "^")
                    print()
                    return
                    
            # this is specifically for files that end in a block comment... 
            # I guess I don't really need this...
            if (machine.name == "block_comment") and machine.currStr:
                tokens.append(machine.terminate())
            
        return tokens

# tokenGen = Scanner("test.src").scan()
# tok = next(tokenGen)
# while (tok is not None):
    # print(tok)
    # tok = next(tokenGen)

# tokens = Scanner("test.src").oldScan()
# for token in tokens: print(token)







