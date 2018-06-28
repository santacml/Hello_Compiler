from llvmlite import ir
# from ctypes import CFUNCTYPE, c_int
from ctypes import *
import llvmlite.binding as llvm

from typeCheck import TypeCheckError, SymTableItem

class IRGenerator(object):
    def __init__(self, filename="test.asm", symTable=None):
        # filename should be proc name
        self.module = ir.Module(name=filename)
        # void = self.getType("void")
        # fnty = ir.FunctionType(void, tuple())
        # func = ir.Function(self.module, fnty, name="main")

        void = self.getType("bool")
        fnty = ir.FunctionType(void, tuple())
        func = ir.Function(self.module, fnty, name="main")


        # self.block = None
        # self.builder = None

        # do this when main pgm found
        block = func.append_basic_block()
        self.builderRoot = ir.IRBuilder(block)

        self.builder = self.builderRoot # root function
        self.builderStack = []  # make stack of functions interpreting

        # if stmts come in pairs of 2's
        # when starting else clause pop off last stmt
        # or if no else/done with if, pop off both and phi join
        # they are added backwards
        # so we can always be working on last entry
        self.condStack = [] # stack of current if stmt block
        self.ifBlock = None # the last if block we will use to join on else terminate
        self.ifHandle = None # handle for phi node

        self.loopStack = []

        '''
        # Create some useful types
        double = ir.DoubleType()
        fnty = ir.FunctionType(double, (double, double))

        # Create an empty module...
        module = ir.Module(name=__file__)
        # and declare a function named "fpadd" inside it
        func = ir.Function(module, fnty, name="fpadd")

        # Now implement the function
        block = func.append_basic_block(name="entry")
        builder = ir.IRBuilder(block)
        a, b = func.args
        result = builder.fadd(a, b, name="res")
        builder.ret(result)

        # Print the module IR

        out = repr(module)
        print(out)

        '''

        #'''
        self.symTable = symTable
        self.loadDefaults()

    def loadDefaults(self):
        void = self.getType("void")
        fnty = ir.FunctionType(void, (ir.IntType(32),))
        func = ir.Function(self.module, fnty, name="foo")
        arg = SymTableItem("integer", 0, 0)
        item  = SymTableItem("procedure", 0, 0, (arg,))
        item.irPtr = func
        self.symTable.declare("foo", item)

        void = self.getType("void")
        fnty = ir.FunctionType(void, (ir.IntType(1),))
        func = ir.Function(self.module, fnty, name="putBool")
        arg = SymTableItem("bool", 0, 0)
        item  = SymTableItem("procedure", 0, 0, (arg,))
        item.irPtr = func
        self.symTable.declare("putbool", item)

        void = self.getType("void")
        fnty = ir.FunctionType(void, (ir.IntType(32),))
        func = ir.Function(self.module, fnty, name="putInteger")
        arg = SymTableItem("integer", 0, 0)
        item  = SymTableItem("procedure", 0, 0, (arg,))
        item.irPtr = func
        self.symTable.declare("putinteger", item)

        void = self.getType("void")
        fnty = ir.FunctionType(void, (ir.FloatType(),))
        func = ir.Function(self.module, fnty, name="putFloat")
        arg = SymTableItem("float", 0, 0)
        item  = SymTableItem("procedure", 0, 0, (arg,))
        item.irPtr = func
        self.symTable.declare("putfloat", item)

        void = self.getType("void")
        ptr = ir.PointerType(self.getType("string"))
        fnty = ir.FunctionType(void, (ptr,))
        func = ir.Function(self.module, fnty, name="putString")
        arg = SymTableItem("string", 0, 0)
        item  = SymTableItem("procedure", 0, 0, (arg,))
        item.irPtr = func
        self.symTable.declare("putstring", item)

        void = self.getType("void")
        fnty = ir.FunctionType(void, (self.getType("char"),))
        func = ir.Function(self.module, fnty, name="putChar")
        arg = SymTableItem("char", 0, 0)
        item  = SymTableItem("procedure", 0, 0, (arg,))
        item.irPtr = func
        self.symTable.declare("putchar", item)

        self.defaults = ["foo",
                         "getbool",
                         "getinteger",
                         "getfloat",
                         "getstring",
                         "getchar",
                         "putbool",
                         "putinteger",
                         "putfloat",
                         "putstring",
                         "putchar"]
        #class SymTableItem(object):
        #    def __init__(self, valType, arraySize, arrayStart, params=None, paramVal=None):
        #'''

    def enterProc(self, func):
        block = func.append_basic_block()
        newBuilder = ir.IRBuilder(block)

        self.builderStack.append(newBuilder)
        self.builder = newBuilder

    def exitBuilder(self):
        # self.builder.ret(self.getType("true"))   # assume that return is handled...

        del self.builderStack[-1]
        if len(self.builderStack) > 0:
            self.builder = self.builderStack[-1]
        else:
            self.builder = self.builderRoot

    def bindAndRun(self):

        #gcc -c -Wall -Werror -fpic foo.c
        #gcc -shared -o libfoo.so foo.o
        llvm.load_library_permanently("libfoo.so")



        void = self.getType("void")

        '''fnty = ir.FunctionType(void, (ir.IntType(32),))
        func = ir.Function(self.module, fnty, name="putInteger")
        arg = ir.Constant(ir.IntType(32), "1234")
        self.builder.call(func, (arg,))

        fnty = ir.FunctionType(void, (ir.FloatType(),))
        func = ir.Function(self.module, fnty, name="putFloat")
        arg = ir.Constant(ir.FloatType(), 1234.5)
        self.builder.call(func, (arg,))

        fnty = ir.FunctionType(void, (ir.IntType(1),))
        func = ir.Function(self.module, fnty, name="putBool")
        arg = self.getType("true")
        self.builder.call(func, (arg,))'''


        # self.builder.ret_void()
        self.builder.ret(self.getType("true"))
        print(self.builder.basic_block)

        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()  # yes, even this one

        llvm_ir = self.getIR()

        def create_execution_engine():
            """
            Create an ExecutionEngine suitable for JIT code generation on
            the host CPU.  The engine is reusable for an arbitrary number of
            modules.
            """
            # Create a target machine representing the host
            target = llvm.Target.from_default_triple()
            target_machine = target.create_target_machine()
            # And an execution engine with an empty backing module
            backing_mod = llvm.parse_assembly("")
            engine = llvm.create_mcjit_compiler(backing_mod, target_machine)
            return engine

        def compile_ir(engine, llvm_ir):
            """
            Compile the LLVM IR string with the given engine.
            The compiled module object is returned.
            """
            # Create a LLVM module object from the IR
            mod = llvm.parse_assembly(llvm_ir)
            mod.verify()
            # Now add the module and make sure it is ready for execution
            engine.add_module(mod)
            engine.finalize_object()
            engine.run_static_constructors()
            return mod

        engine = create_execution_engine()
        mod = compile_ir(engine, llvm_ir)

        # Look up the function pointer (a Python int)
        func_ptr = engine.get_function_address("main")

        # Run the function via ctypes
        cfunc = CFUNCTYPE(c_bool)(func_ptr)
        res = cfunc()
        print("Exit: ", res)

    def getIR(self):
        print(repr(self.module))
        return repr(self.module)

    def getType(self, typeStr, arr=False, arrSize=0, arrStart=0):
        if arr:
            return ir.ArrayType(self.getType(typeStr), arrSize)

        elif typeStr == "integer":
            return ir.IntType(32)
        elif typeStr == "bool":
            return ir.IntType(1)

        elif typeStr == "true":
            return ir.Constant(ir.IntType(1), "1")

        elif typeStr == "false":
            return ir.Constant(ir.IntType(1), "0")

        elif typeStr == "string":
            byte = ir.IntType(8)
            array = ir.ArrayType(byte, 256)
            return array
        elif typeStr == "char":
            byte = ir.IntType(8)
            #array = ir.ArrayType(byte, 256)
            return byte


        return  {
            "float": ir.FloatType,
            "void": ir.VoidType,
        }[typeStr]()

    def getTypeConversion(self, type1, type2):
        pass

    def enterCond(self):
        self.builder.position_at_end(self.condStack[-1])

    def exitCond(self):
        # print("ASDF")
        del self.condStack[-1]
        self.builder.branch(self.condStack[-1])
        self.builder.position_at_end(self.condStack[-1])

    def enterLoop(self):
        self.builder.position_at_end(self.loopStack[-1])

    def exitLoop(self):
        del self.loopStack[-1]
        # self.builder.branch(self.loopStack[-1])
        self.builder.position_at_end(self.loopStack[-1])

    def addIR(self, pattern):
        # todo
            # in typecheck assignment, check if in.out.inout
            # should be done, in's are handled in typecheck, out and inout are declared beforehand?
            # handle strings and chars... and arrays.. and type checking/conversions
                # what else do i need to do? too many things...
            # if stmt with return inside
            # puInteger and etc

        # in if stmt, make it necessary for there to be at least 1 stmt!!!!!!!!!!!!!

        # EVERYTHING ABOUT ARRAYS
            # loading a value requires int...


        # limit char length to only 1 !!!! somewhere...

        # and main enemy: err handling
        # is this really still an issue?

        # idk what these are:
        # make functino for each toktype
        # hashmap to functions
        # use a decorator for things like toktype numchildren op etc
        tokType = pattern.tokType


        numChildren = len(pattern.children)
        if tokType in ["term", "relation", "arithOp", "expression"] and numChildren == 1:
            pattern.irHandle = pattern.children[0].irHandle

        elif tokType == "factor":
            # ("lparen", "expression", "rparen"): "factor",
            # ("minus", "name"): "factor",
            # ("name",): "factor",
            # ("minus", "number"): "factor",
            # ("number",): "factor",
            # ("string",): "factor",
            # ("char",): "factor",
            # ("true",): "factor",
            # ("false",): "factor",
            if numChildren == 1:
                child = pattern.children[0]

                if child.irHandle:
                    pattern.irHandle = child.irHandle # pretty much for just name

                # elif child.name in ["true", "false"]:
                elif child.tokType in ["true", "false"]:  # why does child.name not work? no idea. but it doesn't.
                    typ = self.getType(child.resultType)
                    # constant
                    pattern.irHandle = typ
                elif child.tokType == "string_val": # tokType is not sanitize, resultType is
                    typ = self.getType("string") # i am fed up with this, whatever
                    const = pattern.grabLeafValue(0)
                    const = const[1:-1] # chop off quotes

                    # all strings are exactly 256 len I guess
                    if len(const) > 256:
                        raise TypeCheckError("Strings may only be 256 characters long.")
                    else:
                        null = "\0" + "0" * (255-len(const))
                        const = const + null

                    const = bytearray(const.encode()) # convert to bytearray
                    #const = [ord(char) for char in const]
                    pattern.irHandle = ir.Constant(typ, const)

                elif child.tokType == "char_val":
                    typ = self.getType("char")
                    const = pattern.grabLeafValue(0)
                    const = const[1:-1] # chop off quotes

                    # ord() gives decimal value for ascii
                    # NO idea why this works
                    # just take it man
                    const = ord(const)
                    pattern.irHandle = ir.Constant(typ, const)

            elif numChildren == 2:
                # minus something
                #rhs should have ir handle?
                child = pattern.children[1]
                if child.tokType == "number":
                    pattern.irHandle = self.builder.neg(pattern.children[1].irHandle)
                else:
                    pattern.irHandle = self.builder.neg(child.irHandle)

            else:
                print("Is this tested?")
                pattern.irHandle = pattern.children[1].irHandle
                # should be handled in expression

        elif tokType == "number":

            const = pattern.grabLeafValue(0)
            typ = self.getType(pattern.resultType)

            # floatType doesn't like float strings
            # look into this future michael
            # maybe contribute to llvmlite
            pattern.irHandle = ir.Constant(typ, const)
            if pattern.resultType == "float":
                pattern.irHandle = ir.Constant(typ, float(const))

        elif tokType == "name":
            name = pattern.grabLeafValue(0)

            if name in self.symTable:
                # set it to the pointer for i.e. name + 4

                # loads this value even for like assignments... ohwell
                # print(self.symTable[name])
                if pattern.arrayExprIRHandle:
                    #TODO future michael
                    # cant figure out how to dynamically use llvm in array
                    # as in, load array[i]
                    # as the python function requires an inteer

                    # loc = pattern.grabLeafValue(2) #this is not how it should work
                    # offset =  - pattern.arrayStart + int(loc)
                    # val = self.builder.load(self.symTable[name].irPtr, align=offset)

                    loc =  pattern.arrayExprIRHandle
                    loc = self.builder.add(loc, ir.Constant(ir.IntType(32), str(- pattern.arrayStart)))

                    ptr = self.builder.load(self.symTable[name].irPtr)
                    val = self.builder.extract_value(ptr, loc)
                else:
                    val = self.builder.load(self.symTable[name].irPtr)

                # print(name, val)
                pattern.irHandle = val
            else:
                pass # it has to be declaring when this happens. Hopefully. or something

        elif tokType == "term":
            # ("term", "multiply", "factor"): "term",
            # ("term", "divide", "factor"): "term",
            # ("factor",): "term",
            op = pattern.grabLeafValue(1)
            lhs = pattern.children[0].irHandle
            rhs = pattern.children[2].irHandle

            if op == "/":
                pattern.irHandle = self.builder.mul(lhs, rhs)
            elif op == "*":
                pattern.irHandle = self.builder.sdiv(lhs, rhs)

        elif tokType == "relation":
            # ("relation", "less", "term"): "relation",
            # ("relation", "lessequal", "term"): "relation",
            # ("relation", "greater", "term"): "relation",
            # ("relation", "greaterequal", "term"): "relation",
            # ("relation", "equalequal", "term"): "relation",
            # ("relation", "notequal", "term"): "relation",
            # ("term",): "relation",

            op = pattern.grabLeafValue(1)
            # The string cmpop can be one of <, <=, ==, !=, >= or >.

            lhs = pattern.children[0].irHandle
            rhs = pattern.children[2].irHandle

            if pattern.children[0].resultType == "bool":
                lhs = self.builder.zext(lhs, ir.IntType(32))

            if pattern.children[2].resultType == "bool":
                rhs = self.builder.zext(rhs, ir.IntType(32))

            pattern.irHandle = self.builder.icmp_signed(op, lhs, rhs)

        elif tokType == "arithOp":
            # ("arithOp", "plus", "relation"): "arithOp",
            # ("arithOp", "minus", "relation"): "arithOp",
            # ("arithOp", "minus", "number"): "arithOp", # gross
            # ("arithOp", "minus", "name"): "arithOp",   # but this fixes it? I guess?
            # ("relation",): "arithOp",

            # if numChildren > 1: # covered

            op = pattern.grabLeafValue(1)
            lhs = pattern.children[0].irHandle
            rhs = pattern.children[2].irHandle

            if pattern.children[0].resultType != pattern.children[2].resultType:
                # one is float and one is int, convert both to float
                lhs = self.builder.uitofp(lhs, ir.FloatType)
                rhs = self.builder.uitofp(rhs, ir.FloatType)

            if op == "+":
                pattern.irHandle = self.builder.add(lhs, rhs)
            elif op == "-":
                pattern.irHandle = self.builder.sub(lhs, rhs)

        elif tokType == "expression":
            # ("expression", "and", "arithOp"): "expression",
            # ("expression", "or", "arithOp"): "expression",
            # ("not", "arithOp"): "expression",
            # ("arithOp",): "expression",
            if numChildren == 2:
                pattern.irHandle = self.builder.not_(pattern.children[1].irHandle)
            else:
                op = pattern.grabLeafValue(1)
                lhs = pattern.children[0].irHandle
                rhs = pattern.children[2].irHandle

                if op == "and":
                    pattern.irHandle = self.builder.and_(lhs, rhs)
                elif op == "or":
                    pattern.irHandle = self.builder.or_(lhs, rhs)

        elif tokType == "if_start":
            # self.builder.select(cond, lhs, rhs,
            # test = ir.cbranch(cond, truebr, falsebr)
            if numChildren == 5:
                cond = pattern.children[2].irHandle

                # with self.builder.if_else(cond) as (then, orelse):
                    # self.condStack.extend([orelse, then])
                    # self.condStack[-1].__enter__()
                bb = self.builder.basic_block
                bbif = self.builder.append_basic_block(name=bb.name + '.if')
                bbelse = self.builder.append_basic_block(name=bb.name + '.ifelse')
                bbend = self.builder.append_basic_block(name=bb.name + '.ifend')

                br = self.builder.cbranch(cond, bbif, bbelse)
                self.condStack.extend([bbend, bbelse, bbif])

                self.enterCond()
            else:
                # if not a new stmt, statement will be handled by builder

                # do this in typechecking/parser, for parse errors of if stmt w/o statements. Also do else stmt
                pattern.irHandle = pattern.children[1].irHandle # keep this for the phi node!!

        elif tokType == "else_start":
            if numChildren == 2:
                # self.ifBlock = self.builder.basic_block
                # self.ifHandle = pattern.children[0].irHandle
                # print(self.condStack)
                # self.condStack[-1].__exit__()
                # del self.condStack[-1]

                # enter else
                # self.condStack[-1].__enter__()

                self.exitCond()

            else:
                pattern.irHandle = pattern.children[1].irHandle # for the phi node

        elif tokType == "if_stmt":
            #print(pattern.children[0].tokType)
            if self.condStack[-1].is_terminated:
                # return was called within if statements

                del self.condStack[-1]
                # do I need to do anything here?
                # if statement will return voiding
                # I think then the rest of the function is in else stmt
                # so we are good to go?

                # go into else and then end
                self.enterCond()
                self.exitCond()

            else:
                orelseHandle = pattern.children[0].irHandle # get the out handle here. if no else stmt, will get fixed
                if pattern.children[0].tokType == "if_start":
                    # self.ifBlock = self.builder.basic_block
                    # self.ifHandle = pattern.children[0].irHandle
                    # self.condStack[-1].__exit__()
                    # del self.condStack[-1]

                    # self.condStack[-1].__enter__()
                    # orelseHandle = self.builder.add(self.getType("true"),self.getType("true"))  # dead code, return handle
                    self.exitCond()
                    # self.builder.add(self.getType("true"),self.getType("true"))  # dead code

                # exit out of else, reattach to end
                self.exitCond()
                # now delete end just for good measure
                # self.builder.add(self.getType("true"),self.getType("true"))
                # print(self.condStack[-1])
                    # now this is up to speed
                # orelseBlock = self.builder.basic_block


                #...... do I need a phi node????????? I think not...
                # out_phi = builder.phi(i32)
                # out_phi.add_incoming(out_then, bb_then)
                # out_phi.add_incoming(out_orelse, bb_orelse)

                # self.condStack[-1].__exit__()
                # del self.condStack[-1]
                # self.ifBlock = None
                # self.ifHandle = None

                del self.condStack[-1]

        elif tokType == "loop_open":
            # ("for", "lparen","assignment_stmt", "semic"): "loop_open",
            # ("loop_open", "expression", "rparen"): "loop_start",
            # ("loop_start", "statement", "semic",): "loop_start",
            # ("loop_start", "end", "for",): "loop_stmt",
            bb = self.builder.basic_block
            bbbranch = self.builder.append_basic_block(name=bb.name + '.loopstart')

            self.builder.branch(bbbranch)  # small block just for deciding
            self.builder.position_at_end(bbbranch)

            pattern.irHandle = bbbranch

        elif tokType == "loop_start":
            firstChild = pattern.children[0]
            if firstChild.tokType == "loop_open":
                cond = pattern.children[1].irHandle

                bb = self.builder.basic_block
                bbloop = self.builder.append_basic_block(name=bb.name + '.loopblock')
                bbend = self.builder.append_basic_block(name=bb.name + '.loopend')


                br = self.builder.cbranch(cond, bbloop, bbend)

                self.loopStack.extend([bbend, bbloop])
                bbbranch = pattern.children[0].irHandle # loop_open, use as handle to start the whole thing
                #bbbranch consists of assignment, conditional, and cbranch
                pattern.irHandle = bbbranch
                self.enterLoop()

                name = pattern.children[1].grabLeafValue(0)
                ptr = self.symTable[name].irPtr

                val = self.builder.load(ptr)
                result = self.builder.add(val, ir.Constant(ir.IntType(32), "1")) # just add 1 to variable

                self.builder.store(result, ptr)

            else:
                pattern.irHandle = pattern.children[0].irHandle

        elif tokType == "loop_stmt":
            # still in loop, loop back to start of loop
            # pattern handle should be bbbranch
            loopHandle = pattern.children[0].irHandle
            self.builder.branch(loopHandle)  # loop back to the bbbranch to decide to keep going

            self.exitLoop() # position ptr to end of loop

        elif tokType == "argument_list":
            argsToAdd = []
            if pattern.children[0].tokType == "expression":
                argsToAdd.append(pattern.children[0])
            else:
                pattern.irHandleList = pattern.children[0].irHandleList

            argsToAdd.append(pattern.children[2])

            # all arguments to a function come in as ptrs to maintain in/out/inout
            for argPattern in argsToAdd:
                name = argPattern.grabLeafValue(0)
                if name in self.symTable:
                    pattern.irHandleList.append(self.symTable[name].irPtr)
                else:
                    # turn a constant into a ptr to the constant
                    handle = pattern.children[2].irHandle
                    typ = handle.type
                    ptr = self.builder.alloca(typ)
                    self.builder.store(handle, ptr)

                    pattern.irHandleList.append(ptr)


            pattern.children[0].irHandleList = [] # just save space

        elif tokType == "parameter_list":
            if numChildren == 1:
                pattern.irHandleList.append(pattern.children[0].irHandle)
            else:
                pattern.irHandleList = pattern.children[0].irHandleList
                pattern.irHandleList.append(pattern.children[2].irHandle)
                pattern.children[0].irHandleList = [] # just save space

        elif tokType == "procedure_header":
            # matters
            # ("procedure", "identifier", "lparen", "rparen",): "procedure_header",
            # ("procedure", "identifier", "lparen", "parameter_list","rparen"): "procedure_header",

            # just for parsing
            # ("procedure_header", "procedure_body",): "procedure_declaration",
            # ("procedure_header_w_vars", "procedure_body",): "procedure_declaration",

            # handled when declaration occurs?? I think so... routes to appropriate builder...
            # ("procedure_header", "declaration", "semic",): "procedure_header_w_vars",
            # ("procedure_header_w_vars", "declaration", "semic",): "procedure_header_w_vars",

            # what procedure actually does, also routes to builder?
            # ("begin",): "procedure_body_start",
            # ("procedure_body_start", "statement", "semic",): "procedure_body_start",
            # ("procedure_body_start", "end", "procedure",): "procedure_body",
            func = None
            void = self.getType("void")
            procName = pattern.grabLeafValue(1)
            if numChildren == 4:
                fnty = ir.FunctionType(void, tuple())
                func = ir.Function(self.module, fnty, name=procName)
            else:
                irHandleList = []
                for paramPattern in pattern.myList:
                    # child = pattern.children[0]
                    symItem = self.symTable[paramPattern.name]
                    typ = None
                    if symItem.arrayType:
                        typ = self.getType(symItem.valType, symItem.arraySize) #HOW TO DO OFFSET???
                    else:
                        typ = self.getType(paramPattern.resultType)

                    # params hsould not be able to be global....?
                    # if pattern is global:
                        # irHandleList.append(ir.GlobalVariable(self.module, typ, paramPattern.name))
                    # else:

                    # include name of variable somehow? not really important? IDK
                    # irHandleList.append(self.builder.alloca(typ, name=paramPattern.name))
                    # print(self.symTable[paramPattern.name])
                    irHandleList.append(ir.PointerType(typ))


                    symItem.irPtr = pattern.irHandle
                # fnty = ir.FunctionType(void, pattern.children[3].irHandleList)
                fnty = ir.FunctionType(void, irHandleList)
                func = ir.Function(self.module, fnty, name=procName)

                funcArgs = func.args
                for i in range(0, len(pattern.myList)):
                    self.symTable[pattern.myList[i].name].irPtr = func.args[i]

            self.symTable[procName].irPtr = func
            self.enterProc(func)

        elif tokType == "procedure_call":
            argList = []
            procName = pattern.grabLeafValue(0)

            if pattern.children[2].tokType == "expression":
                name = pattern.grabLeafValue(2)
                if name in self.symTable:
                    # this is a variable, not a constant!!
                    argList.append(self.symTable[name].irPtr)
                else:
                    # argList.append(pattern.children[2].irHandle)
                    # turn a constant into a stored variable. gross :( but necessary
                    handle = pattern.children[2].irHandle
                    typ = handle.type
                    ptr = self.builder.alloca(typ)
                    self.builder.store(handle, ptr)

                    argList.append(ptr)

            elif pattern.children[2].tokType == "argument_list":
                argList = pattern.children[2].irHandleList

            # ptrList = []
            # for arg in argList:
                # arg =
                # ptrList.append( ir.PointerType(arg))
            if procName in self.defaults and len(argList) == 1 and procName != "putstring":
                argList[0] = self.builder.load(argList[0])
                #print(argList)
                # for default functions e.g. putInteger()
                # arguments come in as pointers
                # this results in a type mismatch
                # even when I make the C function argument a pointers
                # therefore, I need to dereference for these functions
                # and write C functions as NOT taking pointers

            pattern.irHandle = self.builder.call(self.symTable[procName].irPtr, argList)

        elif tokType == "declaration":
            loc = 0
            if numChildren == 2:
                loc = 1

            child = pattern.children[loc]
            symItem = self.symTable[child.name]

            if pattern.children[loc].tokType == "procedure_declaration":
                self.builder.ret_void()
                self.exitBuilder()
            else:
                # variable declaration
                # ("type_mark", "identifier"): "variable_declaration",
                # ("type_mark", "identifier","lbracket", "number", "colon", "number", "rbracket"): "variable_declaration",
                # ("type_mark", "identifier","lbracket", "expression", "rbracket"): "variable_declaration",

                # ("global", "procedure_declaration",): "declaration",
                # ("global", "variable_declaration",): "declaration",
                # ("procedure_declaration",): "declaration",
                # ("variable_declaration",): "declaration",


                typ = None
                if symItem.arrayType:
                    typ = self.getType(symItem.valType, arr=True, arrSize=symItem.arraySize)
                else:
                    typ = self.getType(child.resultType)

                if numChildren == 2:
                    #honestly idk what this is for
                    pattern.irHandle = ir.GlobalVariable(self.module, typ, child.name)
                else:
                    #declaring a variable
                    # alignSize = child.arraySize if child.arraySize else None
                    # print(alignSize, child.name)
                    # what actually is align??
                    # pattern.irHandle = self.builder.alloca(typ, name=child.name, size=alignSize)
                    pattern.irHandle = self.builder.alloca(typ, name=child.name)


                symItem.irPtr = pattern.irHandle

        elif tokType == "assignment_stmt":
            # ("name", "assignment", "expression"): "assignment_stmt",
            typ = self.getType(pattern.children[2].resultType)
            result = pattern.children[2].irHandle

            name = pattern.grabLeafValue(0)
            item = self.symTable[name]
            if item.arraySize != pattern.children[2].arraySize:
                raise TypeCheckError("Tried to assign array to array of different size")

            if item.valType != pattern.children[2].resultType:
                # print(item.valType)
                typeConvert = self.getTypeConversion(item.valType, pattern.children[2].resultType)

            name = pattern.grabLeafValue(0)

            ptr = self.symTable[name].irPtr

            self.builder.store(result, ptr)

        elif tokType == "return_stmt":
            self.builder.ret_void()



        # for(i := 0; i < zach)
            # ryan := zach + i;
        # end for;

        self.patterns = {
            #done
            ("for", "lparen","assignment_stmt", "semic"): "loop_open",
            ("loop_open", "expression", "rparen"): "loop_start",
            ("loop_start", "statement", "semic",): "loop_start",
            ("loop_start", "end", "for",): "loop_stmt",
            ("return",): "return_stmt",
            ("if", "lparen", "expression", "rparen", "then", ): "if_start",
            ("if_start", "statement","semic",): "if_start",
            ("if_start", "else", ): "else_start", # get rid of this to catch stmts
            ("else_start", "statement", "semic",): "else_start",
            ("if_start", "end", "if",): "if_stmt",
            ("else_start", "end", "if"): "if_stmt",
            ("assignment_stmt",): "statement",
            ("if_stmt",): "statement",
            ("loop_stmt",): "statement",
            ("return_stmt",): "statement",
            ("procedure_call",): "statement",
            ("type_mark", "identifier"): "variable_declaration",
            ("type_mark", "identifier","lbracket", "number", "colon", "number", "rbracket"): "variable_declaration",
            ("type_mark", "identifier","lbracket", "expression", "rbracket"): "variable_declaration",
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
