from operator import attrgetter

class test(object):
    def __init__(self):
        self.a=1
        self.b=None

atts_required=['a','b']        
test=test()
f=attrgetter(*atts_required)
vals=f(test)
dic=dict(zip(atts_required, f(test)))
print dic
missing=[k for k in dic if dic[k] == None]
print missing