"""
Enhanced Mermaid Chart Generator
Supports multiple types of Mermaid diagrams for tutorial generation
"""

from typing import List, Dict, Any, Optional
import re


class MermaidChartGenerator:
    """Generate various types of Mermaid charts for documentation and tutorials"""
    
    def __init__(self):
        self.chart_types = {
            'flowchart': self._create_flowchart,
            'sequence': self._create_sequence_diagram,
            'class': self._create_class_diagram,
            'state': self._create_state_diagram,
            'timeline': self._create_timeline,
            'gantt': self._create_gantt_chart,
            'pie': self._create_pie_chart,
            'journey': self._create_user_journey,
            'mindmap': self._create_mindmap,
            'gitgraph': self._create_git_graph,
            'architecture': self._create_architecture_diagram,
            'entity_relationship': self._create_entity_relationship
        }
    
    def generate_chart(self, chart_type: str, data: Dict[str, Any], title: str = "") -> str:
        """Generate a Mermaid chart based on type and data"""
        if chart_type not in self.chart_types:
            return self._create_simple_flowchart(data, title)
        
        return self.chart_types[chart_type](data, title)
    
    def _create_flowchart(self, data: Dict[str, Any], title: str = "") -> str:
        """Create a flowchart diagram"""
        nodes = data.get('nodes', [])
        connections = data.get('connections', [])
        direction = data.get('direction', 'TD')  # TD, LR, BT, RL
        
        chart = f"```mermaid\nflowchart {direction}\n"
        
        if title:
            chart += f"    %% {title}\n"
        
        # Add nodes
        for node in nodes:
            node_id = node.get('id', '')
            label = node.get('label', '')
            shape = node.get('shape', 'rect')  # rect, round, circle, diamond, etc.
            style_class = node.get('class', '')
            
            if shape == 'rect':
                chart += f'    {node_id}["{label}"]'
            elif shape == 'round':
                chart += f'    {node_id}("{label}")'
            elif shape == 'circle':
                chart += f'    {node_id}(("{label}"))'
            elif shape == 'diamond':
                chart += f'    {node_id}{{{label}}}'
            elif shape == 'hexagon':
                chart += f'    {node_id}{{{{{label}}}}}'
            else:
                chart += f'    {node_id}["{label}"]'
            
            if style_class:
                chart += f':::{style_class}'
            chart += '\n'
        
        # Add connections
        for conn in connections:
            from_id = conn.get('from', '')
            to_id = conn.get('to', '')
            label = conn.get('label', '')
            style = conn.get('style', 'solid')  # solid, dotted, thick
            
            if style == 'dotted':
                arrow = '-..->'
            elif style == 'thick':
                arrow = '==>'
            else:
                arrow = '-->'
            
            if label:
                chart += f'    {from_id} {arrow}|{label}| {to_id}\n'
            else:
                chart += f'    {from_id} {arrow} {to_id}\n'
        
        # Add styling
        chart += self._add_flowchart_styles()
        chart += "```"
        
        return chart
    
    def _create_sequence_diagram(self, data: Dict[str, Any], title: str = "") -> str:
        """Create a sequence diagram showing interactions between actors"""
        participants = data.get('participants', [])
        messages = data.get('messages', [])
        
        chart = "```mermaid\nsequenceDiagram\n"
        
        if title:
            chart += f"    title {title}\n"
        
        # Add participants
        for participant in participants:
            chart += f"    participant {participant}\n"
        
        # Add messages
        for msg in messages:
            from_actor = msg.get('from', '')
            to_actor = msg.get('to', '')
            message = msg.get('message', '')
            msg_type = msg.get('type', 'sync')  # sync, async, response
            
            if msg_type == 'async':
                chart += f"    {from_actor}->>+{to_actor}: {message}\n"
            elif msg_type == 'response':
                chart += f"    {to_actor}-->>-{from_actor}: {message}\n"
            else:
                chart += f"    {from_actor}->>+{to_actor}: {message}\n"
        
        chart += "```"
        return chart
    
    def _create_class_diagram(self, data: Dict[str, Any], title: str = "") -> str:
        """Create a class diagram"""
        classes = data.get('classes', [])
        relationships = data.get('relationships', [])
        
        chart = "```mermaid\nclassDiagram\n"
        
        if title:
            chart += f"    %% {title}\n"
        
        # Add classes
        for cls in classes:
            class_name = cls.get('name', '')
            attributes = cls.get('attributes', [])
            methods = cls.get('methods', [])
            
            chart += f"    class {class_name} {{\n"
            
            # Add attributes
            for attr in attributes:
                visibility = attr.get('visibility', '+')  # +, -, #, ~
                name = attr.get('name', '')
                type_hint = attr.get('type', '')
                chart += f"        {visibility}{name}: {type_hint}\n"
            
            # Add methods
            for method in methods:
                visibility = method.get('visibility', '+')
                name = method.get('name', '')
                params = method.get('params', '')
                return_type = method.get('return', '')
                chart += f"        {visibility}{name}({params}): {return_type}\n"
            
            chart += "    }\n"
        
        # Add relationships
        for rel in relationships:
            from_class = rel.get('from', '')
            to_class = rel.get('to', '')
            rel_type = rel.get('type', 'association')  # inheritance, composition, aggregation, association
            
            if rel_type == 'inheritance':
                chart += f"    {from_class} --|> {to_class}\n"
            elif rel_type == 'composition':
                chart += f"    {from_class} *-- {to_class}\n"
            elif rel_type == 'aggregation':
                chart += f"    {from_class} o-- {to_class}\n"
            else:
                chart += f"    {from_class} --> {to_class}\n"
        
        chart += "```"
        return chart
    
    def _create_state_diagram(self, data: Dict[str, Any], title: str = "") -> str:
        """Create a state diagram"""
        states = data.get('states', [])
        transitions = data.get('transitions', [])
        
        chart = "```mermaid\nstateDiagram-v2\n"
        
        if title:
            chart += f"    %% {title}\n"
        
        # Add states
        for state in states:
            state_id = state.get('id', '')
            label = state.get('label', '')
            if label and label != state_id:
                chart += f"    {state_id}: {label}\n"
        
        # Add transitions
        for trans in transitions:
            from_state = trans.get('from', '')
            to_state = trans.get('to', '')
            trigger = trans.get('trigger', '')
            
            if trigger:
                chart += f"    {from_state} --> {to_state}: {trigger}\n"
            else:
                chart += f"    {from_state} --> {to_state}\n"
        
        chart += "```"
        return chart
    
    def _create_timeline(self, data: Dict[str, Any], title: str = "") -> str:
        """Create a timeline diagram"""
        events = data.get('events', [])
        
        chart = "```mermaid\ntimeline\n"
        
        if title:
            chart += f"    title {title}\n"
        
        for event in events:
            period = event.get('period', '')
            items = event.get('items', [])
            
            chart += f"    {period}\n"
            for item in items:
                chart += f"        : {item}\n"
        
        chart += "```"
        return chart
    
    def _create_gantt_chart(self, data: Dict[str, Any], title: str = "") -> str:
        """Create a Gantt chart"""
        tasks = data.get('tasks', [])
        
        chart = "```mermaid\ngantt\n"
        
        if title:
            chart += f"    title {title}\n"
        
        chart += "    dateFormat  YYYY-MM-DD\n"
        
        for task in tasks:
            name = task.get('name', '')
            status = task.get('status', '')  # done, active, milestone, crit
            start_date = task.get('start', '')
            duration = task.get('duration', '')
            
            chart += f"    {name}    :{status}, {start_date}, {duration}\n"
        
        chart += "```"
        return chart
    
    def _create_pie_chart(self, data: Dict[str, Any], title: str = "") -> str:
        """Create a pie chart"""
        data_points = data.get('data', [])
        
        chart = "```mermaid\npie"
        
        if title:
            chart += f" title {title}"
        
        chart += "\n"
        
        for point in data_points:
            label = point.get('label', '')
            value = point.get('value', 0)
            chart += f'    "{label}": {value}\n'
        
        chart += "```"
        return chart
    
    def _create_user_journey(self, data: Dict[str, Any], title: str = "") -> str:
        """Create a user journey map"""
        steps = data.get('steps', [])
        
        chart = "```mermaid\njourney\n"
        
        if title:
            chart += f"    title {title}\n"
        
        for step in steps:
            section = step.get('section', '')
            actions = step.get('actions', [])
            
            chart += f"    section {section}\n"
            for action in actions:
                name = action.get('name', '')
                score = action.get('score', 5)
                actors = action.get('actors', [])
                chart += f"        {name}: {score}: {', '.join(actors)}\n"
        
        chart += "```"
        return chart
    
    def _create_mindmap(self, data: Dict[str, Any], title: str = "") -> str:
        """Create a mindmap"""
        root = data.get('root', 'Root')
        branches = data.get('branches', [])
        
        chart = "```mermaid\nmindmap\n"
        chart += f"  root({root})\n"
        
        for branch in branches:
            name = branch.get('name', '')
            items = branch.get('items', [])
            
            chart += f"    {name}\n"
            for item in items:
                chart += f"      {item}\n"
        
        chart += "```"
        return chart
    
    def _create_git_graph(self, data: Dict[str, Any], title: str = "") -> str:
        """Create a Git graph"""
        commits = data.get('commits', [])
        
        chart = "```mermaid\ngitgraph\n"
        
        if title:
            chart += f"    %% {title}\n"
        
        for commit in commits:
            action = commit.get('action', 'commit')
            message = commit.get('message', '')
            branch = commit.get('branch', '')
            
            if action == 'commit':
                chart += f"    commit id: \"{message}\"\n"
            elif action == 'branch':
                chart += f"    branch {branch}\n"
            elif action == 'checkout':
                chart += f"    checkout {branch}\n"
            elif action == 'merge':
                chart += f"    merge {branch}\n"
        
        chart += "```"
        return chart
    
    def _create_architecture_diagram(self, data: Dict[str, Any], title: str = "") -> str:
        """Create an architecture diagram using C4 model style"""
        components = data.get('components', [])
        relationships = data.get('relationships', [])
        
        chart = "```mermaid\nflowchart TB\n"
        
        if title:
            chart += f"    %% {title}\n"
        
        # Add components with different styles
        for comp in components:
            comp_id = comp.get('id', '')
            name = comp.get('name', '')
            comp_type = comp.get('type', 'component')  # system, container, component
            
            if comp_type == 'system':
                chart += f'    {comp_id}["{name}"]:::system\n'
            elif comp_type == 'container':
                chart += f'    {comp_id}["{name}"]:::container\n'
            else:
                chart += f'    {comp_id}["{name}"]:::component\n'
        
        # Add relationships
        for rel in relationships:
            from_comp = rel.get('from', '')
            to_comp = rel.get('to', '')
            description = rel.get('description', '')
            
            if description:
                chart += f'    {from_comp} -->|{description}| {to_comp}\n'
            else:
                chart += f'    {from_comp} --> {to_comp}\n'
        
        # Add C4 styling
        chart += """
    classDef system fill:#1168bd,stroke:#0b4884,color:#ffffff
    classDef container fill:#438dd5,stroke:#2e6295,color:#ffffff
    classDef component fill:#85bbf0,stroke:#5d82a8,color:#000000
"""
        
        chart += "```"
        return chart
    
    def _create_entity_relationship(self, data: Dict[str, Any], title: str = "") -> str:
        """Create an Entity Relationship diagram"""
        entities = data.get('entities', [])
        relationships = data.get('relationships', [])
        
        chart = "```mermaid\nerDiagram\n"
        
        if title:
            chart += f"    %% {title}\n"
        
        # Add entities
        for entity in entities:
            name = entity.get('name', '')
            attributes = entity.get('attributes', [])
            
            chart += f"    {name} {{\n"
            for attr in attributes:
                attr_name = attr.get('name', '')
                attr_type = attr.get('type', 'string')
                is_key = attr.get('key', False)
                
                if is_key:
                    chart += f"        {attr_type} {attr_name} PK\n"
                else:
                    chart += f"        {attr_type} {attr_name}\n"
            chart += "    }\n"
        
        # Add relationships
        for rel in relationships:
            from_entity = rel.get('from', '')
            to_entity = rel.get('to', '')
            relationship = rel.get('relationship', 'one-to-many')  # one-to-one, one-to-many, many-to-many
            
            if relationship == 'one-to-one':
                chart += f"    {from_entity} ||--|| {to_entity} : has\n"
            elif relationship == 'one-to-many':
                chart += f"    {from_entity} ||--o{{ {to_entity} : has\n"
            elif relationship == 'many-to-many':
                chart += f"    {from_entity} }}o--o{{ {to_entity} : has\n"
        
        chart += "```"
        return chart
    
    def _create_simple_flowchart(self, data: Dict[str, Any], title: str = "") -> str:
        """Create a simple flowchart for fallback"""
        abstractions = data.get('abstractions', [])
        relationships = data.get('relationships', [])
        
        chart = "```mermaid\nflowchart TD\n"
        
        if title:
            chart += f"    %% {title}\n"
        
        # Create simple nodes from abstractions
        for i, abstraction in enumerate(abstractions[:8]):  # Limit to 8 nodes
            name = abstraction.get('name', f'Item {i+1}')
            node_id = f"A{i+1}"
            display_name = name[:15] + "..." if len(name) > 15 else name
            chart += f'    {node_id}["{display_name}"]\n'
        
        # Add some basic connections
        for i in range(min(len(abstractions) - 1, 7)):
            chart += f"    A{i+1} --> A{i+2}\n"
        
        chart += "```"
        return chart
    
    def _add_flowchart_styles(self) -> str:
        """Add common styling for flowcharts"""
        return """
    classDef foundation fill:#e1f5fe,stroke:#0277bd,stroke-width:2px,color:#000
    classDef core fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#000
    classDef advanced fill:#fff3e0,stroke:#f57c00,stroke-width:2px,color:#000
    classDef highlight fill:#ffebee,stroke:#c62828,stroke-width:3px,color:#000
"""
    
    def generate_code_flow_chart(self, code_analysis: Dict[str, Any]) -> str:
        """Generate a flowchart specifically for code flow analysis"""
        functions = code_analysis.get('functions', [])
        classes = code_analysis.get('classes', [])
        dependencies = code_analysis.get('dependencies', [])
        
        nodes = []
        connections = []
        
        # Add function nodes
        for i, func in enumerate(functions[:6]):
            nodes.append({
                'id': f'F{i+1}',
                'label': func.get('name', f'Function {i+1}'),
                'shape': 'rect',
                'class': 'core'
            })
        
        # Add class nodes
        for i, cls in enumerate(classes[:4]):
            nodes.append({
                'id': f'C{i+1}',
                'label': cls.get('name', f'Class {i+1}'),
                'shape': 'round',
                'class': 'foundation'
            })
        
        # Add connections based on dependencies
        for dep in dependencies[:8]:
            from_item = dep.get('from', '')
            to_item = dep.get('to', '')
            # Simplified mapping - in real implementation you'd map actual names to IDs
            connections.append({
                'from': 'F1',
                'to': 'F2',
                'style': 'solid'
            })
        
        data = {
            'nodes': nodes,
            'connections': connections,
            'direction': 'TD'
        }
        
        return self._create_flowchart(data, "Code Flow Analysis")


def create_tutorial_charts(shared_state: Dict[str, Any]) -> Dict[str, str]:
    """Create various charts for tutorial based on shared state data"""
    generator = MermaidChartGenerator()
    charts = {}
    
    abstractions = shared_state.get('abstractions', [])
    relationships = shared_state.get('relationships', {})
    chapters = shared_state.get('chapters', [])
    
    # 1. Architecture Overview Flowchart
    if abstractions:
        arch_data = {
            'nodes': [
                {
                    'id': f'A{i+1}',
                    'label': abs_item.get('name', f'Item {i+1}')[:20],
                    'shape': 'rect',
                    'class': abs_item.get('type', 'core').lower()
                }
                for i, abs_item in enumerate(abstractions[:8])
            ],
            'connections': [
                {'from': f'A{i+1}', 'to': f'A{i+2}', 'style': 'solid'}
                for i in range(min(len(abstractions) - 1, 7))
            ],
            'direction': 'TD'
        }
        charts['architecture'] = generator.generate_chart('flowchart', arch_data, "Architecture Overview")
    
    # 2. Learning Journey Timeline
    if chapters:
        timeline_data = {
            'events': [
                {
                    'period': f"Chapter {i+1}",
                    'items': [chapter.get('title', f'Chapter {i+1}')]
                }
                for i, chapter in enumerate(chapters[:6])
            ]
        }
        charts['timeline'] = generator.generate_chart('timeline', timeline_data, "Learning Journey")
    
    # 3. Component Relationships
    if relationships and abstractions:
        rel_list = relationships.get('relationships', [])
        comp_data = {
            'components': [
                {
                    'id': f'comp{i+1}',
                    'name': abs_item.get('name', f'Component {i+1}')[:15],
                    'type': 'component'
                }
                for i, abs_item in enumerate(abstractions[:6])
            ],
            'relationships': [
                {
                    'from': 'comp1',
                    'to': 'comp2',
                    'description': 'uses'
                }
            ]
        }
        charts['components'] = generator.generate_chart('architecture', comp_data, "Component Relationships")
    
    # 4. Learning Progress Pie Chart
    if chapters:
        progress_data = {
            'data': [
                {'label': 'Beginner', 'value': 30},
                {'label': 'Intermediate', 'value': 50},
                {'label': 'Advanced', 'value': 20}
            ]
        }
        charts['progress'] = generator.generate_chart('pie', progress_data, "Learning Distribution")
    
    return charts
