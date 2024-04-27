import re

class RegexStream:
    """
    basic iterator that gets the next statement from a given file
    """
    def __init__(self,regex,get,**kwargs):
        self.regex = regex
        self.get_f = get
        self.buffer_size : int = kwargs["buffer_size"] if "buffer_size" in kwargs else 1024
        self.buffer_threshold : int = kwargs["buffer_threshold"] if "buffer_threshold" in kwargs else 50

    
        #for tab completion
        self.buffer_idx = 0
        self.buffer = ""

        self.eos = False #end of stream

        self.read_to_buffer()

    def read_to_buffer(self)->None:
        self.buffer_idx = 0
        self.buffer += self.get(self.buffer_size)

    def get(self,n)->str:
        if self.eos: return ""

        data = self.get_f(n)

        if data == "":
            self.eos = True
        
        return data

    def __iter__(self):
        return self
    
    def pull_match(self,m : re.Match)->str:
        ret_val = m.group()
        self.buffer_idx += len(ret_val)
        if self.buffer_idx > self.buffer_threshold:
            self.buffer = self.buffer[self.buffer_idx:]
            self.buffer_idx = 0
        return ret_val

    def __next__(self):
        m = self.regex.search(self.buffer[self.buffer_idx:])
        
        while not m and not self.eos:
            self.buffer += self.get(self.buffer_size)
            m = self.regex.search(self.buffer[self.buffer_idx:])
        
        if m:
            return self.pull_match(m)

        #eos must be true if we got here
        raise StopIteration



class RegexFileIterator(RegexStream):
    def __init__(self,fname,regex,**kwargs):
        self.file = open(fname,'r')
        super().__init__(regex,lambda n : self.file.read(n))



if __name__ == '__main__':
    word = re.compile("[a-z]+\\s")
    rfi = RegexFileIterator("test.txt", word)

    for word in rfi:
        print(word.strip())

