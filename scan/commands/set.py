'''
Created on Mar 8,2015

@author: qiuyx
'''
from scan.commands.command import Command
try:
    import xml.etree.cElementTree as ET
except:
    import xml.etree.ElementTree as ET

class Set(Command):
    """Set a device to a value.
    
    With optional check of completion and readback verification.
    
    :param device:     Device name
    :param value:      Value
    :param completion: Await callback completion?
    :param readback:   `False` to not check any readback,
                       `True` to wait for readback from the `device`,
                       or name of specific device to check for readback.
    :param tolerance:  Tolerance when checking numeric `readback`.
    :param timeout:    Timeout in seconds, used for `completion` and `readback`.
    :param errhandler: Error handler
    
    Example:
        >>> cmd = Set('position', 10.5)

    Note usage of timeout:
    When the command awaits completion, the timeout is applied to the completion check,
    i.e. we await the completion callback for `timeout` seconds.
    If another readback check is performed after the completion,
    this check is immediate, comparing the readback right now,
    and not waiting for the readback to match within another `timeout` seconds.

    On the other hand, if completion is not used,
    the timeout is applied to the readback check.
    So in case a readback comparison is requested,
    we wait for up to `timeout` seconds for the readback to be within tolerance.    
    """

    def __init__(self, device, value, completion=False, readback=False, tolerance=0.0, timeout=0.0, errhandler=None):
        self.__device = device
        self.__value = value
        self.__completion = completion
        self.__readback = readback
        self.__tolerance = tolerance
        self.__timeout = timeout
        self.__errHandler = errhandler
        
    def getDevice(self):
        """:return: Device name"""
        return self.__device
    
    def setCompletion(self, completion):
        """Change completion
        
        :param completion: Await callback completion?
        """
        self.__completion = completion

    def setReadback(self, readback):
        """Change readback
        
        :param readback: `False` to not check any readback,
               `True` to wait for readback from the `device`,
               or name of specific device to check for readback.
        """
        self.__readback = readback

    def setTolerance(self, tolerance):
        """Change tolerance
        
        :param tolerance:  Tolerance when checking numeric `readback`.
        """
        self.__tolerance = tolerance

    def setTimeout(self, timeout):
        """Change timeout
        
        :param timeout:    Timeout in seconds, used for `completion` and `readback`.
        """
        self.__timeout = timeout
        
    def genXML(self):
        xml = ET.Element('set')

        dev = ET.SubElement(xml, 'device')
        if self.__device:
            dev.text = self.__device
        
        if isinstance(self.__value, str):
            ET.SubElement(xml, 'value').text = '"%s"' % self.__value
        else:
            ET.SubElement(xml, 'value').text = str(self.__value)
        
        need_timeout = False
        if self.__completion:
            ET.SubElement(xml, 'completion').text = 'true'
            need_timeout = True
            
        if self.__readback:
            ET.SubElement(xml, "wait").text = "true"
            ET.SubElement(xml, "readback").text = self.__device if self.__readback == True else self.__readback
            ET.SubElement(xml, "tolerance").text = str(self.__tolerance)
            need_timeout = True
        else:
            ET.SubElement(xml, "wait").text = "false"            
        if need_timeout  and  self.__timeout > 0:
            ET.SubElement(xml, "timeout").text = str(self.__timeout)
        
        if self.__errHandler:
            ET.SubElement(xml,'error_handler').text = self.__errHandler
 
        return xml
    
    def __repr__(self):
        result = "Set('%s'" % self.__device
        if isinstance(self.__value, str):
            result += ", '%s'" % self.__value
        else:
            result += ", %s" % str(self.__value)
        if self.__completion:
            result += ', completion=True'
            if self.__timeout!=0.0:
                result += ', timeout='+str(self.__timeout)
        if isinstance(self.__readback, str):
            result += ", readback='%s'" % self.__readback
            result += ", tolerance=%f" % self.__tolerance
            if not self.__completion and  self.__timeout!=0.0:
                result += ', timeout='+str(self.__timeout)
        elif self.__readback:
            result += ", readback=%s" % str(self.__readback)
            result += ", tolerance='%f'" % self.__tolerance
            if not self.__completion and  self.__timeout!=0.0:
                result += ', timeout='+str(self.__timeout)
        if self.__errHandler:
            result += ", errhandler='%s'" % self.__errHandler
        result+=')'
        return result
    
        
