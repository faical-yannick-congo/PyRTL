""" Example 6:  Interfacing with Verilog.

    While there is much more about PyRTL design to discuss, at some point somebody
    might ask you to do something with your code other than have it print
    pretty things out to the terminal.  We provide import from and export to
    Verilog of designs, export of waveforms to VCD, and a set of transforms
    that make doing netlist-level transforms and analyis directly in pyrtl easy.
"""
import sys

# sys.path.append("..")
# need this to get the testexamples working (need abs path)
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) +" /..")

import random
import io
import pyrtl

# ---- Importing From Verilog ----

# Sometimes it is useful to pull in components written in Verilog to be used
# as subcomponents of PyRTL designs or to be subject to analysis written over
# the PyRTL core.   One standard format supported by PyRTL is "blif" format:
# https://www.ece.cmu.edu/~ee760/760docs/blif.pdf

# Many tools supoprt outputing hardware designs to this format, including the
# free open source project "Yosys".   Blif files can then be imported either
# as a string or directly from a file name by the function input_from_blif.
# Here is a simple example of a 1 bit full adder imported and then simulated
# from this blif format.

full_adder_blif = """
# Generated by Yosys 0.3.0+ (git sha1 7e758d5, clang 3.4-1ubuntu3 -fPIC -Os)
.model full_adder
.inputs x y cin
.outputs sum cout
.names $false
.names $true
1
.names y $not$FA.v:12$3_Y
0 1
.names x $not$FA.v:11$1_Y
0 1
.names cin $not$FA.v:15$6_Y
0 1
.names ind3 ind4 sum
1- 1
-1 1
.names $not$FA.v:15$6_Y ind2 ind3
11 1
.names x $not$FA.v:12$3_Y ind1
11 1
.names ind2 $not$FA.v:16$8_Y
0 1
.names cin $not$FA.v:16$8_Y ind4
11 1
.names x y $and$FA.v:19$11_Y
11 1
.names ind0 ind1 ind2
1- 1
-1 1
.names cin ind2 $and$FA.v:19$12_Y
11 1
.names $and$FA.v:19$11_Y $and$FA.v:19$12_Y cout
1- 1
-1 1
.names $not$FA.v:11$1_Y y ind0
11 1
.end
"""

pyrtl.input_from_blif(full_adder_blif)
# have to find the actual wire vectors generated from the names in the blif file
x, y, cin = [pyrtl.working_block().get_wirevector_by_name(s) for s in ['x', 'y', 'cin']]
io_vectors = pyrtl.working_block().wirevector_subset((pyrtl.Input, pyrtl.Output))

# we are only going to trace the input and output vectors for clarity
sim_trace = pyrtl.SimulationTrace(wirevector_subset=io_vectors)
# now simulate the logic with some random inputs
sim = pyrtl.Simulation(tracer=sim_trace)
for i in xrange(15):
    # here we actually generate random booleans for the inputs
    sim.step({
        x: random.choice([0, 1]),
        y: random.choice([0, 1]),
        cin: random.choice([0, 1])
        })
sim_trace.render_trace(symbol_len=5, segment_size=5)


# ---- Exporting to Verilog ----

# However, not only do we want to have a method to import from Verilog, we also
# want a way to export it back out to Verilog as well. To demonstrate PyRTL's
# ability to export in Verilog, we will create a sample 3-bit counter. However
# unlike the example in example2, we extend it to be synchronously resetting.

pyrtl.reset_working_block()

zero = pyrtl.Input(1, 'zero')
counter_output = pyrtl.Output(3, 'counter_output')
counter = pyrtl.Register(3, 'counter')
counter.next <<= pyrtl.mux(zero, counter + 1, 0)
counter_output <<= counter

# The counter gets 0 in the next cycle if the "zero" signal goes high, otherwise just
# counter + 1.  Note that both "0" and "1" are bit extended to the proper length and
# here we are making use of that native add operation.  Let's dump this bad boy out
# to a verilog file and see what is looks like (here we are using StringIO just to
# print it to a string for demo purposes, most likely you will want to pass a normal
# open file).

print "--- PyRTL Representation ---"
print pyrtl.working_block()
print

print "--- Verilog for the Counter ---"
with io.BytesIO() as vfile:
    pyrtl.output_to_verilog(vfile)
    print vfile.getvalue()

print "--- Simulation Results ---"
sim_trace = pyrtl.SimulationTrace([counter_output, zero])
sim = pyrtl.Simulation(tracer=sim_trace)
for cycle in xrange(15):
    sim.step({zero: random.choice([0, 0, 0, 1])})
sim_trace.render_trace()

# We already did the "hard" work of generating a test input for this simulation so
# we might want to reuse that work when we take this design through a verilog toolchain.
# The function output_verilog_testbench grabs the inputs used in the simulation trace
# and sets them up in a standar verilog testbench.

print "--- Verilog for the TestBench ---"
with io.BytesIO() as tbfile:
    pyrtl.output_verilog_testbench(tbfile, sim_trace)
    print tbfile.getvalue()


# Not let's talk about transformations of the hardware block.  Many times when you are
# doing some hardware-level analysis you might wish to ignore higher level things like
# multi-bit wirevectors, adds, concatination, etc. and just thing about wires and basic
# gates.  PyRTL supports "lowering" of designs into this more restricted set of functionality
# though the function "synthesize".  Once we lower a design to this form we can then apply
# basic optimizations like constant propgation and dead wire elimination as well.  By
# printing it out to verilog we can see exactly how the design changed.

print "--- Optimized Single-bit Verilog for the Counter ---"
pyrtl.synthesize()
pyrtl.optimize()

with io.BytesIO() as vfile:
    pyrtl.output_to_verilog(vfile)
    print vfile.getvalue()
