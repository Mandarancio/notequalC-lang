import re
from collections import namedtuple
import sys
import os

sources = []


Comment = namedtuple('Comment', 'start end')


def clean(s):
    return ''.join([c if c.isalpha() else '_' for c in s])
    

def t_hash(arguments):
    return '_'.join([clean(s) for s in arguments])
    

def impl_macro(name, arguments):
    for s in sources:
        for m in s.macros:
            if m.name == name:
                body = m.impl(arguments)
                s.insert(body, m.pos+1)
                
def impl_struct(name, arguments):
    for s in sources:
        for o in s.structs:
            if o.name == name:
                body = o.impl(arguments)
                s.insert(body, o.pos)

def impl_function(name, arguments):
    for s in sources:
        for o in s.functions:
            if o.name == name:
                body = o.impl(arguments)
                s.insert(body, o.pos)
                
def impl_method(cname, fname, arguments):
    for s in sources:
        for o in s.methods:
            if o.name == fname and o.cname == cname:
                body = o.impl(arguments)
                s.insert(body, o.pos)

def arg_split(args):
    status = True
    old = 0
    res = []
    for i in range(len(args)):
        if status and args[i] == ',':
            res.append(args[old:i])
            old = i+1
        elif status and args[i] in [' ', '\t', '\n']:
            old += 1
        elif args[i] == '"':
            status = not status
    res.append(args[old:])
    return res
                  

def close_brakets(text, start=0):
    count = 0 if text[start] == '{' else 1
    status = 0
    for i in range(start, len(text)-1):
        if text[i] == '{' and status == 0:
            count += 1
        elif text[i] == '}' and status == 0:
            count -= 1
            if count == 0:
                return i+1
        elif status == 0 and text[i:i+1] == '//': 
            status = 1
        elif status == 0 and text[i:i+1] == '/*':
            status = 2
        elif status == 1 and text[i] == '/n':
            status = 0
        elif status == 2 and text[i:i+1] == '*/':
            status = 0
    return len(text)

def start_brakets(text, end):
    count = 0
    last_open = 0
    status = 0
    for i in range(end):
        if text[i] == '{' and status == 0:
            if count == 0:
                last_open = i
            count += 1
        elif text[i] == '}' and status == 0:
            count -= 1
        elif status == 0 and text[i:i+1] == '//': 
            status = 1
        elif status == 0 and text[i:i+1] == '/*':
            status = 2
        elif status == 1 and text[i] == '/n':
            status = 0
        elif status == 2 and text[i:i+1] == '*/':
            status = 0
    return last_open

def find_definition_of(text, start):
    count = 0
    fn_def = -1
    status = 0
    for i in range(start):
        if count == 0 and status == 0  and fn_def < 0 and text[i] not in ['\n', '\t', ' ', '#', ';']:
            fn_def = i
        elif fn_def >= 0 and text[i] == ';' and status == 0:
            fn_def = -1
        elif text[i] == '{' and status == 0:
            if count == 0:
                fn_def = -1
            count += 1
        elif text[i] == '}' and status == 0:
            count -= 1
        elif status == 0 and text[i:i+1] == '//': 
            status = 1
        elif status == 0 and text[i:i+1] == '/*':
            status = 2
        elif status == 1 and text[i] == '/n':
            status = 0
        elif status == 2 and text[i:i+1] == '*/':
            status = 0
    return fn_def
        

def close_parentesis(text, start = 0):
    count = 0 if text[start] == '(' else 1
    status = 0
    for i in range(start, len(text)-1):
        if text[i] == '(' and status == 0:
            count += 1
        elif text[i] == ')' and status == 0:
            count -= 1
            if count == 0:
                return i+1
        elif status == 0 and text[i:i+1] == '//': 
            status = 1
        elif status == 0 and text[i:i+1] == '/*':
            status = 2
        elif status == 1 and text[i] == '/n':
            status = 0
        elif status == 2 and text[i:i+1] == '*/':
            status = 0
    return len(text)
    
    
def close_line(text, start = 0):
    status = 0
    for i in range(start, len(text)-1):
        if text[i] == ';' and status == 0:
            return i+1
        elif status == 0 and text[i:i+1] == '//': 
            status = 1
        elif status == 0 and text[i:i+1] == '/*':
            status = 2
        elif status == 1 and text[i] == '/n':
            status = 0
        elif status == 2 and text[i:i+1] == '*/':
            status = 0
    return len(text)
    

def bracket_or_column(text, start=0):
    status = 0
    for i in range(start, len(text)-1):
        if text[i] in [';', '{'] and status == 0:
            return i+1, text[i]
        elif status == 0 and text[i:i+1] == '//': 
            status = 1
        elif status == 0 and text[i:i+1] == '/*':
            status = 2
        elif status == 1 and text[i] == '/n':
            status = 0
        elif status == 2 and text[i:i+1] == '*/':
            status = 0
    return len(text)


class Struct:
    def __init__(self, name, arguments, text, pos):
        self.name = name
        self.arguments = arg_split(arguments)
        self.text = text
        self.pos = pos
        self.__impl__ = []
        
    def __repr__(self):
        return self.text
    
    def impl(self, arguments):
        thash = t_hash(arguments)
        if thash not in self.__impl__:
            res = self.text[:]
            rin = self.name+'\s*<'+'\s*,?'.join(self.arguments)+'\s*>'
            rout = self.name+'_'+thash
            res = re.sub(rin, rout, res)
            for ta, ra in zip(self.arguments, arguments):
                rin = r'(\W)('+ta+')(\W)'
                rout = r'\1'+ra+r'\3'
                res = re.sub(rin, rout, res)
            self.__impl__.append(thash)
            return res
        return ''
        

        
class Function:
    def __init__(self, name, arguments, result, body, pos, cname=None):
        self.name = name
        self.arguments = arg_split(arguments)
        self.result = result
        self.body = body
        self.cname = cname
        self.pos = pos
        self.__impl__ = []
    
    def __repr__(self):
        return self.result+' '+self.name+'<'+self.arguments+'>'+self.body
    
    def impl(self, arguments):
        thash = t_hash(arguments)
        if thash not in self.__impl__:
            res = self.body[:]
            if self.cname:
                rin = self.cname+'\s*<'+'\s*,?'.join(self.arguments)+'\s*>::'+self.name
                rout =  self.cname+'_'+thash+'_'+self.name
            else:
                rin = self.name+'\s*<'+'\s*,?'.join(self.arguments)+'\s*>'
                rout = self.name+'_'+thash
            res = re.sub(rin, rout, res)
            for ta, ra in zip(self.arguments, arguments):
                rin = r'(\W)?('+ta+')(\W)'
                rout = r'\1'+ra+r'\3'
                res = re.sub(rin, rout, res)
            self.__impl__.append(thash)
            return res
        return ''

class Macro:
    def __init__(self, name, arguments, body, pos):
        self.name = name
        self.arguments = arg_split(arguments)
        self.body = body
        self.pos = pos
        self.__impl__ = []
    
    def impl(self, arguments):
        thash = t_hash(arguments)
        if thash not in self.__impl__:
            res = self.body[:]
            for ta, ra in zip(self.arguments, arguments):
                rin = r'(\W)('+ta+r')(\W)'
                rout = r'\1'+ra+r'\3'
                res = re.sub(rin, rout, res)
            self.__impl__.append(thash)
            return res
        return ''
        


class Source:
    def __init__(self, path, text):
        self.input = text[:]
        self.path = path
        self.name = path.split('/')[-1]
        
        self.structs = []
        self.macros = []
        self.functions = []
        self.methods = []
        
        self.lambdas = 0
        
        self.objects = []
        
        self.__find_macros__()
        self.__find_structs__()
        self.__find_functions__()
        self.__find_methods__()
        
        self.__impl__ = self.input[:]
        
    def result(self):
        return self.__impl__
        
    def insert(self, text, pos):
        l = len(text)
        self.__impl__ = self.__impl__[:pos]+text+self.__impl__[pos:]
        for o in self.objects:
            if o.pos >= pos:
                o.pos += l
                
    def remove(self, start, end):
        l = (end - start)
        self.input = self.input[:start] + self.input[end:]
        for o in self.objects:
            if o.pos > start:
                o.pos -= l
                
    def replace(self, start, end, text):
        delta = len(text)-(end - start)
        self.__impl__ = self.__impl__[:start]+text+self.__impl__[end:]
        for o in self.objects:
            if o.pos > start:
                o.pos += delta
        
    def implement(self):
        status = False
        status = status or self.__impl_macros__()
        status = status or self.__impl_methods__()
        status = status or self.__impl_functions__()
        status = status or self.__impl_structs__()
        status = status or self.__impl_lambdas__()
        return status
        
    def __impl_macros__(self):
        regex = r'\s*\W@(\w*)\s*<(.*)>'
        changed = True
        updated = False
        while changed:
            changed = False
            matches = re.finditer(regex, self.__impl__, re.MULTILINE)
            for match in matches:
                s = match.start()
                e = match.end()
                if self.is_commented(s,e):
                    continue
                updated = True
                name = match.group(1)
                arguments = arg_split(match.group(2))
                group_end = close_line(self.__impl__, e)
                self.__impl__ = self.__impl__[:s] + (' ' * (group_end-s)) + self.__impl__[group_end:]
                #self.remove(s, group_end)
                impl_macro(name, arguments)
                changed = True
                break
        return updated
        
    def __impl_structs__(self):
        regex = r'(\w+)\s*<([\w\"_,\s.]*)>\s*'
        changed = True
        updated = False
        while changed:
            changed = False
            matches = re.finditer(regex, self.__impl__, re.MULTILINE)
            for match in matches:
                s = match.start()
                e = match.end()
                if self.__impl__[s-1] == '#':
                    continue
                if self.is_commented(s,e):
                    continue
                updated = True
                name = match.group(1)
                arguments = arg_split(match.group(2))
                self.replace(s, e,  name+"_"+ t_hash(arguments)+' ')
                impl_struct(name, arguments)
                changed = True
                break
        return updated
        
    def __impl_functions__(self):
        regex = r'(\w+)\s*<([\w\"_,\s.]*)>\s*\('
        changed = True
        updated = False
        while changed:
            changed = False
            matches = re.finditer(regex, self.__impl__, re.MULTILINE)
            for match in matches:
                s = match.start()
                e = match.end()
                if self.is_commented(s,e):
                    continue
                updated = True
                name = match.group(1)
                arguments = arg_split(match.group(2))
                self.replace(s, e,  name+"_"+ t_hash(arguments)+'(')
                impl_function(name, arguments)
                changed = True
                break
        return updated
        
    def __impl_methods__(self):
        regex = r'(\w+)\s*<([\w\"_,\s.]*)>::(\w+)'
        changed = True
        updated = False
        while changed:
            changed = False
            matches = re.finditer(regex, self.__impl__, re.MULTILINE)
            for match in matches:
                s = match.start()
                e = match.end()
                if self.is_commented(s,e):
                    continue
                updated = True
                cname = match.group(1)
                arguments = arg_split(match.group(2))
                fname = match.group(3)
                
                self.replace(s, e,  cname+"_"+ t_hash(arguments)+'_'+fname)
                impl_method(cname, fname, arguments)
                
                changed = True
                break
        return updated
        
    def __impl_lambdas__(self):
        regex = '\Wlambda\s*\((.*)\)\s*=>\s*(.*)\s*{'
        changed = True
        updated = False
        while changed:
            changed = False
            matches = re.finditer(regex, self.__impl__, re.MULTILINE)
            for match in matches:
                s = match.start()
                e = match.end()
                if self.is_commented(s,e):
                    continue
                updated = True
                arguments = match.group(1)
                result = match.group(2)
                name = '__lambda_'+str(self.lambdas)+'__'
                self.lambdas += 1
                ge = close_brakets(self.__impl__, e)
                gs = start_brakets(self.__impl__, s)

                ds = find_definition_of(self.__impl__, gs)
                
                body = result+' '+name+' ('+arguments+')\n{'+self.__impl__[e:ge-1]+'}\n\n'
                self.replace(s, ge,  name)
                self.insert(body, ds)
                changed = True
                break
        return updated
        
    def is_commented(self, start, end):
        for comment in self.__find_comments__():
            if start > comment.start and start < comment.end:
                return True
        return False
        
    def __find_comments__(self):
        # regex for both inline and multiline comments
        res = []
        for regex in [r'//.*', r'(?s)/\*.*?\*/']:
            matches = re.finditer(regex, self.input, re.MULTILINE)
            for match in matches:
                res.append(Comment(start=match.start(), end=match.end()))
        return res 
                
    def __find_macros__(self):
        regex = r'\W@(\w+)\s*<(.*)>\s*{'
        changed = True
        while changed:
            changed = False
            matches = re.finditer(regex, self.input, re.MULTILINE)
            for match in matches:
                s = match.start()
                e = match.end()
                if self.is_commented(s,e):
                    continue
                name = match.group(1)
                arguments = match.group(2)
                group_end = close_brakets(self.input, e)
                body = self.input[e:group_end-1]
                self.macros.append(Macro(name=name, arguments=arguments, body=body, pos=s))
                self.objects.append(self.macros[-1])
                self.remove(s, group_end)
                changed = True
                break
                
    def __find_structs__(self):
        regex = r'(\btypedef\s*)?\bstruct\s+(\w*)\s*<(.*)>\s*{'
        changed = True
        while changed:
            changed = False
            matches = re.finditer(regex, self.input, re.MULTILINE)
            for match in matches:
                s = match.start()
                e = match.end()
                if self.is_commented(s,e):
                    continue
                group_end = close_line(self.input, close_brakets(self.input, e))
                name = match.group(2)
                arguments = match.group(3)
                self.structs.append(Struct(name=name, arguments=arguments, pos=s, text=self.input[s:group_end]))
                self.objects.append(self.structs[-1])
                self.remove(s, group_end)
                changed = True
                break
            
    def __find_functions__(self):
        regex = r'(\w[\w_\t *<>()]*)\s+(\w*)\s*<([\w\s_,])>\s*\('
        changed = True
        while changed:
            changed = False
            matches = re.finditer(regex, self.input, re.MULTILINE)
            for match in matches:
                s = match.start()
                e = match.end()
                if self.is_commented(s,e):
                    continue
                result = match.group(1)
                if result.strip() == 'return':
                    continue
                arg_end = close_parentesis(self.input, e)
                pos, char = bracket_or_column(self.input, arg_end)
                end = close_brakets(self.input, pos) if char == '{' else pos
                name = match.group(2)
                arguments = match.group(3)
                body = self.input[s:end]
                self.functions.append(Function(name, arguments, result, body, s))
                self.objects.append(self.functions[-1])
                self.remove(s, end)
                changed = True
                break
        
    def __find_methods__(self):
        regex = r'(\w[\w\s*<>]*)\s+(\w[\w\d_]*)\s*<(\w[\w_\d\s,]*)>::(\w[\w\d_]*)\s*\('
        changed = True
        while changed:
            changed = False
            matches = re.finditer(regex, self.input, re.MULTILINE)
            for match in matches:
                s = match.start()
                e = match.end()

                if self.is_commented(s,e):
                    continue
                result = match.group(1)
                if result.strip() == 'return':
                    continue
                arg_end = close_parentesis(self.input, e)
                pos, char = bracket_or_column(self.input, arg_end)
                end = close_brakets(self.input, pos) if char == '{' else pos
                cname = match.group(2)
                arguments = match.group(3)
                name = match.group(4)
                body = self.input[s:end]
                self.methods.append(Function(name, arguments, result, body, s, cname=cname))
                self.objects.append(self.methods[-1])
                self.remove(s, end)
                changed = True
                break
        
            
def parse(fpath, f):
    text = f.read()
    return Source(fpath, text)


if __name__ == "__main__":
    args = sys.argv[1:]
    output_dir = 'aout/'
    files = []
    for arg in args:
        if arg.startswith('-o'):
            output_dir = arg[2:]
        else:
            files.append(arg)
    output_dir = output_dir + ('' if output_dir[-1]=='/' else '/')
    print(f'output dir: {output_dir}')
    for fpath in files:
        with open(fpath, 'r') as f:
            sources.append(parse(fpath, f))
    changed = True
    
    while changed:
        changed = False
        for source in sources:
            changed = changed or source.implement()
    
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)
        
    for source in sources:
        name = source.name.split('.')[0]
        ext = '.c' if 'c' in source.name.split('.')[-1] else '.h'
        path = output_dir + name + ext
        print('- '+source.name+' => '+path)
        with open(path, 'w') as f:
            f.write(source.result())
