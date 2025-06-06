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

