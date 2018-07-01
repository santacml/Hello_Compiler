# from scanner import Scanner
from hc_typeCheck import *
from hc_irGenerator import IRGenerator

class ParseError(Exception): pass

class Pattern(object):
    def __init__(self, tokType, children, leaf=False):
        self.tokType = tokType
        self.children = children

        self.passedCheck = False
        self.resultType = self.tokType # default to this for leaf nodes??? I suppose?

        self.name = None # make this for ease in getting declarations
        self.arraySize = 0  # for array variables..?
        self.arrayStart = 0

        self.myList = [] # for both paramlist and arglist

        if leaf:
            # print("got leaf", self.tokType, children)
            self.children = [Pattern(children, None)]


        self.irHandle = None
        self.irHandleList = []

        self.parameterVal = None

        # only use if this pattern is a name and references an array
        # this is gross, not sure what else to do
        self.arrayExprIRHandle = None

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

        if grandParent and len(grandParent.children) == 2:
            # handle negative numbers
            possibleNeg = grandParent.children[0].children[0].tokType

            #because I made integer_num and float_num go down one more level
            possibleNum = grandParent.children[1].children[0].children[0].tokType

            if possibleNeg == "-":
                token = possibleNeg + possibleNum


        return token

class PatternMatcher(object):
    def __init__(self):

        self.patterns = {
            ("identifier", "lbracket", "expression", "rbracket"): "name",
            ("identifier",): "name",

            # i introduce these to make my life much easier
            ("integer_number",): "number",
            ("float_number",): "number",

            ("lparen", "expression", "rparen"): "factor",
            ("minus", "name"): "factor",
            ("name",): "factor",
            ("minus", "number"): "factor",
            ("number",): "factor",
            ("string_val",): "factor",
            ("char_val",): "factor",
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
            # IS THIS WRONG??????????
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

            ("for", "lparen","assignment_stmt", "semic"): "loop_open",
            ("loop_open", "expression", "rparen"): "loop_start",
            ("loop_start", "statement", "semic",): "loop_start",
            # ("end", "for",): "loop_end",
            ("loop_start", "end", "for",): "loop_stmt",

            ("return",): "return_stmt",

            # destination is redundant with name???
            # ("identifier","lbracket","expression","rbracket"): "destination",
            # ("identifier",): "destination",

            # ("if", "lparen", "expression", "rparen", "then", "statement", "semic",): "if_start",
            ("if", "lparen", "expression", "rparen", "then",): "if_start",  # get rid of stuff to catch stmts
            ("if_start", "statement","semic",): "if_start",
            # ("if_start", "else", "statement", "semic",): "else_start",
            ("if_start", "else", ): "else_start", # get rid of this to catch stmts
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
            ("procedure_header_w_vars", "declaration", "semic",): "procedure_header_w_vars",

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


            # ("loop_open", "assignment_stmt", "semic",): "__shift__", # prevent assignments getting sucked up
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

        self.enders =  (
            "rbracket",
            "semic",
            "period",
            "in",
            "out"
            "inout",
            "procedure_body",
            "is",



        )

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
    def __init__(self, scanner):
        self.currTokens = []
        self.patternMatcher = PatternMatcher()
        self.symTable = SymTable()
        # self.irGenerator = IRGenerator(symTable=self.symTable)

        self.scanner = scanner
    
    def getLineNumber(self):
        return self.scanner.getLineNumber()

    def parse(self):
        #self.scanner = scanner

        tokenGen = self.scanner.scan()
        currTok = next(tokenGen)
        currTok = Pattern(currTok[0],currTok[1], leaf=True)
        lookAhead = next(tokenGen)

        while(currTok is not None):
            # shift
            self.currTokens.append(currTok)

            # reduce
            # continuously yield the next token
            for tok in self.reduce(lookAhead):
                yield tok

            if lookAhead:
                currTok = Pattern(lookAhead[0], lookAhead[1], leaf=True)
            else:
                currTok = lookAhead

            lookAhead = next(tokenGen) if lookAhead is not None else None # now THAT's python

            #print(lookAhead)

        # print(self.currTokens)
        # print(tuple(tok[0] for tok in self.currTokens))

        validEndTypes = ["program", "block_comment", "comment"]
        endTokTypes = [tok.tokType for tok in self.currTokens]

        checkValid = [tokType in validEndTypes for tokType in endTokTypes]
        if False in checkValid:
            # badLoc = checkValid.index(False) # can put this in if stmt w/e
            # print(badLoc)
            # print(endTokTypes[badLoc])
            print(endTokTypes)
            # this sucks ass.......
            raise ParseError("Error parsing, could not figure out where.")


        # self.irGenerator.bindAndRun()
        # return self.currTokens


    def reduce(self, lookAheadTok):
        reduceable = True
        reduced = False # reduced once in a loop, gets reset

        onceReduced = False # something was reduced at least 1 time

        # needs to be here, multiple reduces in one reduce call IS possible
        while(reduceable):
            if reduced:
                reduced = False
                onceReduced = True

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
                
                yield newToken
                # typeCheck(newToken, self.scanner.LINE_NUMBER, self.symTable)
                # self.irGenerator.addIR(newToken)


                # print("reducing", pattern, "to", newToken.tokType)  # very important for debug
                
                self.currTokens = self.currTokens[:n]
                self.currTokens.append(newToken)
                reduced = True
                break

            if not reduced: reduceable = False


        # if not onceReduced:
            # tok = self.currTokens[-1].tokType
            # print(tok)
            # if tok in self.patternMatcher.enders:
                # raise ParseError("Parse error on line",  self.scanner.LINE_NUMBER)

            # check if last token added was in definite reduce list
            # if it was not then it's fine
            # if it was then err


# scanner = Scanner("test.src")
# tokens = Parser(scanner).parse()

# for tok in tokens:
    # print(tok.tokType)




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
