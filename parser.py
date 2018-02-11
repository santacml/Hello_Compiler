from scanner import Scanner
        
'''

//////goal -> expr   fix me i guess?
expr -> expr + factor
     | expr - factor
     | factor

factor -> num | id

x -> factor -> expr
+ -> expr +
y -> expr + factor -> expr
and so on
'''



class Patterns(object):
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
            
            ("name", "assignment", "expression"): "assignment_stmt",
            
            ("for", "lparen", "assignment_stmt", "semic", "statement", "rparen"): "loop_start",
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
            ("procedure_header", "declaration", "semic",): "procedure_header", 
            
            ("procedure_header", "procedure_body",): "procedure_declaration",
            
            ("global", "procedure_declaration",): "declaration",
            ("global", "variable_declaration",): "declaration",
            ("procedure_declaration",): "declaration",
            ("variable_declaration",): "declaration",
            
            # all programs are procedures until the end?
            ("procedure_body_start", "end", "program",): "program_body", 
            
            # this doesn't work - when do we shift vs. reduce? (might reduce identifier)
            # ( i guess I could shift)
            # (whatever fuck you)
            # ("program", "identifier", "is",): "program_header",
            # this way, identifier isn't caught between shift and reduce
            ("program", "identifier",): "program_header_start",
            ("program_header_start", "is"): "program_header",
            
            ("program_header", "declaration", "semic",): "program_header",
            
            ("program_header", "program_body", "period"): "program",
        }
        
        self.shiftTable = {
            ("name", "assignment",): "__shift__", # for destination/assignment
            
            ("term", "multiply",): "__shift__", 
            ("term", "divide", ): "__shift__", 
            
            ("relation", "less",  ): "__shift__",
            ("relation", "lessequal", ): "__shift__",
            ("relation", "greater", ): "__shift__",
            ("relation", "greaterequal", ): "__shift__",
            ("relation", "equalequal", ): "__shift__",
            ("relation", "notequal", ): "__shift__",
            
            ("arithOp", "plus", ): "__shift__",
            ("arithOp", "minus", ): "__shift__",
            
            ("expression", "comma",): "__shift__",
            
            ("if", "lparen", "expression", "rparen","then",): "__shift__",
            
            ("type_mark", "identifier","lbracket", "number",): "__shift__", # need to shift so number isn't sucked up
            
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
                print("FOUND LOOKAHEAD, USING SHIFT", lookAheadPattern)
        
        return matched
        
        
class Parser(object):
    def __init__(self):
        self.currTokens = []
        # self.treeNode = Node("root", None) 
        self.treeNode = None
        self.patterns = Patterns()
        self.currNodes = []
        
    def parse(self, tokenGen):
        currTok = next(tokenGen)
        lookAhead = next(tokenGen)
        
        while(currTok is not None):
            self.currTokens.append(currTok)
            self.reduce(lookAhead)
            # print(self.currTokens)
            
            currTok = lookAhead
            lookAhead = next(tokenGen) if lookAhead is not None else None # now THAT's python
        
            
        print(self.currTokens)
        # self.printAll(self.currTokens)
        print(tuple(tok[0] for tok in self.currTokens))
        
        
            
    def reduce(self, lookAheadTok):
        reduceable = True
        reduced = False
        err = False  # do this later... for now, blindly accept everything is A-OK
        
        # needs to be here, multiple reduces in one reduce call IS possible
        while(reduceable):
            if reduced: reduced = False
            # for n in range(len(self.currTokens)-1, -1,-1):
            for n in range(0,len(self.currTokens)):   # why did I ever do this
                pattern = tuple(tok[0] for tok in self.currTokens[n:]) #idk if this works
                print("pattern: ", pattern)
                
                matched = self.patterns.match(pattern, lookAheadTok)
                if matched:
                    if matched == "__shift__":
                        reduceable = False
                        break
                    
                    newToken = (matched, self.currTokens[n:],)
                    # newToken = self.patterns.create(pattern, self.currTokens[n:])
                    print("reducing", pattern, "to", newToken[0])
                    
                    
                    self.currTokens = self.currTokens[:n]
                    self.currTokens.append(newToken)
                    reduced = True
                    break
                    
            if not reduced: reduceable = False
        
        
    

tokenGen = Scanner("test.src").scan()
tree = Parser().parse(tokenGen)














