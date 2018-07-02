class TypeCheckError(Exception): pass
class ParseError(Exception): pass

class SymTableItem(object):
    def __init__(self, valType, arraySize, arrayStart, params=None, paramVal=None):
        self.valType = valType
        if arraySize:
            self.arrayType = True # false unless >0
        else:
            self.arrayType = False # false unless >0
        self.arraySize = arraySize
        self.arrayStart = arrayStart

        self.params = params # only for procedures....
        self.paramVal = paramVal

class SymTable(object):
    def __init__(self):
        self.rootScope = {}
        self.currScope = self.rootScope  # start off at root level
        self.globalScope = {} # global always accessible, root is just not any more local scopes
        self.scopes = []

        self.inALocalScope = False

    def exit(self):
        # i can delete scopes and it's fine
        # anything that has references to the items will still have them
        del self.scopes[-1]
        if len(self.scopes) > 0:
            self.currScope = self.scopes[-1]
        else:
            self.currScope = self.rootScope
            self.inALocalScope = False

    def enter(self, procName=None, procSymTableItem=None):   # only time entering is with a proc? I guess? Idk...
        self.scopes.append({})
        self.parentScope = self.currScope
        self.currScope = self.scopes[-1]

        if procName:
            if not procSymTableItem: raise ParseError("Incorrect usage of enter.")
            self.parentScope[procName] = procSymTableItem
            self.currScope[procName] = procSymTableItem


        self.inALocalScope = True

    def __getitem__(self, key):
        item = None
        if self.inALocalScope:
            item = self.currScope.get(key, None)
        else:
            item = self.rootScope.get(key, None)

        if not item:
            item = self.globalScope.get(key, None)
        if not item:
            raise ParseError("Could not find symbol:", key)

        return item

    # def __setitem__(self, key, value, valType, arrayType=False):
        # if not (self.currScope == None):
            # self.currScope[key] = SymTableItem(value, valType, arrayType)
        # else:
            # self.rootScope[key] = SymTableItem(value, valType, arrayType)

    def promote(self, key):
        if key in self.currScope:
            self.globalScope[key] = self.currScope[key]
            del self.currScope[key]
        elif key not in self.globalScope:
            raise ParseError("Error promoting var.")

    def declare(self, key, symTableItem):
        # use rootScope as default value
        # print("Declaring", key, self.inALocalScope)
        if self.inALocalScope:
            self.currScope[key] = symTableItem
            # print("insert", key, "into currScope")
        else:
            self.rootScope[key] = symTableItem
            # print("insert", key, "into rootScope")


    def __contains__(self, key):
        contained = False
        # print("getting", key, self.inALocalScope)
        if self.inALocalScope:
            if key in self.currScope: contained = True
        else:
            if key in self.rootScope: contained = True

        if key in self.globalScope: contained = True

        return contained

class TypeChecker(object):
    def __init__(self, scanner, parser):
        self.scanner = scanner
        self.parser = parser

        self.symTable = self.parser.symTable

    def getLineNumber(self):
        return self.parser.getLineNumber()

    def typeCheck(self, pattern):

        lineErrStart = "\nError on line " + str(self.getLineNumber()) + ":\n"
        tokType = pattern.tokType
        numChildren = len(pattern.children)
        status = True

        # numbers = ["float_number", "integer_number"]
        numbers = ["float", "integer"]
        bools = ["true", "false"]

        # all of these are the same for numChildren == 1 case
        # just assign resultType as the encapsulated item's resultType
        if tokType in ["string_val", "char_val", "factor", "term", "relation", "arithOp", "expression", "number"] and numChildren == 1:
            pattern.resultType = pattern.children[0].resultType

            # need the _number or _val for parsing purposes, but from here on, chop it
            if pattern.resultType == "float_number": pattern.resultType = "float"
            if pattern.resultType == "integer_number": pattern.resultType = "integer"


            if pattern.resultType == "string_val":
                pattern.resultType = "string"
                string = pattern.grabLeafValue(0)
                if len(string) > 258: # 258 for quotes ""
                    raise TypeCheckError("Strings may only be up to 256 characters long.")

            if pattern.resultType == "char_val":
                pattern.resultType = "char"
                char = pattern.grabLeafValue(0)
                if len(char) > 3: # 3 for quotes on either side ''
                    raise TypeCheckError("Characters may only be length 1.")

            if pattern.resultType in bools: pattern.resultType = "bool"

        elif tokType == "name":
            # ("identifier", "lbracket", "expression", "rbracket"): "name",
            # ("identifier",): "name",

            name = pattern.children[0].children[0].resultType

            if not name in self.symTable:
                #print(self.symTable.rootScope)
                raise TypeCheckError(lineErrStart + "Variable or procedure name " + name + " not found.")

            symItem = self.symTable[name]
            pattern.resultType = symItem.valType

            if len(pattern.children) == 4:
                pattern.arrayExprIRHandle = pattern.children[2].irHandle

        elif tokType == "factor":
            # covers 2 and 3

            # fuuuuuuuuuuuuuuuuuuuuuuuuuck
            # use resultType not tokType... dummy
            pattern.resultType = pattern.children[1].resultType

        elif tokType == "term":
            type1 = pattern.children[0].resultType
            type2 = pattern.children[2].resultType

            if type1 == type2:
                if not type1 in numbers : raise TypeCheckError(lineErrStart + "Can only divide or multiply numbers.")
                pattern.resultType = type1
            else:
                raise TypeCheckError(lineErrStart + "Types do not match for division or multiplication.")

        elif tokType == "relation":
            relationTypes =  ["bool"] + numbers
            type1 = pattern.children[0].resultType
            type2 = pattern.children[2].resultType

            if not type1 in relationTypes or not type2 in relationTypes:
                raise TypeCheckError(lineErrStart + "Relations can only compare numbers and bools.")

            pattern.resultType = "bool"

        elif tokType == "arithOp":
            type1 = pattern.children[0].resultType
            type2 = pattern.children[2].resultType

            if not type1 in numbers or not type2 in numbers:
                raise TypeCheckError(lineErrStart + "Arithmetic Ops can only operate on numbers.")

            if type1=="float" or type2=="float":
                pattern.resultType = "float"
            else:
                pattern.resultType = "integer"

        elif tokType == "expression":
            exprTypes = ["bool"] + numbers

            if numChildren == 2:
                pattern.resultType = pattern.children[1].resultType

            elif numChildren == 3:
                type1 = pattern.children[0].resultType
                type2 = pattern.children[2].resultType
                if type1 in exprTypes and type2 in exprTypes:
                    pattern.resultType = "bool"
                else:
                    raise TypeCheckError(lineErrStart + "Expression can only operate on numbers and bools.")

        elif tokType == "assignment_stmt":
            # ("name", "assignment", "expression"): "assignment_stmt",
            name = pattern.grabLeafValue(0)
            item = self.symTable[name]

            if item.valType != pattern.children[2].resultType:
                types = [item.valType, pattern.children[2].resultType].sort()

                if not (types == ["bool", "integer"] or type == ["float", "integer"]):

                    raise TypeCheckError(lineErrStart + "Assigned type " + pattern.children[2].resultType + " does not match declared type " + item.valType)

            if item.paramVal == "in":
                raise TypeCheckError(lineErrStart + "Variable " + name + " is a type 'in' variable and cannot be assigned to.")

        elif tokType == "loop_start":
            # ("for", "lparen", "assignment_stmt", "semic", "expression", "rparen"): "loop_start",
            # ("loop_start", "statement", "semic",): "loop_start",

            # only need to check the real start, and only the expr
            if len(pattern.children) == 6:
                expr = pattern.children[4]
                if expr.resultType != "bool":
                    raise TypeCheckError(lineErrStart + "Loops must use comparisons that evaluate to bools to evaluate if finished.")

        elif tokType == "parameter":
            # ("variable_declaration", "in",): "parameter",
            # ("variable_declaration", "out",): "parameter",
            # ("variable_declaration", "inout",): "parameter",

            # idk how to handle in and out yet
            child = pattern.children[0]
            pattern.name = child.name
            pattern.resultType = child.resultType
            pattern.arraySize = child.arraySize
            pattern.arrayStart = child.arrayStart

            pattern.parameterVal =  pattern.grabLeafValue(1)

        elif tokType == "parameter_list":
            # ("parameter",): "parameter_list",
            # ("parameter_list", "comma", "parameter"): "parameter_list",

            if len(pattern.children) == 1:
                pattern.myList.append(pattern.children[0])
            else:
                pattern.myList = pattern.children[0].myList
                pattern.myList.append(pattern.children[2])
                pattern.children[0].myList = [] # just save space

        elif tokType == "procedure_declaration":
            pattern.name = pattern.children[0].name # just for helping later on

        elif tokType == "procedure_header_w_vars":
            pattern.name = pattern.children[0].name # just for helping later on

        elif tokType == "procedure_header":
            # def __init__(pattern, valType, arraySize, arrayStart, params=None):
            # ("procedure", "identifier", "lparen", "rparen",): "procedure_header",
            # ("procedure", "identifier", "lparen", "parameter_list","rparen"): "procedure_header",

            pattern.name = pattern.grabLeafValue(1)
            pattern.resultType = "procedure"

            symTableItemList = []
            if len(pattern.children) > 4:
                pattern.myList = pattern.children[3].myList

                symTableItemList = [SymTableItem(item.resultType, item.arraySize, item.arrayStart, paramVal=item.parameterVal) for item in pattern.myList]


            procSymTableItem = SymTableItem(pattern.resultType, 0, 0, symTableItemList)

            # add params to symtable as procedure item
            self.symTable.enter(procName=pattern.name, procSymTableItem=procSymTableItem)

            # for item in pattern.myList:
            for i in range(0, len(pattern.myList)):
                self.symTable.declare(pattern.myList[i].name, symTableItemList[i])

        elif tokType == "variable_declaration":
            declType = pattern.children[0].children[0].tokType
            name = pattern.children[1].children[0].tokType
            arraySize=0
            arrayStart=0
            if numChildren == 7: # don't need to check if 2 children
                start = pattern.children[3].children[0].resultType
                end = pattern.children[5].children[0].resultType
                start = int(start)
                end = int(end)
                arraySize = end - start
                arrayStart = start

            elif numChildren == 5:
                if not pattern.children[3].resultType == "integer":
                    # need to check for negative array sizes????????
                    # print(pattern.children[3].children[0].children[0].children[0].children[0].children[1].resultType)

                    raise TypeCheckError(lineErrStart + "Array must be declared with an integer size.")

                token = pattern.grabLeafValue(3)

                arraySize = int(token)

            # symTableItem = SymTableItem(declType, arraySize, arrayStart)
            # symTable.declare(name, symTableItem)

            # thank god I dont have to change this
            pattern.resultType = declType
            pattern.name = name
            pattern.arraySize = arraySize
            pattern.arrayStart = arrayStart

        elif tokType == "declaration":
            loc = 0
            if len(pattern.children) == 2: loc = 1

            # print(pattern.children[loc].tokType)
            if pattern.children[loc].tokType == "procedure_declaration":
                self.symTable.exit() # could do this separate, w/e
            else:  #now.... deal with variables...
                # declare them here to avoid procedure params being accidentally declared
                # in a scope above
                child = pattern.children[loc]
                symTableItem = SymTableItem(child.resultType, child.arraySize, child.arrayStart)
                self.symTable.declare(child.name, symTableItem)

            if len(pattern.children) == 2:
                # oh, this is where it gets promoted
                self.symTable.promote(pattern.children[1].name)

        elif tokType == "argument_list":
            if pattern.children[0].tokType == "expression":
                pattern.myList.append(pattern.children[0])
            else:
                pattern.myList = pattern.children[0].myList

            pattern.myList.append(pattern.children[2])
            pattern.children[0].myList = [] # just save space

        elif tokType == "procedure_call":
            # ("identifier", "lparen", "argument_list", "rparen",): "procedure_call",
            # ("identifier", "lparen", "expression", "rparen",): "procedure_call",
            # ("identifier", "lparen", "rparen",): "procedure_call",

            procName = pattern.grabLeafValue(0)
            # if not procName in symTable: # this is actually handled by name if stmt

            if len(pattern.children) == 3:
                pass
            elif len(pattern.children) == 4:
                # need to check if arglist or expression
                # then check each individual thing
                if pattern.children[2].tokType == "expression":
                    pattern.myList.append(pattern.children[2])  # does not have an arglist
                else:
                    pattern.myList = pattern.children[2].myList # has an arglist


            symTableItemList = [SymTableItem(item.resultType, item.arraySize, item.arrayStart) for item in pattern.myList]

            procItem = self.symTable[procName] # should not fail...
            procParams = procItem.params

            if len(procParams) != len(symTableItemList):
                # print(len(procParams) )
                # print(symTableItemList[0].valType)
                # print(symTableItemList[0].valType)
                # print(pattern.myList[0].resultType)
                raise TypeCheckError(lineErrStart + "Number of arguments given to procedure does not match number of procedure parameters.")

            for i in range(0, len(procParams)):
                arg = symTableItemList[i]
                param = procParams[i]

                if arg.valType != param.valType:
                    raise TypeCheckError(lineErrStart + "Argument " + str(i) + " does not match type for procedure parameter")
                elif arg.arraySize != param.arraySize:
                    raise TypeCheckError(lineErrStart + "Argument " + str(i) + " does not match array size for procedure parameter")
                elif arg.arrayStart != param.arrayStart:
                    raise TypeCheckError(lineErrStart + "Argument " + str(i) + " does not match array start location for procedure parameter")


        pattern.passedCheck = status
