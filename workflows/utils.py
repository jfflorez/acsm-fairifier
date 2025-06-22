import yaml
import os
from collections import OrderedDict

def generate_command(base_command='python', inputs=None, outputs=None, parameters=None):
    inputs = inputs or []
    outputs = outputs or []
    placeholders = [
        f"${name}"
        for name, value in inputs + parameters + outputs
        if isinstance(value, dict) and not value.get('implicit', False)
    ]
    return f"{base_command} {' '.join(placeholders)}"

class RenkuWorkflowBuilder:
    def __init__(self, name):
        self.name = name
        self.steps = OrderedDict()

    def add_step(self, step_name, base_command, inputs=None, outputs=None, parameters=None):
        command = generate_command(base_command, inputs, outputs,parameters)
        step = {
            'command': command
        }
        if inputs:
            step['inputs'] = [{key: value} for key, value in inputs]
        if outputs:
            step['outputs'] = [{key: value} for key, value in outputs]
        if parameters:
            step['parameters'] = [{key: value} for key, value in parameters] 
        self.steps[step_name] = step

    @staticmethod
    def parse_workflow(yaml_content: str):
        data = yaml.safe_load(yaml_content)
        builder = RenkuWorkflowBuilder(data['name'])

        for step_name, step_def in data['steps'].items():
            command = step_def.get('command')
            inputs = step_def.get('inputs', [])
            outputs = step_def.get('outputs', [])
            parameters = step_def.get('parameters', [])
            builder.steps[step_name] = {
                'command': command,
                'inputs': inputs,
                'outputs': outputs,
                'parameters': parameters
            }
        return builder

    @staticmethod
    def from_file(filepath):
        if not os.path.exists(filepath):
            return None
        with open(filepath, 'r') as f:
            return RenkuWorkflowBuilder.parse_workflow(f.read())

    def to_dict(self):
        for step_name, step_value in self.steps.items():
            for segment in ['inputs','outputs']:
                for item in step_value.get(segment,[]):# ['inputs', 'outputs']:
                    # Go over either inputs or outputs
                    for name, value in item.items():
                        if not isinstance(value, dict):
                            raise ValueError(f"Invalid input. Step {step_name} must have {segment} of either dict or str type.")
                        if isinstance(value, str):
                            continue
                        if isinstance(value, dict) and 'path' in value.keys():
                            value['path'] = value['path'].replace(os.sep, '/')

        return {
            'name': self.name,
            'steps': { key : value for key, value in self.steps.items()}
        }

    def to_yaml(self):
        return yaml.dump(self.to_dict(), sort_keys=False)

    def append_from(self, other, force=False):
        if other.name != self.name:
            raise ValueError(f"Cannot merge workflows with different names: {self.name} != {other.name}")

        for step_name, step_def in other.steps.items():
            if step_name in self.steps:
                if force:
                    print(f"[Overwriting] Step '{step_name}' was overwritten as 'force=True'.")
                    self.steps[step_name] = step_def
                else:
                    print(f"[Skipping] Step '{step_name}' already exists. Use 'force=True' to overwrite.")
            else:
                self.steps[step_name] = step_def

    def save_to_file(self, directory):
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, f"{self.name}.yaml")

        if os.path.exists(filepath):
            existing = RenkuWorkflowBuilder.from_file(filepath)
            if existing and existing.name == self.name:
                existing.append_from(self)
                with open(filepath, 'w') as f:
                    f.write(existing.to_yaml())
                return
        # Save as new
        with open(filepath, 'w') as f:
            f.write(self.to_yaml())

import os
import re
import yaml
from graphviz import Digraph
from IPython.display import Image

def plot_workflow_graph(yaml_file_path, 
                        output_dir=".", 
                        output_name="workflow_graph",
                        output_format="png",
                        dpi=300,
                        show_parameters=False):
    
    def shorten_path(path, keep_start=1, keep_end=2):
        """
        Shortens a long path by keeping a few elements from the start and end.
        E.g. 'a/b/c/d/e/f.txt' -> 'a/.../e/f.txt'
        """
        parts = path.strip('/').split('/')
        if len(parts) <= (keep_start + keep_end):
            return path
        return '/'.join(parts[:keep_start]) + '/.../' + '/'.join(parts[-keep_end:])

    def split_path_label(path):
        parts = path.split('/')
        if len(parts) >= 2:
            return f"{'/'.join(parts[:-1])}/\n{parts[-1]}"
        return path

    # Load YAML workflow file
    with open(yaml_file_path, 'r') as f:
        workflow_full = yaml.safe_load(f)

    dot = Digraph(format=output_format)
    dot.attr(rankdir='LR') #'TB')  # vertical layout
    dot.node_attr.update(fontsize='48')

    # Set DPI only if format supports it (like png)
    if output_format.lower() == 'png':
        dot.attr(dpi=str(dpi))

    used_paths = set()

    for step_name, step in workflow_full['steps'].items():
        # Extract parameters
        params = step.get("parameters", [])
        
        # Extract parameters if enabled
        param_lines = []
        if show_parameters:
            params = step.get("parameters", [])
            for param in params:
                for k, v in param.items():
                    val = v.get("value", "")
                    param_lines.append(f"{k} = {val}")

        param_label = "\n".join(param_lines)
        label = f"{param_label}\n{step_name}" if param_label else step_name

        dot.node(step_name, label=label, shape="box", style="filled", fillcolor="lightblue")

        for input_item in step.get('inputs', []):
            for key, val in input_item.items():
                if isinstance(val, dict) and 'path' in val:
                    path = shorten_path(val['path'])
                    label = split_path_label(path)
                    if path not in used_paths:
                        dot.node(path, label=label, tooltip=path, shape="ellipse", style="filled", fillcolor="lightgrey")
                        used_paths.add(path)
                    dot.edge(path, step_name)

        for output_item in step.get('outputs', []):
            for key, val in output_item.items():
                if isinstance(val, dict) and 'path' in val:
                    path = shorten_path(val['path'])
                    label = split_path_label(path)
                    if path not in used_paths:
                        dot.node(path, label=label, tooltip=path, shape="ellipse", style="filled", fillcolor="lightgreen")
                        used_paths.add(path)
                    dot.edge(step_name, path)

    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_name)
    dot.render(output_path)
    dot.view()

    # For SVG or PDF, you may want to return the file path or raw output instead of Image()
    if output_format.lower() in ['png', 'jpg', 'jpeg', 'gif']:
        return Image(output_path + f".{output_format}")
    else:
        print(f"Graph saved to: {output_path}.{output_format}")
        return output_path + f".{output_format}"
