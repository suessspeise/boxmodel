# box model class
import numpy as np
import matplotlib.pyplot as plt

    
class Registry:
    reg = None

    def __init__(self):
        self.reg = dict()

    def check_key(self, key):
        return key in self.reg.keys()

    def check_id(self, name):
        return id(name) in [id(val) for val in self.reg.values()]

    def register(self, key, var):
        if self.check_key(key):
            raise AttributeError(f"variable with id \'{id(var)}\' already registered")
        else:
            if self.check_id(var):
                raise AttributeError(f"key \'{key}\' already registered")
            else:
                self.reg[key] = var

    def get(self, key):
        return self.reg[key][0] # regarding [0], see comment in BasicBox.__init__()
    def get_ref(self, key):
        return self.reg[key]

    def set(self, key, value):
        self.reg[key][0] = value

    def keys(self):
        return list(self.reg.keys())
        return self.reg.keys()
    def values(self):
        return self.reg.values()
    def items(self):
        return self.reg.items()
    def identities(self):
        return [id(k) for k in self.reg.values()]


class BasicBox:
    attr = None

    def __init__(self, attributes):
        self.attr = dict()
        for key, value in attributes.items():
            # this is an ugly trick to circumvent Pythons naming system
            # instead of referencing an inmutable e.g. integer or float
            # we wrap the value in a mutable list, thus forcing python to not use an identical object
            # see: https://realpython.com/pointers-in-python/
            wrapped_val = list()
            wrapped_val.append(value)
            self.attr[key] = wrapped_val

    def __str__(self):
        sep = ','
        attributes = ''
        for e in list(self.attr.keys()): attributes += (e + sep)
        return f"Box[{attributes[0:-len(sep)]}]"

    def get(self, key):
        return self.attr[key][0] # regarding [0], see comment in BasicBox.__init__()

    def set(self, key, value):
        self.attr[key][0] = value # regarding [0], see comment in BasicBox.__init__()

    def add(self, key, value):
        self.attr[key][0] += value # regarding [0], see comment in BasicBox.__init__()

    def substract(self, key, value):
        self.attr[key][0] -= value # regarding [0], see comment in BasicBox.__init__()
    def sub(self, key, value):
        self.substract(key, value)

    def keys(self):
        return self.attr.keys()


class Delta(BasicBox):

    scaling_factor = None

    def __init__(self, original_box, time_step_length):
        self.attr = dict()
        for key in original_box.keys():
            self.attr[key] = [0.0] # regarding [0.0], see comment in BasicBox.__init__()
            self.scaling_factor = time_step_length

    def scale(self, key, value):
        self.attr[key][0] = self.attr[key][0] * value # regarding [0], see comment in BasicBox.__init__()

    def get_delta(self, key):
        return self.attr[key][0] * self.scaling_factor # regarding [0], see comment in BasicBox.__init__()


class Box(BasicBox):

    processes = None
    process_registry = None
    delta = None

    def list_processes(self):
        return self.processes.keys()

    def add_process(self, label, target, func, arg_names, sign='+'):
        if not self.processes:
            self.processes = dict()
            self.process_registry = Registry()
        # don't allow two processes with the same name
        if label in self.processes.keys():
            raise AttributeError(f"process with label \'{label}\' already registered")
        # two processes with the identical setup (and thus effect) are allowed
        else:
            self.processes.update({label : {'func':func, 'target':target, 'arg_names':arg_names, 'sign':sign} })

    def run_processes(self):
        if self.processes: 
            for key in self.processes.keys():
                sign      = self.processes[key]['sign']
                arg_names = self.processes[key]['arg_names']
                args = list()
                for a in arg_names:
                    args.append(*a)
                target    = self.processes[key]['target']
                d = self.processes[key]['func'](*args)
                if sign in ['-', 'minus', 'negative'] : d = d * -1
                self.delta.add(target,   d)

    def do_step(self, step_length=1):
        self.reset_deltas(step_length)
        self.run_processes()
        self.apply_delta()

    def reset_deltas(self, time_step_length):
        self.delta = Delta(self, time_step_length)

    def apply_delta(self):
        for key in self.delta.keys():
            delta = self.delta.get(key) * self.delta.scaling_factor
            self.add(key, delta)

# class BoxModel:
class BoxModel:
    
    step_length  = None
    n_steps_end  = None
    current_step = None
    current_time = None
    boxes    = None
    registry = None
    output   = None
    
    def __init__(self, step=None, step_length=None, n_steps=None,):
        if step: 
            self.n_steps_end = step[0]
            self.step_length = step[1]
        else:
            if timestep: self.step_length = step_length
            if n_steps : self.n_steps_end = n_steps
        self.registry = Registry()
        self.current_step = [0]
        self.current_time = [0.0]
        self.registry.register('step', self.current_step)
        self.registry.register('time', self.current_time)
        
    def add_box(self, label, attributes):
        if not self.boxes:
            self.boxes = dict()
        self.boxes[label] = Box(attributes)
        hashlist = list()
        for key, variable in self.boxes[label].attr.items():
            self.registry.register(f"{label}_{key}", variable)
        return hashlist
    
    def check_setup(self):
        if not self.step_length: return False
        if not self.n_steps: return False
        if len(self.boxes) < 1: return False
        return True
    
    def ref(self, name):
        return self.registry.get_ref(name)
    def get_box(self, label):
        return self.boxes[label]
    
    def set_box(self, label, box):
        if not type(box) == type(Box()):
            raise TypeError()
        self.boxes[label] = box
        
    def get_step(self):
        return self.current_step[0] # regarding [0], see comment in BasicBox.__init__()
    def increment_step(self):
        self.current_step[0] += 1 # regarding [0], see comment in BasicBox.__init__()
    def get_time(self):
        return self.current_time[0] # regarding [0], see comment in BasicBox.__init__()
    def update_time(self):
        self.current_time[0] = self.get_step() * self.step_length # regarding [0], see comment in BasicBox.__init__()
        
    def do_step(self):
        # in case this is the first step: initialise output field:
        if not self.output:
            self.output = {}
            for key in self.registry.keys():
                self.output[key] = []

        # add current states to output field:
        for key in self.registry.keys():
            self.output[key].append(self.registry.get(key))            
            
        # let every box do a step 
        for b in self.boxes.values():
            b.do_step(self.step_length)
        self.increment_step()
        self.update_time()
    
    def run(self):      
        while self.get_step() < self.n_steps_end:
            self.do_step()
        return self.output
                   
    def plot(self, var=None, title=None, figsize=(15,10)):
        fig, ax  = plt.subplots(figsize=figsize)
        if title: fig.suptitle(title)
        if not var:
            var = list(self.output.keys())
            var.remove('time')
            var.remove('step')
        t = self.output['time']
        for v in var:
            data = self.output[v]
            ax.plot(t,data,label=f"{v}\n(max:{np.max(data):.2f}; last: {data[-1]:.2f})")
        ax.legend()
        plt.show
        return fig, ax

