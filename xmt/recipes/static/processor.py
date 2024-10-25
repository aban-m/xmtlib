class IndexCollection:
    ''' Essentially a list of indices, with fast set operations. '''
    def __init__(self, indices, total_len, name = None):
        self.name = name
        self.indices = indices
        self.indices_set = set(indices) # for faster inversion
        self.total_len = total_len

    def __len__(self): return len(self.indices)
    def __repr__(self): return f'IndexCollection({self.name}, with {len(self.indices)} indices)'
    def __str__(self): return self.__repr__()

    def __and__(self, other):
        result = []
        # use two pointers to find intersectiono
        i, j = 0, 0
        while i < len(self.indices) and j < len(other.indices):
            if self.indices[i] == other.indices[j]:
                result.append(self.indices[i])
                i += 1
                j += 1
            elif self.indices[i] < other.indices[j]:
                i += 1
            else:
                j += 1
        return IndexCollection(result, min(self.total_len, other.total_len), 
                               f'({self.name} & {other.name})' if self.name and other.name else None)

    def __or__(self, other):
        result = []
        # use two pointers to find union
        i, j = 0, 0
        while i < len(self.indices) and j < len(other.indices):
            if self.indices[i] < other.indices[j]:
                result.append(self.indices[i])
                i += 1
            elif self.indices[i] > other.indices[j]:
                result.append(other.indices[j])
                j += 1
            else:
                result.append(self.indices[i])
                i += 1
                j += 1
        result += self.indices[i:]
        result += other.indices[j:]
        return IndexCollection(result, max(self.total_len, other.total_len),
                               f'({self.name} | {other.name})' if self.name and other.name else None)
    
    def __sub__(self, other):
        result = []
        # use two pointers to find difference
        i, j = 0, 0
        while i < len(self.indices) and j < len(other.indices):
            if self.indices[i] == other.indices[j]:
                i += 1
                j += 1
            elif self.indices[i] < other.indices[j]:
                result.append(self.indices[i])
                i += 1
            else:
                j += 1
        return IndexCollection(result, min(self.total_len, other.total_len),
                               f'({self.name} - {other.name})' if self.name and other.name else None)
    
    # define the minus sign to be a complement
    def __invert__(self):
        result = []
        for i in range(1, self.total_len + 1):
            if i not in self.indices_set:
                result.append(i)
        return IndexCollection(result, self.total_len, f'~{self.name}')
    

    def __eq__(self, other):
        return self.indices == other.indices
    
    def __hash__(self):
        return hash((tuple(self.indices), self.total_len, self.name))
    
        
