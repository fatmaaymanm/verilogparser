import re
import json

with open('atm.v', 'r') as file:
    verilog_code = file.read()

########### PORTS ################################

module_re = re.compile(r"module\s+(\w+)\s*(#\s*\((.?)\))?\s\((.*?)\);", re.DOTALL)
port_pattern = re.compile(r"\s*(?:input|output\s+(?:reg|wire|\s)|\s)\s*(\[.*?\])?\s([\w']+)")
input_re = re.compile(r"\s*(input)\s+(\[.*?\])?\s*(\w+)\s*(,|\))")
output_re = re.compile(r"\s*(output\s+(?:reg|wire|\s))\s*(\[.*?\])?\s*(\w+)\s*(|\))")
assign_re = re.compile(r"assign\s+(.?)\s=\s*(.*?);")
verilog_module_pattern = re.compile(r"^\s*module\s+(\w+)\s*\((.*?)\);", re.DOTALL | re.MULTILINE)

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
match2 = input_re.search(verilog_code)

if match:
    module_name = match.group(1)
    port_string = match.group(4)
    # Extract parameter names and values
    ports = {}
    for match in port_pattern.finditer(port_string):
        port_width = match.group(1)
        port_name = match.group(2)
        if port_width in ports:
            port_width = ports[port_width]
        elif port_width is None:
            port_width = 0
        elif port_width.isdigit():
            port_width = int(port_width)
        ports[port_name] = port_width
    # Replace parameter values in input and output declarations
    # verilog_code = port_pattern.sub("", verilog_code)  # Remove parameter declarations from code
    inputs = []
    input_signals = []
    input_temp = {}

    for match in input_re.finditer(port_string):
        input_declaration = match.group(0)
        input_width = match.group(2)
        input_name = match.group(3)
        if "[" in input_declaration:  # Extract the width if it's a vector
            input_width2 = match.group(2)
            if ":" in input_width2:  # Replace parameter names with values in the width declaration
                input_width2 = input_width2.replace("[", "").replace("]", "")
                input_width2 = input_width2.split(":")
                input_width2[0] = input_width2[0].replace(list(ports.keys())[0], str(list(ports.values())[0]))
                # # input_width[1] = input_width[1].replace(list(parameters.keys())[0], str(list(parameters.values(
                # ))[0]))
                input_width2 = int(input_width2[0]) + 1
            # else:  # Otherwise, the width is constant
            #     ## input_width = int(input_width.strip("[]"))
            #     input_width2 = [int(i) for i in match.group(2).strip("[]").split(":")]
            #     print(input_width2)
                # input_width2 = input_width2[0] - input_width2[1] + 1
        else:  # If the input is not a vector, the width is 1
            input_width2 = 1

        if input_width is None:
            input_width = ""

        input_temp = {"name": input_name, "range": (0, (2 ** int(input_width2)) - 1)}

        if input_name != "clk" and input_name != "rst":
            input_signals.append(input_temp)
            inputs.append((input_name, input_width))

    outputs = []
    output_signals = []
    output_temp = {}
    for match in output_re.finditer(verilog_code):
        output_declaration = match.group(0)
        output_name = match.group(3)
        output_width = match.group(2)

        if "[" in output_declaration:  # Extract the width if it's a vector
            output_width2 = match.group(2)
            if ":" in output_width2:  # Replace parameter names with values in the width declaration
                output_width2 = output_width2.replace("[", "").replace("]", "")
                output_width2 = output_width2.split(":")
                output_width2[0] = output_width2[0].replace(list(ports.keys())[0], str(list(ports.values())[0]))
                # # input_width[1] = input_width[1].replace(list(parameters.keys())[0], str(list(parameters.values(
                # ))[0]))
                output_width2 = int(output_width2[0]) + 1
            # else:  # Otherwise, the width is constant
            #     ## input_width = int(input_width.strip("[]"))
            #     input_width2 = [int(i) for i in match.group(2).strip("[]").split(":")]
            #     print(input_width2)
                # input_width2 = input_width2[0] - input_width2[1] + 1
        else:  # If the input is not a vector, the width is 1
            output_width2 = 1

        if output_width is None:
            output_width = ""

        outputs.append((output_name, output_width))

#     # Extract continuous assignments
#     assignments = assign_re.findall(verilog_code)
else:
    print("Module declaration not found")

########### ALWAYS ################################

for line in verilog_code.split("\n"):
    # check for sequential always block
    if "always @(" in line and ("posedge" in line or "negedge" in line):
        always_count += 1
        # sensitive_block = []
        # sensitivity_list = re.findall(r"(posedge|negedge)\s+(\w+)", line)
        # if sensitivity_list:
        #     for sensitivity in sensitivity_list:
        #         edge_type = sensitivity[0]
        #         signal_name = sensitivity[1]
        #         sensitivity_dict = {"signal_name": signal_name, "edge_type": edge_type}
        #         sensitive_block.append(sensitivity_dict)
        #         #edge_type = "posedge" if "posedge" in line else "negedge"
        # always_dict[f"always_{always_count}"] = {"sequential": True, "sensitivity":sensitive_block, "if": [], "else if": [], "else": [], "case statement":[]}
        # current_block = always_dict[f"always_{always_count}"]
        # if_else_flag = None
