#!/bin/python

#for language parsing
from pylang.read_lang import LanguageMap
from pylang.read_lang import GrammerNode
from pylang.read_lang import hide_parenthasis

#for typing
from samgob.iterators.control_flow_iterator import ControlFlowIterator

#for random number generation
import random


class DiceSetParser:
    """
    the sorting algorithm used by the dice parser,
    we use the built in python one cuz were laaaaaayZ
    """
    def sort_set(self,s : [float],*args) -> [float]:
        #even though we use in place sort, still return
        #for future iterations
        s.sort(*args)
        return s
    
    def setify(self,n)-> [float]:
        if type(n) is float or type(n) is int: return [i for i in range(1,int(n)+1)]
        if type(n) is list: return n

    def __init__(self,**kwargs):
        #if we are theoretical we only want the operator functions on the object,
        #since we are using this object purly for operator parsing
        if not kwargs["only_operations"] if "only_operations" in kwargs else True:

            language_file = kwargs["language_file"] if "language_file" in kwargs else "dice_set.lang"
            #generate the langauge structure
            lang,lexims,maps = LanguageMap.from_file(language_file,
                                                     entry_point = "statement")
            self.lang = lang
            self.lexims = lexims
            self.maps = maps

            self.print_delimiter = ' '

            self.variable_map = {}

            self.do_compile = False
            self.tab_order = 0

        self.arithmatic_operators = {
                "+": lambda x,y : x+y,
                "-": lambda x,y : x-y,
                "/": lambda x,y : x/y,
                "*": lambda x,y : x*y,
                ">=": lambda x,y : int(x>=y),
                "<=": lambda x,y : int(x<=y),
                ">": lambda x,y : int(x>y),
                "<": lambda x,y : int(x<y),
                "==": lambda x,y : int(x==y),
                }
        
        self.set_compressors = {
                'd': lambda n,s: sum([random.choice(self.setify(s)) for _ in range(int(n))])
                }
        self.unary_set_compressors = {
                's': lambda s: sum(self.setify(s))
                }
        self.set_operators = {
                'D' : lambda n,s: [random.choice(self.setify(s)) for _ in range(int(n))],
                'T' : lambda n,s : self.sort_set(self.setify(s))[-int(n):],
                'B' : lambda n,s : self.sort_set(self.setify(s))[:int(n)]
                }
        
        self.statement_stream : ControlFlowIterator = None

    def print_out(self,data,*args,**kwargs)->None:
        print("\t"*self.tab_order + data,*args,**kwargs)

    def parse_assignment(self,token : GrammerNode,parenth)->None:
        var_name = token.sub_tokens[0].data
        if token.sub_tokens[2].token.name == "arithmatic":
            
            if self.do_compile:
                self.variable_map[var_name] = 1
                self.print_out(f"{var_name}=",end="")
                self.parse_arithmatic(token.sub_tokens[2],parenth)
            else:
                self.variable_map[var_name] = self.parse_arithmatic(token.sub_tokens[2],parenth)

        else:
            self.variable_map[var_name] = self.parse_set(token.sub_tokens[2],parenth)

    def parse_print_flow(self,token : GrammerNode,parenth = [])->None:

        if not (token.sub_tokens[0].sub_tokens[0].token.name == "flow_end" 
               or
               self.statement_stream.while_flag):
            if len(token.sub_tokens) == 2:
                if self.do_compile:
                    self.print_out("context.delimiters.append('\\n')")
                else:
                    self.print_delimiter = "\n"
            elif len(token.sub_tokens) == 1:
                if self.do_compile:
                    self.print_out("context.delimiters.append(' ')")
                else:
                    self.print_delimiter = " "
            else:
                if self.do_compile:
                    self.print_out("context.delimiters.append('",end="")
                    print(token.sub_tokens[2].data,end="")
                    print("')")
                else:
                    self.print_delimiter = token.sub_tokens[2].data
        

        self.parse_control_flow(token.sub_tokens[0])


    def parse_control_flow(self,token : GrammerNode,parenth = [])->None:
        flow_token = token.sub_tokens[0]
        flow_type = flow_token.token.name
        match flow_type:
            case "for":
                if self.do_compile:
                    self.print_out("for i in range(",end="")
                    self.parse_arithmatic(flow_token.sub_tokens[1],parenth)
                    print("):",end="")
                    self.tab_order += 1
                else:
                    n = self.parse_arithmatic(flow_token.sub_tokens[1],parenth)
                    
                    if n == 0:
                        self.statement_stream.add_if(False,self.print_delimiter)
                    elif n == 1:
                        self.statement_stream.add_if(True,self.print_delimiter)
                    else:
                        self.statement_stream.add_for(int(n),self.print_delimiter)
            case "flow_end":
                if self.do_compile:
                    self.tab_order -= 1
                    self.print_out("clean_delimiters()")
                else:
                    self.statement_stream.pop_loop()
            case "else":
                if self.do_compile:
                    self.print_out("break")
                    print("\t"*(self.tab_order-1) + "else:")
                else:
                    self.statement_stream.set_else(True,self.print_delimiter)
            case "while":
                if self.do_compile:
                    self.print_out("while ",end="")
                    self.tab_order += 1
                    self.parse_arithmatic(flow_token.sub_tokens[2],parenth)
                    print(">0:",end="")
                else:
                    n = self.parse_arithmatic(flow_token.sub_tokens[2],parenth)
                    self.statement_stream.add_while(n>0,flow_token.data,self.print_delimiter)

    def parse_statement(self,statement : GrammerNode,parenth = []):
        expr = statement.sub_tokens[0]
        expression_token = expr.sub_tokens[0]
        
        #control flow clauses
        if self.statement_stream.in_if(False) or self.statement_stream.in_else(True):
            if expression_token.token.name == "print_control_flow":
                expression_token = expression_token.sub_tokens[0]
                if expression_token.sub_tokens[0].token.name == "flow_end":
                    self.statement_stream.break_loop()
                elif expression_token.sub_tokens[0].token.name == "else":
                    self.statement_stream.set_else(False,self.print_delimiter)
                else:
                    """
                    we still care about control flow for the ordering of --
                    but we don't want to parse loops, so a neet hack is to add
                    a true if statement that does nothing, but gets poped when it finds
                    the flow end
                    """
                    self.statement_stream.add_if(True,self.print_delimiter) 
        else:
            match expression_token.token.name:
                case "arithmatic":
                    if self.do_compile:
                        self.print_out('print(')
                        n = self.parse_arithmatic(expression_token,parenth)
                        print('\n,end=get_delimiter())')
                    else:
                        n = self.parse_arithmatic(expression_token,parenth)
                        print("%g" % n, end=self.print_delimiter)
                case "set":
                    if self.do_compile:
                        self.print_out("print(")
                        s = self.parse_set(expression_token,parenth),
                        print("\n,end=get_delimiter())")
                        print()
                    else:
                        s = self.parse_set(expression_token,parenth)
                        print(s,end=self.print_delimiter)
                case "assignment":
                    self.parse_assignment(expression_token,parenth)
                case "print_control_flow":
                    self.parse_print_flow(expression_token,parenth)
            
            if self.do_compile:
                print()

    def parse_set(self,set_node : GrammerNode,parenth = []):#->float | [float]:
        inner_token : GrammerNode = set_node.sub_tokens[0]
        if inner_token.token.name == "range":
            if len(inner_token.sub_tokens) == 1:
                number = int(inner_token.sub_tokens[0].data)
                a = [i for i in range(1,number+1)]
                if self.do_compile:
                    print(a,end="")
                else:
                    return a
            else:
                a = [i for i in range(int(inner_token.sub_tokens[1].data),int(inner_token.sub_tokens[3].data)+1)]
                if self.do_compile:
                    print(a,end="")
                else:
                    return a
        elif inner_token.token.name == 'arithmatic':
            return self.parse_arithmatic(inner_token,parenth)
        elif set_node.sub_tokens[1].token.name == "set_operator":
            if self.do_compile:
                print(f"context.set_operators['{set_node.sub_tokens[1].data}'](",end="")
                self.parse_set(set_node.sub_tokens[0],parenth)
                print(",",end="")
                self.parse_set(set_node.sub_tokens[2],parenth)
                print(")",end="")
            else:
                #ensure that we parse out the correct set from incoming data
                return self.set_operators[set_node.sub_tokens[1].data](
                         self.parse_set(set_node.sub_tokens[0],parenth),
                         self.parse_set(set_node.sub_tokens[2],parenth)
                         )


    #handles parsing out arithmatic statements
    def parse_arithmatic(self,arithmatic : GrammerNode,parenth = [])->float:
        if len(arithmatic.sub_tokens) == 3:
            if arithmatic.sub_tokens[1].token.name == "arithmatic_operator":
                if self.do_compile:

                    self.parse_arithmatic(arithmatic.sub_tokens[0],parenth)
                    print(arithmatic.sub_tokens[1].data,end="")
                    self.parse_arithmatic(arithmatic.sub_tokens[2],parenth)
                else:
                    return self.arithmatic_operators[arithmatic.sub_tokens[1].data](
                                self.parse_arithmatic(arithmatic.sub_tokens[0],parenth),
                                self.parse_arithmatic(arithmatic.sub_tokens[2],parenth)
                            )

            elif arithmatic.sub_tokens[1].token.name == "set_compressor":
                if self.do_compile:
                    print(f"context.set_compressors['{arithmatic.sub_tokens[1].data}'](",
                            end="")
                    self.parse_arithmatic(arithmatic.sub_tokens[0],parenth)
                    print(",",end="")
                    self.parse_set(arithmatic.sub_tokens[2],parenth)
                    print(")",end="")
                else:
                    return self.set_compressors[arithmatic.sub_tokens[1].data](
                                self.parse_arithmatic(arithmatic.sub_tokens[0],parenth),
                                self.parse_set(arithmatic.sub_tokens[2],parenth)
                            )
        elif len(arithmatic.sub_tokens) == 2:
            if self.do_compile:
                print(f"context.unary_set_compressors['{arithmatic.sub_tokens[0].data}'](",
                      end="")
                self.parse_set(arithmatic.sub_tokens[1],parenth)
                print(f")",end="")
            else:
                return self.unary_set_compressors[arithmatic.sub_tokens[0].data](
                        self.parse_set(arithmatic.sub_tokens[1],parenth)
                    )
        elif arithmatic.sub_tokens[0].token.name == "number":
            if self.do_compile:
                print(arithmatic.data,end="")
            else:
                return float(arithmatic.data)
        elif arithmatic.sub_tokens[0].token.name == "variable":
            if not (arithmatic.data in self.variable_map):
                print(f"\nerror reading unset variable :: {arithmatic.data}")
                quit()
            if self.do_compile:
                print(arithmatic.data,end="")
            else:
                if not (arithmatic.data in self.variable_map):
                    print(f"\nerror reading unset variable :: {arithmatic.data}")
                    quit()
                return self.variable_map[arithmatic.data]
        else:
            
            inner_parenth = parenth[int(arithmatic.data.split("_")[2][1:])]
            inner_parenth,iner_para =  hide_parenthasis(inner_parenth)
            if self.do_compile:
                print("(",end="")
                self.parse_arithmatic(
                                          self.maps["arithmatic"].match(inner_parenth),
                                          iner_para
                                      )
                print(")",end="")
            else:
                return self.parse_arithmatic(
                                          self.maps["arithmatic"].match(inner_parenth),
                                          iner_para
                                      )

    def break_delimiter_print(self,just_broke_delimiter : str)->None:
        if len(self.statement_stream.flow_stack) < 1:
            return
        previous_delimiter = self.statement_stream.flow_stack[-1][-2][0]
        if previous_delimiter != just_broke_delimiter:
            print(end=previous_delimiter)

    def compile_langauge(self,statement_stream : ControlFlowIterator)->None:

        self.statement_stream = statement_stream
        self.statement_stream.break_callback = self.break_delimiter_print

        entry_map = self.maps[self.lang.entry_node.name]

        for idx,statement in enumerate(statement_stream):
            statement, parenth = hide_parenthasis(statement)
            #print("reading " + statement)
            g = entry_map.match(statement.strip() + ";")
            if g == None:
                print(f"error on statement {idx} :: {statement}")
                quit()
            else:
                #print(g.get_summary())
                self.parse_statement(g,parenth)
