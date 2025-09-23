import os
import sys
import inspect
try:
    thisFilePath = os.path.abspath(__file__)
    print(thisFilePath)
except NameError:
    print("[Notice] The __file__ attribute is unavailable in this environment (e.g., Jupyter or IDLE).")
    print("When using a terminal, make sure the working directory is set to the script's location to prevent path issues (for the DIMA submodule)")
    #print("Otherwise, path to submodule DIMA may not be resolved properly.")
    thisFilePath = os.getcwd()  # Use current directory or specify a default


projectPath = os.path.normpath(os.path.join(thisFilePath, "..", ".."))  # Move up to project root

if projectPath not in sys.path:
    sys.path.insert(0,projectPath)

import yaml
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
    """
    Build and manage a Renku workflow definition (YAML-based).
    Steps can be added, merged, serialized, and reloaded.
    """

    def __init__(self, name):
        """
        Initialize a workflow builder.

        Args:
            name (str): Workflow name.
        """
        self.name = name
        self.directory_path = os.path.join(projectPath, 'workflows').replace(os.sep, '/')
        self.steps = OrderedDict()

    @staticmethod    
    def _hash_content(step_def):
        """
        Compute a stable hash of a step definition (for collision detection).
        """
        import json, hashlib
        content_str = json.dumps(step_def, sort_keys=True, default=str)
        return hashlib.md5(content_str.encode()).hexdigest()

    @staticmethod
    def _normalize_paths(items : list):
        """
        Normalize file paths inside a list of (key, value) pairs.
        """
        if not items:
            return items
        normalized = []
        for key, value in items:
            if isinstance(value, dict) and 'path' in value:
                value['path'] = value['path'].replace(os.sep, '/')
            normalized.append({key: value})
        return normalized

    def create_workflow_file(self):
        """
        Create (or update) a workflow YAML file on disk.
        """
        self.save_to_file(self.directory_path)
        filepath = os.path.join(self.directory_path, f'{self.name}.yaml').replace(os.sep, '/')
        if os.path.exists(filepath):        
            print(f'Workflow file created at : {filepath}')
        # TODO: add else-case handling (currently silent if file not created)

    def add_step(self, step_name, base_command, 
                 inputs : list = [], 
                 outputs : list = [], 
                 parameters : list = []):
        """
        Add a step to the workflow and persist it to file.
        Normalizes input/output/parameter paths and avoids duplicates.
        """
        command = generate_command(base_command, inputs, outputs, parameters)
        step = {'command': command}

        step['inputs'] = self._normalize_paths(inputs) 
        step['outputs'] = self._normalize_paths(outputs) 
        step['parameters'] = self._normalize_paths(parameters)

        # Deduplicate or version step
        if step_name not in self.steps: 
            self.steps[step_name] = step
        elif self.steps[step_name] != step: 
            content_hash = self._hash_content(step)
            hashed_name = f"{step_name}_{content_hash[:8]}"
            print(f"[Added] Step '{step_name}' as '{hashed_name}'")
            self.steps[hashed_name] = step

        self.save_to_file(self.directory_path)

    def run_and_add_step(self, step, *args, **kwargs):
        """
        Run a step function, collect its provenance, and add it to the workflow.
        """
        file_path = inspect.getfile(step)
        step_name = os.path.splitext(os.path.basename(file_path))[0] 
        provenance = step(*args, **kwargs)
        # TODO: validate provenance has 'inputs', 'outputs', 'parameters'
        self.add_step(step_name, "python",
                      provenance["inputs"],
                      provenance["outputs"],
                      provenance["parameters"])
        return provenance

    @staticmethod
    def parse_workflow(yaml_content: str):
        """
        Parse YAML content and return a populated RenkuWorkflowBuilder.
        """
        data = yaml.safe_load(yaml_content)
        builder = RenkuWorkflowBuilder(data['name'])

        for step_name, step_def in data['steps'].items():
            builder.steps[step_name] = {
                'command': step_def.get('command'),
                'inputs': [{k: v} for item in step_def.get('inputs', []) for k, v in item.items()] if step_def.get('inputs') else [],
                'outputs': [{k: v} for item in step_def.get('outputs', []) for k, v in item.items()] if step_def.get('outputs') else [],
                'parameters': [{k: v} for item in step_def.get('parameters', []) for k, v in item.items()] if step_def.get('parameters') else []
            }
        return builder

    @staticmethod
    def from_file(filepath):
        """
        Load a workflow from file, or return a new empty one if file does not exist.
        """
        if not os.path.exists(filepath):
            workflow_name = os.path.splitext(os.path.basename(filepath))[0] 
            return RenkuWorkflowBuilder(name=workflow_name)
        with open(filepath, 'r') as f:
            return RenkuWorkflowBuilder.parse_workflow(f.read())

    def to_dict(self):
        """
        Return workflow definition as a dict, normalizing paths in inputs/outputs.
        """
        for step_name, step_value in self.steps.items():
            for segment in ['inputs', 'outputs']:
                for item in step_value.get(segment, []):
                    for _, value in item.items():
                        if not isinstance(value, dict):
                            raise ValueError(
                                f"Invalid input. Step {step_name} must have {segment} as dict or str type."
                            )
                        if 'path' in value:
                            value['path'] = value['path'].replace(os.sep, '/')

        return {'name': self.name, 'steps': dict(self.steps)}

    def to_yaml(self):
        """
        Serialize workflow definition to YAML.
        """
        return yaml.dump(self.to_dict(), sort_keys=False)

    def append_from(self, other, force=False):
        """
        Merge steps from another workflow into this one.
        If step content differs, a hashed suffix is added.
        """
        if other.name != self.name:
            raise ValueError(f"Cannot merge workflows with different names: {self.name} != {other.name}")
        curr_steps = self.steps.copy()
        for step_name, step_def in other.steps.items():
            if step_name not in curr_steps:
                self.steps[step_name] = step_def
            elif self.steps[step_name] != step_def:
                content_hash = self._hash_content(step_def)
                hashed_name = f"{step_name}_{content_hash[:8]}"
                if hashed_name not in self.steps:
                    self.steps[hashed_name] = step_def
                    print(f"[Added] Step '{step_name}' → '{hashed_name}'")

    def save_to_file(self, directory):
        """
        Save workflow definition to a YAML file in the given directory.
        Merges with existing file if present.
        """
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, f"{self.name}.yaml")

        if os.path.exists(filepath):
            existing = RenkuWorkflowBuilder.from_file(filepath)
            if existing and existing.name == self.name:
                existing.append_from(self)
                with open(filepath, 'w') as f:
                    f.write(existing.to_yaml())
                return

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
    #dot.view()

    # For SVG or PDF, you may want to return the file path or raw output instead of Image()
    if output_format.lower() in ['png', 'jpg', 'jpeg', 'gif']:
        return Image(output_path + f".{output_format}")
    else:
        print(f"Graph saved to: {output_path}.{output_format}")
        return output_path + f".{output_format}"
