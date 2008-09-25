"""
Module to represent a hinet node structure or an arbitrary flow in a HTML-file.

This is done via the HiNetHTML class.
"""

import mdp

import switchboard

## CSS for hinet representation. ##

# Warning: In nested tables the top table css overwrites the nested css if
#    they are specified like 'table.flow td' (i.e. all td's below this table).
#    So be careful about hiding/overriding nested td's.
#
# The tables "nodestruct" are used to separate the dimension values from 
# the actual node text.

CSS_HINET = """
<style type="text/css" media="screen">

table.flow {
    border-collapse: separate;
    padding: 3 3 3 3;
    border: 3px double;
    border-color: #003399;
}

table.flow table {
    width: 100%;
    margin-left: 2px;
    margin-right: 2px;
    border-color: #003399; 
}

table.flow td {
    padding: 1 5 1 5;
    border-style: none;
}

table.layer {
    border-collapse: separate;
    border: 2px dashed;
}

table.flownode {
    border-collapse: separate;
    border: 1px dotted;
}

table.nodestruct {
    border-style: none;
}

table.node {
    border-collapse: separate;
    border: 1px solid;
    border-spacing: 2px;
}

td.nodename {
    font-size: normal;
    text-align: center;
}

td.nodeparams {
    font-size: xx-small;
    text-align: left;
}

td.dim {
    font-size: xx-small;
    text-align: center;
    color: #008ADC;
}

</style>
"""


## Node Parameter Writers ##

# These functions are used to define how the internal node structure is 
# represented in the HTML file (the report argument). 
# Custom write functions can be appended to the list.
# Note that the list is worked starting from the end (so subclasses can
# be appended to the end of the list to override their parent class writer).
    
def _write_rect2dswitchboard(node, report):
    report.write('rec. field size (in channels): %d x %d = %d<br>' 
                 % (node.x_field_channels, node.y_field_channels,
                    node.x_field_channels * node.y_field_channels))
    report.write('# of rec. fields (output channels): %d x %d = %d<br>'
                 % (node.x_out_channels, node.y_out_channels,
                    node.x_out_channels * node.y_out_channels))
    report.write('rec. field distances (in channels): (%d, %d) <br>'
                 % (node.x_field_spacing, node.y_field_spacing))
    report.write('channel width: %d' % node.in_channel_dim)
    
def _write_sfa2(node, report):
    report.write('expansion dim: ' + str(node._expnode.output_dim) + ' <br>')
    
def _write_normalnoise(node, r):
    r.write('noise level: ' + str(node.noise_args[1]) + ' <br>')
    r.write('noise offset: ' + str(node.noise_args[0]))
    
# (node class type, write function)
NODE_PARAM_WRITERS = [
    (switchboard.Rectangular2dSwitchboard, _write_rect2dswitchboard),
    (mdp.nodes.SFA2Node, _write_sfa2),
    (mdp.nodes.NormalNoiseNode, _write_normalnoise),
]


# helper class, spares us from adding newline characters to every line 

class NewlineWriteFile(object):
    """Decorator for file-like object.
    
    Adds a newline character to each line written with write().
    """
    
    def __init__(self, file_obj):
        """Wrap the given file-like object."""
        self.file_obj = file_obj
    
    def write(self, str_obj):
        """Write a string to the file object and append a newline character."""
        self.file_obj.write(str_obj + "\n")
        
    def close(self):
        self.file_obj.close()
        
        
class HiNetHTML(object):
    """Create an HTML representation of a hierarchical network.
    
    This works for any MDP flow, especially those which use the hinet package
    to build arbitrary hierarchical networks of nodes. A HiNetHTML object
    parses the internal structure of such a flow to create schematic view. 
    """
    
    def __init__(self, html_file, node_param_writers=tuple(NODE_PARAM_WRITERS),
                 css=CSS_HINET):
        """Prepare everything for the parsing of an actual flow.
        
        html_file -- File like object to which the HTML code is written.
        node_param_writers -- This list specifies functions for special nodes
            to integrate node properties into the HMTL view. The list consists
            of tuples of length two, the first element is the node class name.
            The second is a function which takes an instance of this class and
            the file object to which the output is written (look at the examples
            provided in this module file).
        css -- A string containing the CSS code for the HMTL representation.
            This is then written to the file. Take a look at the default CSS
            before using a custom style
        """
        self.report = NewlineWriteFile(html_file)
        self.node_param_writers = node_param_writers
        self.report.write(css)
    
    def parse_flow(self, flow):
        """Parse the given flow and write the HTML code into the file."""
        r = self.report
        r.write('<table class="flow">')
        r.write('<tr><td class="dim">in-dim: %d</td></tr>' % flow[0].input_dim)
        r.write('<tr><td><table class="nodestruct">')
        for node in flow.flow:
            r.write('<tr><td>')
            self._parse_node(node)
            r.write('</td></tr>')
        r.write('</td></tr></table>')
        r.write('<tr><td class="dim">out-dim: %d</td></tr>' 
                % flow[-1].output_dim)
        r.write('</table>')

    def _parse_node(self, node):
        """Recursively parse the given nodes."""
        r = self.report
        if isinstance(node, mdp.hinet.FlowNode):
            r.write('<table class="flownode">')
            r.write('<tr><td>')
            self._parse_flownode(node)
            r.write('</td></tr>')
        elif isinstance(node, mdp.hinet.Layer):
            r.write('<table class="layer">')
            r.write('<tr><td class="dim">in-dim: %d</td></tr>' % node.input_dim)
            r.write('<tr><td>')
            self._parse_layer(node)
            r.write('</td></tr>')
            r.write('<tr><td class="dim">out-dim: %d' % node.output_dim)
        elif isinstance(node, mdp.Node):
            r.write('<table class="node">')
            r.write('<tr><td class="dim">in-dim: %d</td></tr>' % node.input_dim)
            r.write('<tr><td>')
            self._write_general_node(node)
            r.write('</td></tr>')
            r.write('<tr><td class="dim">out-dim: %d' % node.output_dim)
        r.write('</td></tr>')
        r.write('</table>')
            
    def _parse_flownode(self, flownode):
        """Recursively parse a FlowNode."""
        r = self.report
        r.write('<table class="nodestruct">')
        flow = flownode._flow
        for node in flow.flow:
            r.write('<tr><td>')
            self._parse_node(node)
            r.write('</td></tr>')
        r.write('</table>')
    
    def _parse_layer(self, layer):
        """Recursively parse a Layer."""
        r = self.report
        r.write('<table class="nodestruct">')
        if isinstance(layer, mdp.hinet.CloneLayer):
            r.write('<tr><td class="nodename">')
            r.write(str(layer) + '<br><br>')
            r.write('%d repetitions' % len(layer.nodes))
            r.write('</td>')
            r.write('<td>')
            self._parse_node(layer.node)
            r.write('</td></tr>')
        else: 
            r.write('<tr>')
            for node in layer.nodes:
                r.write('<td>')
                self._parse_node(node)
                r.write('</td>')
            r.write('</tr>')
        r.write('</table>')
    
    def _write_general_node(self, node):
        """Do not recurse further and write the node."""
        r = self.report
        r.write('<table class="nodestruct">')
        r.write('<tr><td class="nodename">')
        r.write(str(node))
        r.write('</td></tr>')
        r.write('<tr><td class="nodeparams">')
        for node_param_writer in self.node_param_writers[::-1]:
            if isinstance(node, node_param_writer[0]):
                node_param_writer[1](node, r)
                break
        r.write('</td></tr>')
        r.write('</table>')
        
            
            
            
            
            
            
            
            
            
            
            
    