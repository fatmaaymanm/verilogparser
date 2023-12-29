import re
import json

with open('mux_logical.v', 'r') as file:
    verilog_code = file.read()

########### PORTS ################################

module_re = re.compile(r"module\s+(\w+)\s*(#\s*\((.?)\))?\s\((.*?)\);", re.DOTALL)
port_pattern = re.compile(r"\s*(?:input|output\s+(?:reg|wire|\s)|\s)\s*(\[.*?\])?\s([\w']+)")
reg_pattern = re.compile(r"\s*(reg)\s+(\[.?\])?\s*(\[.*?\])?\s*(\w+)\s*(|\))")
wire_pattern = re.compile(r"\s*(wire)\s+(\[.?\])?\s*(\[.*?\])?\s*(\w+)\s*(|\))")
input_re = re.compile(r"\s*(input)\s+(\[.*?\])?\s*(\w+)\s*(,|\))")
output_re = re.compile(r"\s*(output\s+(?:reg|wire|\s))\s*(\[.*?\])?\s*(\w+)\s*(|\))")
assign_re = re.compile(r"assign\s+(.?)\s=\s*(.*?);")
blocking_assignment_pattern = re.compile(r'\s*(\S+)\s*(=)\s*(.*?);')
non_blocking_assignment_pattern = re.compile(r'\s*(\S+)\s*(<=)\s*(.*?);')
# and_operator_pattern = re.compile(r'\s*(\S+)\s*(&&)\s*(\S+)\s*')
# or_operator_pattern = re.compile(r'\s*(\S+)\s*(\|\|)\s*(\S+)\s*')
# not_operator_pattern = re.compile(r'\s*(\S+)\s*(!)\s*(\S+)\s*')
logical_operator_pattern = re.compile(r'\s*(\S+)\s*(?:(!)|(&&)|(\|\|)|(^))\s*(\S+)\s*')

if_else_regex = (r"\s*if\s*\((.?)\)\s*begin\s(.?)\s*end\s(else\s*if\s*\((.?)\)\s*begin\s(.?)\s*end\s)(else\s*begin\s("
                 r".*?)\s*end)?")
if_else_blocks = re.findall(if_else_regex, verilog_code, re.DOTALL)


LOGICAL = logical_operator_pattern.findall(verilog_code)



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

# Find the position of the module declaration
module_start = verilog_code.find("module")

# Find the end position of the module declaration (using the first semicolon after "module")
module_end = verilog_code.find(";", module_start)


# Extract the module name and parameters
match = module_re.search(verilog_code)
match2 = input_re.search(verilog_code)
match3 = reg_pattern.search(verilog_code, module_end)
match4 = wire_pattern.search(verilog_code, module_end)
blocking_list = []
non_blocking_list = []
logical_list = []

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
    regs_list = []
    if match3:
        regs_string = match3.group(0)
        # Extract parameter names and values
        regs = {}
        for match3 in reg_pattern.finditer(regs_string):
            reg_width = match3.group(3)
            reg_name = match3.group(4)
            if reg_width in regs:
                reg_width = regs[reg_width]
            elif reg_width is None:
                reg_width = 0
            elif reg_width.isdigit():
                reg_width = int(reg_width)
            regs[reg_name] = reg_width
            if "[" in regs_string:  # Extract the width if it's a vector
                if ":" in reg_width:  # Replace parameter names with values in the width declaration
                    reg_width = reg_width.replace("[", "").replace("]", "")
                    reg_width = reg_width.split(":")
                    reg_width[0] = reg_width[0].replace(list(regs.keys())[0], str(list(regs.values())[0]))
                    reg_width = int(reg_width[0]) + 1
            else:  # If the input is not a vector, the width is 1
                reg_width = 1

            if reg_width is None:
                reg_width = ""

            reg_temp = {"name": reg_name, "range": (0, (2 ** int(reg_width)) - 1)}

            regs_list.append(reg_temp)

    wires_list = []

    if match4:
        wires_string = match4.group(0)
        # Extract parameter names and values
        wires = {}
        for match4 in wire_pattern.finditer(wires_string):
            wire_width = match4.group(3)
            wire_name = match4.group(4)
            if wire_width in wires:
                wire_width = wires[wire_width]
            elif wire_width is None:
                wire_width = 0
            elif wire_width.isdigit():
                wire_width = int(wire_width)
            wires[wire_name] = wire_width

            if "[" in wires_string:  # Extract the width if it's a vector
                if ":" in wire_width:  # Replace parameter names with values in the width declaration
                    wire_width = wire_width.replace("[", "").replace("]", "")
                    wire_width = wire_width.split(":")
                    wire_width[0] = wire_width[0].replace(list(wires.keys())[0], str(list(wires.values())[0]))
                    wire_width = int(wire_width[0]) + 1
            else:  # If the input is not a vector, the width is 1
                wire_width = 1

            if wire_width is None:
                wire_width = ""

            wire_temp = {"name": wire_name, "range": (0, (2 ** int(wire_width)) - 1)}

            wires_list.append(wire_temp)


    # Replace parameter values in input and output declarations
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
                input_width2 = int(input_width2[0]) + 1
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
                output_width2 = int(output_width2[0]) + 1
        else:
            output_width2 = 1

        if output_width is None:
            output_width = ""
        outputs.append((output_name, output_width))

    # Extract continuous assignments
    assignments = assign_re.findall(verilog_code)
else:
    print("Module declaration not found")

########### ALWAYS ################################

for line in verilog_code.split("\n"):
    # check for sequential always block
    if "always @(" in line and ("posedge" in line or "negedge" in line):
        always_count += 1
        sensitive_block = []
        sensitivity_list = re.findall(r"(posedge|negedge)\s+(\w+)", line)
        if sensitivity_list:
            for sensitivity in sensitivity_list:
                edge_type = sensitivity[0]
                signal_name = sensitivity[1]
                sensitivity_dict = {"signal_name": signal_name, "edge_type": edge_type}
                sensitive_block.append(sensitivity_dict)
        always_dict[f"always_{always_count}"] = {"sequential": True, "sensitivity": sensitive_block, "if": [],
                                                 "else if": [], "else": [], "case statement": []}
        current_block = always_dict[f"always_{always_count}"]
        if_else_flag = None
    elif "always @(*)" in line:
        always_count += 1
        always_dict[f"always_{always_count}"] = {"sequential": False, "if": [], "else if": [], "else": [],
                                                 "case statement": []}
        current_block = always_dict[f"always_{always_count}"]
        if_else_flag = None
    elif always_count > 0 and "else if" in line:
        x, statement = line.strip().split("else if")
        match_l = logical_operator_pattern.match(statement)
        if match_l:
            logical_list.append(statement)
        if_dict = {"condition": "", "statements": []}
        current_block["else if"].append(if_dict)
        if_line = line.replace("else if", "").replace("begin", "").strip()
        if_dict["condition"] = if_line
        if_else_flag = "else if"
        # check for if statement inside always block
    elif always_count > 0 and "if" in line:
        x, statement = line.strip().split("if")
        match_l = logical_operator_pattern.match(statement)
        if match_l:
            logical_list.append(statement)
        if_dict = {"condition": "", "statements": []}
        output_signals_dict = {"name": "", "logic": ""}
        current_block["if"].append(if_dict)
        if_line = line.replace("if", "").replace("begin", "").strip()
        if_dict["condition"] = if_line
        if_else_flag = "if"
    elif always_count > 0 and "else" in line:
        else_dict = {"statements": []}
        current_block["else"].append(else_dict)
        if_else_flag = "else"
        # add line to the last if or else statement
    elif always_count > 0 and "case" in line:
        case_flag = True
        output_signals_dict = {"name": "", "logic": ""}
        case_condition = line.replace("case", "").replace("begin", "").strip()
        case_dict[case_condition] = {}
        # check for case conditions and statements
    elif always_count > 0 and case_flag and "endcase" not in line:
        if ":" in line:
            case, statement = line.strip().split(":")
            match_b = blocking_assignment_pattern.match(statement)
            match_nb = non_blocking_assignment_pattern.match(statement)
            if match_b:
                blocking_list.append(statement)
                output, statement = statement.replace(";", "").split("=")
                output_signals_dict["name"] = output.strip()
            elif match_nb:
                non_blocking_list.append(statement)
                output, statement = statement.replace(";", "").split("<=")
                output_signals_dict["name"] = output.strip()
            if "default" in line:
                x = statement.strip()
                output_signals_dict["logic"] += statement.strip()
            else:
                output_signals_dict["logic"] += statement.strip() + " if " + case_condition + " == " + case + " else "
                found = False
                for i in range(len(output_signals)):
                    if output_signals[i]['name'] == output_signals_dict['name']:
                        output_signals[i] = output_signals_dict
                        found = True
                        break

                if not found:
                    output_signals.append(output_signals_dict)
                case_dict[case_condition][case.strip()] = statement.strip()
        else:
            current_block["case statement"].append(case_dict)  ######### zyada now
            case_flag = False

    elif always_count > 0 and if_else_flag == "if":
        if line.strip() != "end":
            if "=" in line and ";" in line:
                output, statement = line.replace(";", "").replace("<", "").split('=')
                output_signals_dict["name"] = output.strip()
            if if_dict["condition"] != "(!rst)":
                output_signals_dict["logic"] = statement.strip() + " if " + if_dict["condition"].replace("(","").replace(")", "")
            current_block["if"][-1]["statements"].append(line.strip())
            current_block["if"][-1]["statements"] = list(filter(None, current_block["if"][-1]["statements"]))
    elif always_count > 0 and if_else_flag == "else if":
        if line.strip() != "end":
            output, statement = line.replace(";", "").replace("<", "").split('=')
            if if_dict["condition"] != "(!RST)":
                output_signals_dict["logic"] += statement.strip() + " if " + if_dict["condition"].replace("(",
                                                                                                          "").replace(
                    ")", " ")
            else:
                output_signals_dict["logic"] += " else " + statement.strip() + " if " + if_dict["condition"].replace(
                    "(", "").replace(")", " ")

            current_block["else if"][-1]["statements"].append(line.strip())
            current_block["else if"][-1]["statements"] = list(filter(None, current_block["else if"][-1]["statements"]))
    elif always_count > 0 and if_else_flag == "else":
        if line.strip() != "end":
            if "=" in line and ";" in line:
                output, statement = line.replace(";", "").replace("<", "").split('=')
                if if_dict["condition"] != "(!RST)":
                    output_signals_dict["logic"] += " else " + statement.strip()
                else:
                    output_signals_dict["logic"] += statement.strip()
            found = False
            for i in range(len(output_signals)):
                if output_signals[i]['name'] == output_signals_dict['name']:
                    output_signals[i] = output_signals_dict
                    found = True
                    break
            if not found:
                output_signals.append(output_signals_dict)

            if line.strip() != "endmodule":
                current_block["else"][-1]["statements"].append(line.strip())
                current_block["else"][-1]["statements"] = list(filter(None, current_block["else"][-1]["statements"]))
############################################################################################################################

# Define an empty dictionary to store the output
output_dict = {}

# print(case_dict)

# Extract continuous assignments
assignments = assign_re.findall(verilog_code)

# Add the module name to the dictionary
output_dict["module_name"] = module_name

# Add the parameters to the dictionary
ports_dict = {}
for name, value in ports.items():
    ports_dict[name] = value

output_dict["ports"] = ports_dict

# Add the inputs to the dictionary
inputs_dict = {}
for name, width in inputs:
    inputs_dict[name] = width

output_dict["input_ports"] = inputs_dict

# Add the outputs to the dictionary
outputs_dict = {}
for name, width in outputs:
    outputs_dict[name] = width

output_dict["output_ports"] = outputs_dict

if always_dict[f"always_{always_count}"]["sequential"] == True:
    output_dict["clk"] = sensitive_block[0]
    output_dict["rst"] = sensitive_block[1]

# Add the Assignments to the dictionary
assign_dict = {}
for lhs, rhs in assignments:
    assign_dict[lhs] = rhs.strip()

output_dict["input_signals"] = input_signals
output_dict["output_signals"] = output_signals
output_dict["regs_list"] = regs_list
output_dict["wires_list"] = wires_list
output_dict["blocking_list"] = blocking_list
output_dict["non_blocking_list"] = non_blocking_list
output_dict["logical_list"] = logical_list
print(output_dict["input_signals"])
print("-----------------------------------")
print(output_dict["output_signals"])  # there is something wrong

############################################################################


print("-----------------------------------------------")
print(output_dict)

print("design_info = {")
for key, value in output_dict.items():
    if key in ['input_signals', 'output_signals', 'regs_list', 'wires_list', 'blocking_list', 'non_blocking_list', 'logical_list']:
        print(f"    '{key}': [")
        for item in value:
            print(f"        {item},")
        print("    ],")
    else:
        print(f"    '{key}': '{value}',")
print("}")

for key, value in always_dict.items():
    print(f"{key}:")
    if isinstance(value, dict):
        for inner_key, inner_value in value.items():
            if isinstance(inner_value, list):
                print(f"    {inner_key}:")
                for inner_item in inner_value:
                    print(f"        {inner_item}")
            else:
                print(f"    {inner_key}: {inner_value}")
    else:
        print(f"    {value}")
