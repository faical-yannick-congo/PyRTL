""" Example 4: Debugging

Debugging is half the coding process in software, and in PyRTL, it's no
different. PyRTL provides some additional challenges when it comes to
debugging as a problem may surface long after the error was made. Fortunately,
PyRTL comes with various features to help you find mistakes.
"""

import sys

# need this to get the testexamples working (need abs path)
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) +" /..")

import pyrtl
import random

# Setting the random seed so that this example is deterministic before we start
random.seed(93729473)


# Firstly, we will assume that you have experience debugging code. If you do
# not, we recommend that you look at _________ to get yourself oriented with
# how to debug Python code.


# In this example, we will be building a circuit that adds up three values.
# However, instead of building an add function ourselves or using the
# built-in + function in PyRTL, we will instead use the Kogge-Stone adders
# in RtlLib, the standard library for PyRTL.

# The first step to use the RtlLib is to import it
from rtllib import adders

# building three inputs
in1, in2, in3 = (pyrtl.Input(8, "i" + str(x)) for x in range(1, 4))
out = pyrtl.Output(10, "out")

add1_out = adders.kogge_stone(in1, in2)
add2_out = adders.kogge_stone(add1_out, in2)
out <<= add2_out

# The most basic way of debugging PyRTL is to connect a value to an output wire
# and use the simulation to trace the output. A simple print statement doesn't work
# because the values in the wires are not populated during creation time

# If we want to check the result of the first addition, we can connect an output wire
# to the result wire of the first adder

debug_out = pyrtl.Output(9, "debug_out")
debug_out <<= add1_out

# now simulate the circuit

vals1 = [int(2**random.uniform(1, 8) - 2) for _ in range(20)]
vals2 = [int(2**random.uniform(1, 8) - 2) for _ in range(20)]
vals3 = [int(2**random.uniform(1, 8) - 2) for _ in range(20)]

sim_trace = pyrtl.SimulationTrace()
sim = pyrtl.Simulation(tracer=sim_trace)
for cycle in range(len(vals1)):
    sim.step({in1: vals1[cycle], in2: vals2[cycle], in3: vals3[cycle]})

# in order to get the result data, you do not need to print a waveform of the trace
# You always have the option to just pull the data out of the tracer directly

output = sim_trace.trace
print "in1:       " + str(output[in1])
print "in2:       " + str(output[in2])
print "debug_out: " + str(output[debug_out])

# Below, I am using the ability to directly retrieve the trace data to
# verify the correctness of the first adder

for i in range(len(vals1)):
    assert(output[debug_out][i] == output[in1][i] + output[in2][i])

# ----Wirevector Stack Trace ----

# Another case that might arise is that a certain wire is causing an error to occur
# in your program.
# Wirevector Stack Traces allow you to find out more about where a particular
# wirevector was made in your code. With this enabled the wirevector will
# store exactly were it was created, which should help with issues where
# there is a problem with an indentified wire.

# To enable this, just add the following line before the relevant wirevector
# might be made or at the beginning of the program.

pyrtl.set_debug_mode()

# a test wire to show this feature

test_out = pyrtl.Output(9, "test_out")
test_out <<= adders.kogge_stone(in1, in3)

# Now to retrieve information
wire_trace = test_out.init_call_stack

# This data is generated using the traceback.format_stack() call from the Python
# standard library's Traceback module (look at the Python standard library docs for
# details on the function). Therefore, the stack traces are stored as a list with the
# outermost call first.

for frame in wire_trace:
    print frame

# Storage of Additional Debug Data

# ------------------------------------
# WARNING: the debug information generated by the following two processes are
# not guarenteed to be preserved when functions (eg. pyrtl.synthesize() ) are
# done over the block.
# ------------------------------------

# However, if the stack trace does not give you enough information about the
# wirevector, you can also enbed additional information into the wire itself
# Two ways of doing so is either through manipulating the name of the
# wirevector, or by adding your own custom metadata to the wirevector.


# So far, each input and output wirevector have been given their own names, but
# normal wirevectors can also be given names by supplying the name argument to
# the constructor

dummy_wv = pyrtl.WireVector(1, name="blah")

# Also, because of the flexible nature of Python, you can also add custom
# properties to the wirevector.

dummy_wv.my_custom_property_name = "John Clow is great"
dummy_wv.custom_value_028493 = 13

# removing the wirevector from the block to prevent problems with the rest of
# this example
pyrtl.working_block().remove_wirevector(dummy_wv)

# ---- Trivial Graph Format

# Finally, there is a handy way to view your hardware creations as a graph.  The function
# output_to_trivialgraph will render your hardware a formal that you can then open with the
# free software "yEd" (http://en.wikipedia.org/wiki/YEd).  There are options under the
# "heirachical" rendering to draw something looks quite like a circuit.


import io
print "--- Trivial Graph Format  ---"
with io.BytesIO() as tgf:
    pyrtl.output_to_trivialgraph(tgf)
    print tgf.getvalue()
