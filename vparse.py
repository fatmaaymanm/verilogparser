import re
import json

with open('atm.v', 'r') as file:
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

clock_re = re.compile(r"input\s+(?:wire|\s)+(?:clk|clock|CLK|\s)\s*(\[.?\])?\s([\w']+)\s*(,|$)")
match = clock_re.search(verilog_code)

if match:
    clock_signal = match.group(1)

# define a dictionary to hold the always block information
always_dict = {}
sensitivity_dict = {}
always_count = 0

# iterate through the code line by line
current_block = None
if_else_flag = None
sensitive_block = {}

# initialize case flag and dictionary
case_flag = False
case_dict = {}

# Extract the module name and parameters
match = module_re.search(verilog_code)
match2 = parameter_re.findall(verilog_code)
if match:
    module_name = match.group(1)
    parameter_list = match2
    print(parameter_list)
    # Extract parameter names and values
    parameters = {}
    for match in parameter_list:
        parameter_name = match.group(1)
        parameter_value = match.group(2)
        # If the parameter value contains a parameter name, replace it with the actual value
        if parameter_value in parameters:
            parameter_value = parameters[parameter_value]
        elif parameter_value.isdigit():
            parameter_value = int(parameter_value)
        parameters[parameter_name] = parameter_value

    # Replace parameter values in input and output declarations
    verilog_code = parameter_re.sub("", verilog_code)  # Remove parameter declarations from code
    inputs = []
    input_signals = []
    input_temp = {}
    for match in input_re.finditer(verilog_code):
        input_declaration = match.group(0)
        input_name = match.group(2)
        input_width = match.group(1)
        if "[" in input_declaration:  # Extract the width if it's a vector
            input_width2 = match.group(1)
            if "-" in input_width2:  # Replace parameter names with values in the width declaration
                input_width2 = input_width2.replace("[", "").replace("]", "")
                input_width2 = input_width2.split("-")
                input_width2[0] = input_width2[0].replace(list(parameters.keys())[0], str(list(parameters.values())[0]))
                # input_width[1] = input_width[1].replace(list(parameters.keys())[0], str(list(parameters.values())[0]))
                input_width2 = int(input_width2[0])
            else:  # Otherwise, the width is constant
                # input_width = int(input_width.strip("[]"))
                input_width2 = [int(i) for i in match.group(1).strip("[]").split(":")]
                input_width2 = input_width2[0] - input_width2[1] + 1
        else:  # If the input is not a vector, the width is 1
            input_width2 = 1

        if input_width is None:
            input_width = ""

        input_temp = {"name": input_name, "range": (0, (2 ** int(input_width2)) - 1)}
        if input_name != "CLK" and input_name != "RST":
            input_signals.append(input_temp)
            inputs.append((input_name, input_width))

    outputs = []
    output_signals = []
    input_temp = {}
    for match in output_re.finditer(verilog_code):
        output_declaration = match.group(0)
        output_name = match.group(2)
        output_width = match.group(1)

        if output_width is None:
            output_width = ""

        outputs.append((output_name, output_width))

    # Extract continuous assignments
    assignments = assign_re.findall(verilog_code)
else:
    print("Module declaration not found")
