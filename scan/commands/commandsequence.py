'''
Created on Mar 8 ,2015

@author: qiuyx
'''
try:
    import xml.etree.cElementTree as ET
except:
    import xml.etree.ElementTree as ET

from scan.commands.command import Command
from scan.util.xml_helper import indent

class CommandSequence(list):
    """A sequence of scan commands
    
    Basically a list of commands,
    with helper methods to pretty-print
    and convert to the raw XML required by the scan server.
    
    :param commands: One or more commands, or existing list of commands.
    """
    def __init__(self, *commands):
        super(CommandSequence, self).__init__()
        self.append(*commands)
            
    def __iadd__(self, other):
        if isinstance(other, list):
            self.append(*other)
        else:
            self.append(other)
        return self

    def append(self, *commands):
        """Append more commands to the sequence
        
        :param commands: One or more commands, or existing list of commands.
        """
        for command in commands:
            # Append individual command
            if isinstance(command, Command):
                super(CommandSequence, self).append(command)
            else:
                # Assume iterable tuple, list, set, .. and append its content
                self.append(list(command))
    
    def genSCN(self):
        """:return: Command in XML format suitable for scan server"""
        scn = ET.Element('commands')
        for c in self:
            scn.append(c.genXML())
        
        indent(scn)
        return ET.tostring(scn)
    
    def format(self):
        """Format for printing
        
        Example:
            >>> cmds = CommandSequence(Comment('Example'), Loop('pos', 1, 5, 0.5, Set('run', 1), Delay(2), Set('run', 0)))
            >>> print cmds.toSeqString()
            
        Output::
        
            [
              Comment('Example'),
              Loop('pos', 1, 5, 0.5, [ Set('run', 1), Delay(2), Set('run', 0) ])
            ]
            
        """
        if len(self) == 0:
            return "[]"

        result = "["
        for cmd in self:
            result += "\n" + cmd.format(1)
        result += "\n]"
        return result

    def __str__(self):
        return self.format()
    
    def __repr__(self):
        return "CommandSequence(" + str(self) + ")"


if __name__ == "__main__":
    from comment import Comment
    from loop import Loop
    from parallel import Parallel
    
    print CommandSequence(
          [
               Loop('x', 1, 10, 0.5)
          ])

    print CommandSequence(
          [
               Loop('x', 1, 10, 0.5, Comment("Hello"))
          ])

    print CommandSequence(
          [
               Loop('x', 1, 10, 0.5, Comment("Hello"), completion=True)
          ])
 
    print CommandSequence(
          [
               Loop('x', 1, 10, 0.5,
               [
                   Comment("Hello"),
                   Comment("World")
               ], completion=True, timeout=10)
          ])

    print CommandSequence(
          [
               Loop('x', 2, 20, 5,
               [
                   Loop('y', 1, 10, 0.5,
                   [
                       Comment("Hello"),
                       Comment("World")
                   ], completion=True, timeout=10)
               ])
          ])

    print CommandSequence(
          [
               Parallel(
                    Loop('x', 1, 10, 0.5, Comment("Hello")),
                    Loop('y', 1, 10, 0.5, Comment("There"))
               )
          ])
