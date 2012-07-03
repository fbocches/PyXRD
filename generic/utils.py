# coding=UTF-8
# ex:ts=4:sw=4:et=on

# Author: Mathijs Dumon
# This work is licensed under the Creative Commons Attribution-ShareAlike 3.0 Unported License. 
# To view a copy of this license, visit http://creativecommons.org/licenses/by-sa/3.0/ or send
# a letter to Creative Commons, 444 Castro Street, Suite 900, Mountain View, California, 94041, USA.

import os
from math import exp, sqrt, log, pi
import inspect
import time
import hashlib

import gobject
import gtk
import numpy as np

sqrtpi = sqrt(pi)
sqrt2pi = sqrt(2*pi)
sqrt8 = sqrt(8) 
    
def create_treestore_from_directory(directory, extension):
    treestore = gtk.TreeStore(str,str, bool)
    treestore.append(None, ("", "", True))
    ext_len = len(extension)
    parents = {}
    for root, dirnames, filenames in os.walk(directory):
        for dirname in dirnames:
            parents[os.path.join(root, dirname)] = treestore.append(parents.get(root, None), (dirname, "", False))
        for filename in filenames:
            treestore.append(parents.get(root, None), (filename[:-ext_len], "%s/%s" % (root, filename), True))   
    return treestore
    
    
def recgetattr(obj, attr):
    return reduce(getattr, attr.split("."), obj)

def recsetattr(obj, attr, value):
    attrs = attr.split(".")
    setattr(reduce(getattr, attrs[:-1], obj), attrs[-1], value)
    
def get_md5_hash(obj):
    hsh = hashlib.md5()
    hsh.update(obj)
    return hsh.digest()

def u(string):
    return unicode(string, errors='replace', encoding='UTF-8')

def print_timing(func):
    def wrapper(*args, **kwargs):
        t1 = time.time()
        res = func(*args, **kwargs)
        t2 = time.time()
        print '%s took %0.3f ms' % (func.func_name, (t2-t1)*1000.0)
        return res
    return wrapper


class delayed(object):
    def __init__(self, lock=None, delay=250):
        self.__lock = lock
        self.__delay = delay
        self.__tmrid = dict()
        
    def __call__(self, func):
        def wrapper(*args, **kwargs):
            instance = args[0] if len(args)>0 else None
            key = instance or func
            if self.__lock != None and getattr(instance, self.__lock):
                return #if the function is locked, do not push back the call
            if key in self.__tmrid:
                gobject.source_remove(self.__tmrid[key])
                del self.__tmrid[key]
            delay = 0
            try:
                delay = int(self.__delay)
            except:
                delay = getattr(instance, self.__delay)
            self.__tmrid[key] = gobject.timeout_add(delay, self.__timeout_handler__, func, key, *args, **kwargs)
        return wrapper
      
    def __timeout_handler__(self, func, key, *args, **kwargs):
        func(*args, **kwargs)
        if key in self.__tmrid: del self.__tmrid[key]
        return False

def get_case_insensitive_glob(*strings):
    '''Ex: '*.ora' => '*.[oO][rR][aA]' '''
    return ['*.%s' % ''.join(["[%s%s]" % (c.lower(), c.upper()) for c in string.split('.')[1]]) for string in strings]
    
def retreive_lowercase_extension(glob):
    '''Ex: '*.[oO][rR][aA]' => '*.ora' '''
    return ''.join([ c.replace("[", "").replace("]", "")[:-1] for c in glob.split('][')])

def find_ge(a, x):
    'Find leftmost item greater than or equal to x'
    i = bisect_left(a, x)
    if i != len(a):
        return a[i]
    raise ValueError

def whoami():
    return inspect.stack()[1][3]

#expects the data to be sorted!!
def interpolate(data, x):
    x1, y1 = (0,0)
    x2, y2 = (0,0)
    for tx,ty in data:
        if tx > x:
            x1, y1 = (tx,ty)
            break
        else:
            x2, y2 = (tx,ty)
    return y1 + (x-x1) * (y2 - y1) / (x2 - x1)
   
def smooth(x,window_len=3,window='blackman'):
    """smooth the data using a window with requested size.
    
    This method is based on the convolution of a scaled window with the signal.
    The signal is prepared by introducing reflected copies of the signal 
    (with the window size) in both ends so that transient parts are minimized
    in the begining and end part of the output signal.
    
    input:
        x: the input signal 
        window_len: the dimension of the smoothing window; should be an odd integer
        window: the type of window from 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'
            flat window will produce a moving average smoothing.

    output:
        the smoothed signal
        
    example:

    t=linspace(-2,2,0.1)
    x=sin(t)+randn(len(t))*0.1
    y=smooth(x)
    
    see also: 
    
    numpy.hanning, numpy.hamming, numpy.bartlett, numpy.blackman, numpy.convolve
    scipy.signal.lfilter
 
    TODO: the window parameter could be the window itself if an array instead of a string
    """

    if x.ndim != 1:
        raise ValueError, "smooth only accepts 1 dimension arrays."

    if x.size < window_len:
        raise ValueError, "Input vector needs to be bigger than window size."

    half_len = window_len
    window_len = half_len*2 + 1
    if window_len<3:
        return x


    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError, "Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"


    s=np.r_[x[window_len-1:0:-1],x,x[-1:-window_len:-1]]
    #print(len(s))
    if window == 'flat': #moving average
        w=np.ones(window_len,'d')
    else:
        w=eval('np.'+window+'(window_len)')

    y=np.convolve(w/w.sum(),s,mode='valid')
    return y[half_len:-half_len]
   
"""def erf(x):
    # constants
    a1 =  0.254829592
    a2 = -0.284496736
    a3 =  1.421413741
    a4 = -1.453152027
    a5 =  1.061405429
    p  =  0.3275911

    # Save the sign of x
    sign = 1
    if x < 0:
        sign = -1
    x = abs(x)

    # A&S formula 7.1.26
    t = 1.0/(1.0 + p*x)
    y = 1.0 - (((((a5*t + a4)*t) + a3)*t + a2)*t + a1)*t*exp(-x*x)
    
    return sign*y"""
    
#def erf(x, steps=1000):
#    result = np.zeros(x.shape)
#    dt = x / float(steps)
#    for i in range(steps+1):
#        t = float(i + 0.5)*dt
#        result += np.exp(-(t**2))*dt
#    result *= 2 / sqrtpi
#    return result
   
def repos(ln, old_pos, new_pos):
    lb = min(new_pos, old_pos)
    ub = max(new_pos, old_pos)
    adj_range = []
    if new_pos < old_pos:
        adj_range.append(old_pos)
        adj_range += range(lb, ub)
    else:
        adj_range += range(lb+1, ub+1)
        adj_range.append(old_pos)
    return range(0,lb) + adj_range + range(ub,ln-1)
    
def simple_repos(ln, old_pos, new_pos):
    r1 = range(ln)
    val = r1[old_pos]
    del r1[old_pos]
    r1.insert(new_pos, val)
    return r1
    
def smart_repos(ln, old_pos, new_pos):
    if ln > 65:
        return repos(ln, old_pos, new_pos)
    else:
        return simple_repos(ln, old_pos, new_pos)
        
class DelayedProxy():
    __modified__ = set([])

    def __init__(self, subject):
        self.__subject__ = subject
    def __getattr__(self, name):
        if not name in ["__modified__", "__dict__"]:
            return getattr( self.__subject__, name )
    def __setattr__(self, name, val):
        if not name in ["__modified__", "__dict__"]:
            self.__modified__.add(name)
            self.__dict__[name] = val
    
    def apply_changes(self):
        print "Applying changes made to object of type %s:" % type(self.__subject__)
        for name in self.__modified__:
            if not name in ["__subject__"]:
                print "  - %s" % name
                setattr(self.__subject__, name, self.__dict__[name])
        self.__modified__ = set([])
    
    def discard_changes(self):
        print "Discarding previously made changes to object of type %s:" % type(self.__subject__)
        for name in self.__modified__:
            if not name in ["__subject__"]:
                print "  - %s" % name
                del self.__dict__[name]
        self.__modified__ = set([])
        
def lognormal(T, a, b):
    return sqrt2pi * exp(-(log(T) - a)**2 / (2.0*(b**2))) / (abs(b)*T)
    
    
    
#
# decorator used to create indexable properties (e.g. W[1,1])
#
class indexproperty(object):
    
    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        if doc is None and fget is not None and hasattr(fget, "__doc__"):
            doc = fget.__doc__
        self._get = fget
        self._set = fset
        self._del = fdel
        self.__doc__ = doc
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return boundindexproperty(self, instance)
    
    def __set__(self, instance, value):
        raise AttributeError, "can't set attribute"
    
    def __delete__(self, instance):
        raise AttributeError, "can't delete attribute"
    
    def getter(self, fget):
        return indexproperty(fget, self._set, self._del, self.__doc__)

    def setter(self, fset):
        return indexproperty(self._get, fset, self._del, self.__doc__)
    
    def deleter(self, fdel):
        return indexproperty(self._get, self._set, fdel, self.__doc__)


class boundindexproperty(object):
    
    def __init__(self, item_property, instance):
        self.__item_property = item_property
        self.__instance = instance

    def __getitem__(self, key):
        fget = self.__item_property._get
        if fget is None:
            raise AttributeError, "unreadable attribute item"
        return fget(self.__instance, key)
    
    def __setitem__(self, key, value):
        fset = self.__item_property._set
        if fset is None:
            raise AttributeError, "can't set attribute item"
        fset(self.__instance, key, value)
    
    def __delitem__(self, key):
        fdel = self.__item_property._del
        if fdel is None:
            raise AttributeError, "can't delete attribute item"
        fdel(self.__instance, key)
    
