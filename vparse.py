import re
import json

with open('verilog_code_name.v', 'r') as file:
    verilog_code = file.read()

module_re = re.compile(r"module\s+(\w+)\s*(#\s*\((.?)\))?\s\((.*?)\);", re.DOTALL)
parameter_re = re.compile(r"parameter\s+(\w+)\s*=\s*([\w']+)")
input_re = re.compile(r"input\s+(?:wire|\s)\s*(\[.?\])?\s([\w']+)\s*(,|$)")
output_re = re.compile(r"output\s+(?:reg|wire|\s)\s*(\[.?\])?\s([\w']+)\s*(,|.|$)")
assign_re = re.compile(r"assign\s+(.?)\s=\s*(.*?);")

if_else_regex = (r"\s*if\s*\((.?)\)\s*begin\s(.?)\s*end\s(else\s*if\s*\((.?)\)\s*begin\s(.?)\s*end\s)(else\s*begin\s("
                 r".*?)\s*end)?")
if_else_blocks = re.findall(if_else_regex, verilog_code, re.DOTALL)

clock_signal = None
