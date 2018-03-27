from scanner import Scanner
        
class ParseError(Exception): pass
class TypeCheckError(Exception): pass
        
class Pattern(object):
    def __init__(self, tokType, children, leaf=False):
        self.tokType = tokType
        self.children = children
        
        self.passedCheck = False
        self.resultType = self.tokType # default to this for leaf nodes??? I suppose?
        
        if leaf:
            # print("got leaf", self.tokType, children)
            self.children = [Pattern(children, None)]
        
    def typeCheck(self, LINE_NUMBER, symTable):
        # if self.children:
            # print(self.tokType)
            # for child in self.children:
                # child.typeCheck()
        # else:
            # print(self.tokType)
        
        lineErrStart = "Error on line: " + str(LINE_NUMBER) + ":\n"
        tokType = self.tokType
        numChildren = len(self.children)
        status = True
        
        
        # all of these are the same for numChildren == 1 case
        # just assign resultType as the encapsulated item's resultType
        if tokType in ["factor", "term", "relation", "arithOp", "expression"] and numChildren == 1:
            bools = ["true", "false"]
            self.resultType = self.children[0].resultType
            # print("setting result type", tokType, self.children[0].resultType)
            if self.resultType in bools: self.resultType = "bool"
            
        elif tokType == "name":
            name = self.children[0].children[0].resultType
            
            if not name in symTable:
                raise TypeCheckError(lineErrStart + "Variable or procedure not found.")
            
            self.resultType = tokType
            
        elif tokType == "factor":
            # covers 2 and 3
            
            self.resultType = self.children[1].tokType
                
        elif tokType == "term":
            type1 = self.children[0].resultType
            type2 = self.children[2].resultType
            
            if type1 == type2:
                if type1 != "number": raise TypeCheckError(lineErrStart + "Can only divide or multiply numbers.")
                self.resultType = type1
            else:
                print(type1)
                print(type2)
                raise TypeCheckError(lineErrStart + "Types do not match for division or multiplication.")
                
        elif tokType == "relation":
            relationTypes = ["number", "bool"]
            type1 = self.children[0].resultType
            type2 = self.children[2].resultType
            
            if not type1 in relationTypes or not type2 in relationTypes: 
                raise TypeCheckError(lineErrStart + "Relations can only compare numbers and bools.")
                
            self.resultType = "bool"
            
        elif tokType == "arithOp":
            type1 = self.children[0].resultType
            type2 = self.children[2].resultType
            
            if type1 != "number" or type2 != "number":
                raise TypeCheckError(lineErrStart + "Arithmetic Ops can only operate on numbers.")
                
            self.resultType = "number"
            
        elif tokType == "expression":
            exprTypes = ["bool", "number"]
            
            if numChildren == 2:
                self.resultType = self.children[1].resultType
                
            elif numChildren == 3:
                type1 = self.children[0].resultType
                type2 = self.children[2].resultType
                if type1 in exprTypes and type2 in exprTypes: 
                    self.resultType = "bool"
                else:
                    raise TypeCheckError(lineErrStart + "Expression can only operate on numbers and bools.")
            
        elif tokType == "argument_list":
            pass
            
        elif tokType == "procedure_header":
            symTable.enter()
            
        elif tokType == "procedure_declaration":
            symTable.exit()
            
        elif tokType == "variable_declaration":
            declType = self.children[0].children[0].tokType
            name = self.children[1].children[0].tokType
            arraySize=0
            arrayStart=0
            if numChildren == 2:
                pass
            elif numChildren == 7:
                # 5:10, already knows they are numbers
                start = self.children[3].children[0].resultType 
                end = self.children[5].children[0].resultType 
                print(start)
                print(end)
                start = int(start)
                end = int(end)
                
                arraySize = end - start
                arrayStart = start
                
            elif numChildren == 5:
                if self.children[3].resultType != "number":
                    raise TypeCheckError(lineErrStart + "Array must be declared with a range or size.")
                
                token = self.grabLeafValue(3)
                    
                print(token)
                arraySize = int(token)
                
            symTableItem = SymTableItem(declType, arraySize, arrayStart)
            symTable.declare(name, symTableItem)
                
                
        # todo: 
            # procedures in symtable, arglist checking, descent to negative num!
            
        elif tokType == "declaration":
            # need to handle global, local, procedure and var
            pass
        elif tokType == "procedure_call":
            pass
        
        self.passedCheck = status
        
        self.patterns = {
            
            ("expression", "comma", "expression"): "argument_list",    # need to shift something
            ("argument_list", "comma", "expression"): "argument_list",    #would result in errors. instead, try shifting
            
            ("identifier", "lparen", "argument_list", "rparen",): "procedure_call",
            # this way, not all expressions are arglists. makes life easier
            ("identifier", "lparen", "expression", "rparen",): "procedure_call", 
            # can call procedure without args dummy
            ("identifier", "lparen", "rparen",): "procedure_call", 
            
            ("name", "assignment", "expression"): "assignment_stmt",
            
            ("for", "lparen", "assignment_stmt", "semic", "expression", "rparen"): "loop_start",
            ("loop_start", "statement", "semic",): "loop_start",
            ("loop_start", "end", "for",): "loop_stmt",
            
            ("return",): "return_stmt",
            
            # destination is redundant with name???
            # ("identifier","lbracket","expression","rbracket"): "destination",
            # ("identifier",): "destination",
            
            ("if", "lparen", "expression", "rparen", "then", "statement", "semic",): "if_start",
            ("if_start", "statement","semic",): "if_start",
            ("if_start", "else", "statement", "semic",): "else_start",
            ("else_start", "statement", "semic",): "else_start",
            ("if_start", "end", "if",): "if_stmt",
            ("else_start", "end", "if"): "if_stmt",
            
            ("assignment_stmt",): "statement",
            ("if_stmt",): "statement",
            ("loop_stmt",): "statement",
            ("return_stmt",): "statement",
            ("procedure_call",): "statement",
            
            ("integer",): "type_mark",
            ("float",): "type_mark",
            ("string",): "type_mark",
            ("bool",): "type_mark",
            ("char",): "type_mark",
            
            # could mess around with lower/upper bound, no real point
            ("type_mark", "identifier"): "variable_declaration",
            ("type_mark", "identifier","lbracket", "number", "colon", "number", "rbracket"): "variable_declaration",
            ("type_mark", "identifier","lbracket", "expression", "rbracket"): "variable_declaration",
            # do bounds always have to be numbers...?
            
            
            
            ("begin",): "procedure_body_start",
            ("procedure_body_start", "statement", "semic",): "procedure_body_start",
            ("procedure_body_start", "end", "procedure",): "procedure_body",
            
            ("variable_declaration", "in",): "parameter",
            ("variable_declaration", "out",): "parameter",
            ("variable_declaration", "inout",): "parameter",
            
            ("parameter",): "parameter_list",
            ("parameter_list", "comma", "parameter"): "parameter_list",
            
            ("procedure", "identifier", "lparen", "rparen",): "procedure_header",
            ("procedure", "identifier", "lparen", "parameter_list","rparen"): "procedure_header",
            # takes care of  declarations before procedure
            # and name differently to allow increasing sym table only once
            ("procedure_header", "declaration", "semic",): "procedure_header_w_vars", 
            
            ("procedure_header", "procedure_body",): "procedure_declaration",
            ("procedure_header_w_vars", "procedure_body",): "procedure_declaration",
            
            ("global", "procedure_declaration",): "declaration",
            ("global", "variable_declaration",): "declaration",
            ("procedure_declaration",): "declaration",
            ("variable_declaration",): "declaration",
            
            # all programs are procedures until the end?
            ("procedure_body_start", "end", "program",): "program_body", 
            
            # this doesn't work - when do we shift vs. reduce? (might reduce identifier)
            # ( i guess I could shift)
            # (whatever fuck it)
            # ("program", "identifier", "is",): "program_header",
            # this way, identifier isn't caught between shift and reduce
            ("program", "identifier",): "program_header_start",
            ("program_header_start", "is"): "program_header",
            
            ("program_header", "declaration", "semic",): "program_header",
            
            ("program_header", "program_body", "period"): "program",
        }
        
    def grabLeafValue(self, childLoc):
        # if we know this is just some encapsulated number or other such value
        #  descend until the number is obtained
        grandParent = None
        parent = self.children[childLoc]
        child = self.children[childLoc].children[0]
        while child.children:
            grandParent = parent
            parent = child
            child = parent.children[0]
        
        token = child.tokType
        
        if len(grandParent.children) == 2:
            # handle negative numbers
            possibleNeg = grandParent.children[0].children[0].tokType
            possibleNum = grandParent.children[1].children[0].tokType
            
            if possibleNeg == "-":
                token = possibleNeg + possibleNum
             
        
        return token
        
    # def __str__(self):
        # if self.children:
            # return (self.tokType, [str(child) for child in self.children])
        
        # return (self.tokType, None)
        
# this makes it so that multiple things can have reference to same value?
class SymTableItem(object):
    def __init__(self, valType, arraySize, arrayStart):
        self.valType = valType
        if not arraySize: self.arrayType = False # false unless >0
        self.arraySize = arraySize
        self.arrayStart = arrayStart
        

class SymTable(object):
    def __init__(self):
        self.rootScope = {}
        self.scopes = []
        self.currScope = None
        
    def exit(self):
        # i can delete scopes and it's fine
        # anything that has references to the items will still have them
        del self.scopes[-1]
        
        if len(self.scopes) > 0:
            self.currScope = self.scopes[-1]
        else:
            self.currScope = None
        
    def enter(self):
        self.scopes.append({})
        self.currScope = self.scopes[-1]
        
    def __getitem__(self, key):
        item = None
        if not (self.currScope == None):
            item = self.currScope.get(key, None)
        if not item:
            item = self.rootScope.get(key, None)
        if not item:
            print("Could not find symbol.")
            print("Could not find symbol.")
            
        return item
    
    # def __setitem__(self, key, value, valType, arrayType=False):
        # if not (self.currScope == None):
            # self.currScope[key] = SymTableItem(value, valType, arrayType)
        # else:
            # self.rootScope[key] = SymTableItem(value, valType, arrayType)
        
    def declare(self, key, symTableItem):
        # use none as default value
        if self.currScope:
            self.currScope[key] = symTableItem 
            # print("insert", key, valType, "into currScope")
        else:
            self.rootScope[key] = symTableItem
            # print("insert", key, valType, "into rootScope")
        
    def __contains__(self, key):  
        contained = False
        if self.currScope:
            if key in self.currScope: contained = True
        
        if key in self.rootScope: contained = True
        
        return contained

        
class PatternMatcher(object):
    def __init__(self):
        
        self.patterns = {
            ("identifier", "lbracket", "expression", "rbracket"): "name",
            ("identifier",): "name",
            
            ("lparen", "expression", "rparen"): "factor",
            ("minus", "name"): "factor",
            ("name",): "factor",
            ("minus", "number"): "factor",
            ("number",): "factor",
            ("string",): "factor",
            ("char",): "factor",
            ("true",): "factor",
            ("false",): "factor",
            
            ("term", "multiply", "factor"): "term",
            ("term", "divide", "factor"): "term",
            ("factor",): "term",
            
            ("relation", "less", "term"): "relation",
            ("relation", "lessequal", "term"): "relation",
            ("relation", "greater", "term"): "relation",
            ("relation", "greaterequal", "term"): "relation",
            ("relation", "equalequal", "term"): "relation",
            ("relation", "notequal", "term"): "relation",
            ("term",): "relation",
            
            ("arithOp", "plus", "relation"): "arithOp",
            ("arithOp", "minus", "relation"): "arithOp",
            ("arithOp", "minus", "number"): "arithOp", # gross
            ("arithOp", "minus", "name"): "arithOp",   # but this fixes it? I guess?
            ("relation",): "arithOp",
            
            ("expression", "and", "arithOp"): "expression",
            ("expression", "or", "arithOp"): "expression",
            ("not", "arithOp"): "expression",
            ("arithOp",): "expression",
            
            ("expression", "comma", "expression"): "argument_list",    # need to shift something
            ("argument_list", "comma", "expression"): "argument_list",    #would result in errors. instead, try shifting
            
            ("identifier", "lparen", "argument_list", "rparen",): "procedure_call",
            # this way, not all expressions are arglists. makes life easier
            ("identifier", "lparen", "expression", "rparen",): "procedure_call", 
            # can call procedure without args dummy
            ("identifier", "lparen", "rparen",): "procedure_call", 
            
            ("name", "assignment", "expression"): "assignment_stmt",
            
            ("for", "lparen", "assignment_stmt", "semic", "expression", "rparen"): "loop_start",
            ("loop_start", "statement", "semic",): "loop_start",
            ("loop_start", "end", "for",): "loop_stmt",
            
            ("return",): "return_stmt",
            
            # destination is redundant with name???
            # ("identifier","lbracket","expression","rbracket"): "destination",
            # ("identifier",): "destination",
            
            ("if", "lparen", "expression", "rparen", "then", "statement", "semic",): "if_start",
            ("if_start", "statement","semic",): "if_start",
            ("if_start", "else", "statement", "semic",): "else_start",
            ("else_start", "statement", "semic",): "else_start",
            ("if_start", "end", "if",): "if_stmt",
            ("else_start", "end", "if"): "if_stmt",
            
            ("assignment_stmt",): "statement",
            ("if_stmt",): "statement",
            ("loop_stmt",): "statement",
            ("return_stmt",): "statement",
            ("procedure_call",): "statement",
            
            ("integer",): "type_mark",
            ("float",): "type_mark",
            ("string",): "type_mark",
            ("bool",): "type_mark",
            ("char",): "type_mark",
            
            # could mess around with lower/upper bound, no real point
            ("type_mark", "identifier"): "variable_declaration",
            ("type_mark", "identifier","lbracket", "number", "colon", "number", "rbracket"): "variable_declaration",
            ("type_mark", "identifier","lbracket", "expression", "rbracket"): "variable_declaration",
            # do bounds always have to be numbers...?
            
            
            
            ("begin",): "procedure_body_start",
            ("procedure_body_start", "statement", "semic",): "procedure_body_start",
            ("procedure_body_start", "end", "procedure",): "procedure_body",
            
            ("variable_declaration", "in",): "parameter",
            ("variable_declaration", "out",): "parameter",
            ("variable_declaration", "inout",): "parameter",
            
            ("parameter",): "parameter_list",
            ("parameter_list", "comma", "parameter"): "parameter_list",
            
            ("procedure", "identifier", "lparen", "rparen",): "procedure_header",
            ("procedure", "identifier", "lparen", "parameter_list","rparen"): "procedure_header",
            # takes care of  declarations before procedure
            # and name differently to allow increasing sym table only once
            ("procedure_header", "declaration", "semic",): "procedure_header_w_vars", 
            
            ("procedure_header", "procedure_body",): "procedure_declaration",
            ("procedure_header_w_vars", "procedure_body",): "procedure_declaration",
            
            ("global", "procedure_declaration",): "declaration",
            ("global", "variable_declaration",): "declaration",
            ("procedure_declaration",): "declaration",
            ("variable_declaration",): "declaration",
            
            # all programs are procedures until the end?
            ("procedure_body_start", "end", "program",): "program_body", 
            
            # this doesn't work - when do we shift vs. reduce? (might reduce identifier)
            # ( i guess I could shift)
            # (whatever fuck it)
            # ("program", "identifier", "is",): "program_header",
            # this way, identifier isn't caught between shift and reduce
            ("program", "identifier",): "program_header_start",
            ("program_header_start", "is"): "program_header",
            
            ("program_header", "declaration", "semic",): "program_header",
            
            ("program_header", "program_body", "period"): "program",
        }
        
        self.shiftTable = {
            ("name", "assignment",): "__shift__", # for destination/assignment
            ("identifier", "lbracket",): "__shift__", # to make sure names suck up vars[5]
            
            # prevent terms getting sucked up
            ("term", "multiply",): "__shift__", 
            ("term", "divide", ): "__shift__", 
            
            # prevent relations getting sucked up
            ("relation", "less",  ): "__shift__",
            ("relation", "lessequal", ): "__shift__",
            ("relation", "greater", ): "__shift__",
            ("relation", "greaterequal", ): "__shift__",
            ("relation", "equalequal", ): "__shift__",
            ("relation", "notequal", ): "__shift__",
            
            # arithOps
            ("arithOp", "plus", ): "__shift__",
            ("arithOp", "minus", ): "__shift__",
            
            # argList
            ("expression", "comma",): "__shift__",
            
            ("for", "lparen", "assignment_stmt", "semic",): "__shift__", # prevent assignments getting sucked up
            # ("for", "lparen", "assignment_stmt", "semic", "statement", "rparen"): "__shift__", # prevent statement getting sucked up
            
            ("if", "lparen", "expression", "rparen","then",): "__shift__",
            
            ("type_mark", "identifier","lbracket", "number",): "__shift__", # need to shift so number isn't sucked up
            ("type_mark", "identifier","lbracket",): "__shift__", # need to shift so identifier isn't sucked up
            
            ("procedure", "identifier", "lparen",): "__shift__", # stop identifiers from becoming names
            
            ("variable_declaration", "in",): "__shift__",
            ("variable_declaration", "out",): "__shift__",
            ("variable_declaration", "inout",): "__shift__",
            
            ("identifier", "lparen",): "__shift__", # for procedure calls
        }
        
        
    def match(self, pattern, lookAheadTok):
        matched = self.patterns.get(pattern, False) 
        # if lookAheadTok and lookAheadTok[0] in self.lookAheadTable and self.lookAheadTable[lookAheadTok[0]] == pattern:
            # matched = False
            # print("performed lookahead", pattern, lookAheadTok)
        if lookAheadTok:
            lookAheadPattern = pattern + (lookAheadTok[0],)
            # print("looking ahead for", lookAheadPattern)
            
            lookAhead = self.shiftTable.get(lookAheadPattern, False) 
            if lookAhead == "__shift__":
                matched = "__shift__"
                # print("FOUND LOOKAHEAD, USING SHIFT", lookAheadPattern)
        
        return matched
        
class Parser(object):
    def __init__(self):
        self.currTokens = []
        self.patternMatcher = PatternMatcher()
        self.symTable = SymTable()
        
        self.scanner = None 
        
    def parse(self, scanner):
        self.scanner = scanner
        tokenGen = scanner.scan()
        currTok = next(tokenGen)
        currTok = Pattern(currTok[0],currTok[1], leaf=True)
        lookAhead = next(tokenGen)
        
        while(currTok is not None):
            # shift
            self.currTokens.append(currTok)
            
            # reduce 
            self.reduce(lookAhead)
            # print(self.currTokens)
            
            if lookAhead:
                currTok = Pattern(lookAhead[0], lookAhead[1], leaf=True)
            else:
                currTok = lookAhead
            lookAhead = next(tokenGen) if lookAhead is not None else None # now THAT's python
            # print(lookAhead)
            # print(scanner.LINE_NUMBER)
            
        # print(self.currTokens)
        # print(tuple(tok[0] for tok in self.currTokens))
        
        return self.currTokens
        
            
    def reduce(self, lookAheadTok):
        reduceable = True
        reduced = False
        err = False  # do this later... for now, blindly accept everything is A-OK
        
        # needs to be here, multiple reduces in one reduce call IS possible
        while(reduceable):
            if reduced: reduced = False
            # for n in range(len(self.currTokens)-1, -1,-1):
            for n in range(0,len(self.currTokens)):  
                # pattern = tuple(tok[0] for tok in self.currTokens[n:]) 
                pattern = tuple(tok.tokType for tok in self.currTokens[n:]) #idk if this works
                
                # print("pattern: ", pattern)  # very important for debug
                
                matched = self.patternMatcher.match(pattern, lookAheadTok)
                
                # collapse this if stmt, just continue if no match
                # maybe do some error handling here instead?
                # if matched:
                if not matched: continue
                
                # if shift, stop everything and allow loop to break
                if matched == "__shift__":
                    reduceable = False
                    break
                
                # newToken = (matched, self.currTokens[n:],)
                
                newToken = Pattern(matched, self.currTokens[n:])
                newToken.typeCheck(self.scanner.LINE_NUMBER, self.symTable)
                
                # I guess here I'm supposed to actually DO something with the matched tokens
                # instead of storing them
                # something something type checking something something code gen
                
                # print("reducing", pattern, "to", newToken.tokType)  # very important for debug
                
                
                
                self.currTokens = self.currTokens[:n]
                self.currTokens.append(newToken)
                reduced = True
                break
                    
            if not reduced: reduceable = False
            
    

scanner = Scanner("test.src")
tokens = Parser().parse(scanner)

for tok in tokens:
    print(tok.tokType)
    # tok.typeCheck()


'''
# My symbol table is A++

# proves the theory works. yay!
# can just hand off items
test = SymTableItem(5)
test2 = test

test2.value = 6
print(test2.value)
print(test.value)


# proves objects exist after deletion
# and additionally keep value
test = {"X": SymTableItem(5)}
test2 = test["X"]

test2.value = 6
del test
print(test2.value)
# print(test.value)
'''






