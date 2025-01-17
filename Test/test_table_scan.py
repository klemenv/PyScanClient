"""Unit test of the TableScan

   To run just a single test:

   python -m unittest test_table_scan.TableScanTest.testBadInput

   @author: Kay Kasemir
"""
import unittest
from scan.commands import Set, Comment, Delay
from scan.table import TableScan
from scan.util import ScanSettings, setScanSettings
from scan.commands.include import Include
from scan.util.seconds import parseSeconds


class MyScanSettings(ScanSettings):
    def __init__(self):
        super(MyScanSettings, self).__init__()
        # Define special settings for some devices
        self.defineDeviceClass("Motor.*", completion=True, readback=True, timeout=100)
        self.defineDeviceClass("InfiniteCounter", comparison="increase by")
        
    def getReadbackName(self, device_name):
        # Motors use their *.RBV field for readback
        if "Motor" in device_name:
            return device_name + ".RBV"
        return device_name

setScanSettings(MyScanSettings())

# TODO 'Comment' column can be comment command or Set('SomeCommentPV')
# TODO Fix Log command
# TODO Start by waiting for all motors to be idle
#         for motor in motors:
#             idle = self.settings.getMotorIdlePV(motor)
#             if idle:
#                 commands.insert(0, WaitCommand(idle, Comparison.EQUALS, 1, 0.1, 5.0))

def handle(table, lineinfo=False):
    print table
    cmds = table.createScan(lineinfo=lineinfo)
    print
    for cmd in cmds:
        print str(cmd)
    return cmds


class TableScanTest(unittest.TestCase):
    def testBasics(self):
        print "\n=== Basic Table ==="
        table_scan = TableScan(
          (   "Comment", "X ",  "Y", "Speed", "Wavelength" ),
          [
            [ "Setup",  "  1",  "2",    "30",           "" ],
            [ "Count",     "",   "",      "",        "100" ],
            [ "Wait",      "",   "",      "",        "200" ],
          ]
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds), "[Comment('Setup'), Set('X', 1.0), Set('Y', 2.0), Set('Speed', 30.0), Comment('Count'), Set('Wavelength', 100.0), Comment('Wait'), Set('Wavelength', 200.0)]")

        cmds = handle(table_scan, lineinfo=True)
        self.assertEqual(str(cmds), "[Comment('# Line 1'), Comment('Setup'), Set('X', 1.0), Set('Y', 2.0), Set('Speed', 30.0), Comment('# Line 2'), Comment('Count'), Set('Wavelength', 100.0), Comment('# Line 3'), Comment('Wait'), Set('Wavelength', 200.0), Comment('# End')]")

        print "\n=== Wait for time ==="
        # Also using numbers instead of strings
        table_scan = TableScan(
          (   "X",  "Y", "Wait For", "Value" ),
          [
            [  1,   2,  "seconds",   10 ],
            [  3,   4,  "time",   20 ],
          ]
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds), "[Set('X', 1.0), Set('Y', 2.0), Delay(10), Log('X', 'Y'), Set('X', 3.0), Set('Y', 4.0), Delay(20), Log('X', 'Y')]")


        print "\n=== Wait for PV ==="
        table_scan = TableScan(
          (   "X",  "Y", "Wait For", "Value" ),
          [
            [ "1",  "2", "Counter1", "10" ],
            [ "3",  "4", "Counter1", "20" ],
          ]
        )
        cmds = handle(table_scan)
        #self.assertEqual(str(cmds), "")


        print "\n=== Wait for PV using 'increment' ==="
        table_scan = TableScan(
          (   "X",  "Y", "Wait For",        "Value" ),
          [
            [ "1",  "2", "Counter1",        "10" ],
            [ "3",  "4", "InfiniteCounter", "20" ],
          ]
        )
        cmds = handle(table_scan)
        #self.assertEqual(str(cmds), "")


        print "\n=== Wait for PV or Max Time ==="
        table_scan = TableScan(
          (   "X",  "Y", "Wait For", "Value", "Or Time" ),
          [
            [ "1",  "2", "Counter1", "10",    "60" ],
            [ "3",  "4", "Counter1", "20",    "00:01:00" ],
          ]
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds), "[Set('X', 1.0), Set('Y', 2.0), Wait('Counter1', 10.0, comparison='>=', tolerance=0.1, timeout=60, errhandler='OnErrorContinue'), Log('X', 'Y', 'Counter1'), Set('X', 3.0), Set('Y', 4.0), Wait('Counter1', 20.0, comparison='>=', tolerance=0.1, timeout=60, errhandler='OnErrorContinue'), Log('X', 'Y', 'Counter1')]")


    def testStartStop(self):
        print "\n=== Start/stop at each step ==="
        table_scan = TableScan(
          (   "X",  "Y", "Wait For", "Value" ),
          [
            [ "1",  "2", "counter", "10" ],
            [ "3",  "4", "counter", "10" ],
          ],
          pre = Set('shutter', 1),
          post = Set('shutter', 0),
          start = [ Set('counter:reset', 1, completion=True),
                    Set('counter:enable', 1, completion=True),
                    Set('daq:enable', 1, completion=True)
                  ],
          stop  = [ Set('daq:enable', 0, completion=True),
                    Set('counter:enable', 0, completion=True)
                  ],
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds), "[Set('shutter', 1), Set('X', 1.0), Set('Y', 2.0), Set('counter:reset', 1, completion=True), Set('counter:enable', 1, completion=True), Set('daq:enable', 1, completion=True), Wait('counter', 10.0, comparison='>=', tolerance=0.1), Log('X', 'Y', 'counter'), Set('daq:enable', 0, completion=True), Set('counter:enable', 0, completion=True), Set('X', 3.0), Set('Y', 4.0), Set('counter:reset', 1, completion=True), Set('counter:enable', 1, completion=True), Set('daq:enable', 1, completion=True), Wait('counter', 10.0, comparison='>=', tolerance=0.1), Log('X', 'Y', 'counter'), Set('daq:enable', 0, completion=True), Set('counter:enable', 0, completion=True), Set('shutter', 0)]")


    def testWaitFor(self):
        print "\n=== 'Wait For' spelled lowercase ==="
        table_scan = TableScan(
          (   "X",  "wait for", "value" ),
          [
            [ "1",  "seconds", "10" ],
          ],
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds), "[Set('X', 1.0), Delay(10), Log('X')]")



    def testScanSettings(self):
        print "\n=== ScanSettings configure Motor for completion and RBV ==="
        table_scan = TableScan(
          (   "X ",  "Motor1" ),
          [
            [ "  1",  "2" ],
          ]
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds), "[Set('X', 1.0), Set('Motor1', 2.0, completion=True, timeout=100, readback='Motor1.RBV', tolerance=0.100000)]")


        print "\n=== Override ScanSettings for Motor ==="
        table_scan = TableScan(
          (   "Motor1",  "-cr Motor2" ),
          [
            [ "  1",  "2" ],
          ]
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds), "[Set('Motor1', 1.0, completion=True, timeout=100, readback='Motor1.RBV', tolerance=0.100000), Set('Motor2', 2.0)]")


    def testParallel(self):
        print "\n=== Parallel without Wait ==="
        table_scan = TableScan(
          (   "+p A", "+p B", "C", "+p D", "+p E", "F" ),
          [
            [ "1",    "2",    "3", "4",    "5",    "6" ],
          ]
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds), "[Parallel(Set('A', 1.0), Set('B', 2.0)), Set('C', 3.0), Parallel(Set('D', 4.0), Set('E', 5.0)), Set('F', 6.0)]")

        print "\n=== Parallel with Wait For ==="
        table_scan = TableScan(
          (   "+p A", "+p B", "C", "+p D", "+p E", "Wait For",   "Value" ),
          [
            [ "1",    "2",    "3", "4",    "5",    "completion", "10"    ],
            [ "6",    "7",    "8", "9",   "10",    "Seconds",    "10"    ],
          ],
          start = Comment('Start Run'),
          stop  = Comment('Stop Run')
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds), "[Parallel(Set('A', 1.0), Set('B', 2.0)), Set('C', 3.0), Comment('Start Run'), Parallel(Set('D', 4.0), Set('E', 5.0)), Log('A', 'B', 'C', 'D', 'E'), Comment('Stop Run'), Parallel(Set('A', 6.0), Set('B', 7.0)), Set('C', 8.0), Parallel(Set('D', 9.0), Set('E', 10.0)), Comment('Start Run'), Delay(10), Log('A', 'B', 'C', 'D', 'E'), Comment('Stop Run')]")

        print "\n=== Parallel with Delay and Wait For ==="
        table_scan = TableScan(
          (   "+p A", "+p B", "Delay",    "Wait For", "Value" ),
          [
            [ "1",    "2",    "00:05:00", "counts",   "10"    ],
          ],
          start = Comment('Start Run'),
          stop  = Comment('Stop Run'),
          special = { 'Delay': lambda cell : Delay(parseSeconds(cell)) } 
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds), "[Parallel(Set('A', 1.0), Set('B', 2.0)), Delay(300), Comment('Start Run'), Wait('counts', 10.0, comparison='>=', tolerance=0.1), Log('A', 'B', 'counts'), Comment('Stop Run')]")

        print "\n=== Parallel with range and Delay ==="
        table_scan = TableScan(
          (   "+p A", "+p B",      "Delay"    ),
          [
            [ "1",    "[2, 4, 6]", "00:05:00" ],
          ],
          special = { 'Delay': lambda cell : Delay(parseSeconds(cell)) } 
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds), "[Parallel(Set('A', 1.0), Set('B', 2.0)), Delay(300), Parallel(Set('A', 1.0), Set('B', 4.0)), Delay(300), Parallel(Set('A', 1.0), Set('B', 6.0)), Delay(300)]")

        print "\n=== Parallel with Timeout ==="
        table_scan = TableScan(
          (   "+p A", "Wait For", "Value", "Or Time"   ),
          [
            [ "1",    "Completion", "", "00:05:00" ],
          ] 
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds), "[Parallel(Set('A', 1.0), timeout=300, errhandler='OnErrorContinue'), Log('A')]")


    def testRange(self):
        print "\n=== Range Cells ==="
        table_scan = TableScan(
          (   " X ",  "Y", ),
          [
            [ "  1",  "", ],
            [ "   ",  "range(5)", ],
            [ "[ 0, 1]", "range(2)", ],
          ]
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds), "[Set('X', 1.0), Set('Y', 0.0), Set('Y', 1.0), Set('Y', 2.0), Set('Y', 3.0), Set('Y', 4.0), Set('X', 0.0), Set('Y', 0.0), Set('X', 0.0), Set('Y', 1.0), Set('X', 1.0), Set('Y', 0.0), Set('X', 1.0), Set('Y', 1.0)]")

        table_scan = TableScan(
          (   " X ", ),
          [
            [ "range(100,200,10)", ]
          ]
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds), "[Set('X', 100.0), Set('X', 110.0), Set('X', 120.0), Set('X', 130.0), Set('X', 140.0), Set('X', 150.0), Set('X', 160.0), Set('X', 170.0), Set('X', 180.0), Set('X', 190.0)]")

        table_scan = TableScan(
          (   " X ", ),
          [
            [ "range(175,246,70)", ]
          ]
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds), "[Set('X', 175.0), Set('X', 245.0)]")

        print "\n=== Likely a misconfigured Range ==="
        # This used to fail by creating Set('X', 'range(175,245,70)')
        table_scan = TableScan(
          (   " X ", ),
          [
            [ "range(175,245,70)", ]
          ]
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds), "[Set('X', 175.0)]")

        table_scan = TableScan(
          (   "X", "Y" ),
          [
            [ "range(1,0,2)", "2" ]
          ]
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds), "[Set('Y', 2.0)]")

        table_scan = TableScan(
          (   "X", "Y" ),
          [
            [ "3", "[]" ]
          ]
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds), "[Set('X', 3.0)]")

        table_scan = TableScan(
          (   "X", "Y" ),
          [
            [ "[3]", "[2]" ]
          ]
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds), "[Set('X', 3.0), Set('Y', 2.0)]")


        print "\n=== Fractional Range Cells ==="
        table_scan = TableScan(
          (   " X ", ),
          [
            [ "range(0.2, 5.4, 0.7)", ]
          ]
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds), "[Set('X', 0.2), Set('X', 0.9), Set('X', 1.6), Set('X', 2.3), Set('X', 3.0), Set('X', 3.7), Set('X', 4.4), Set('X', 5.1)]")

    def testLogAlways(self):
        print "\n=== log_always ==="
        
        table_scan = TableScan(
          (   "X",  "Wait For", "Value", ),
          [
            [ "10",  "seconds",   "10" ]
          ]
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds), "[Set('X', 10.0), Delay(10), Log('X')]")

        table_scan = TableScan(
          (   "X",  "Wait For", "Value", ),
          [
            [ "10",  "seconds",   "10" ]
          ],
          log_always=[ 'neutrons']
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds), "[Set('X', 10.0), Delay(10), Log('neutrons', 'X')]")

    def testLoop(self):
        print "\n=== Loop Cells ==="
        # Plain loop commands
        table_scan = TableScan(
          [   "position" ],
          [
            [ "loop(2, 5, 1)" ],
          ]
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds), "[Loop('position', 2, 5, 1)]")

        table_scan = TableScan(
          (   "position",        "camera"),
          [
            [ "Loop(0, 3, 0.5)", "snap"],
          ]
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds), "[Loop('position', 0, 3, 0.5, [ Set('camera', 'snap') ])]")

        table_scan = TableScan(
          (   "X",          "Y",        "Camera"),
          [
            [ "loop(1,10)", "Loop(2,5)", "Snap"],
          ]
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds), "[Loop('X', 1, 10, 1, [ Loop('Y', 2, 5, 1, [ Set('Camera', 'Snap') ]) ])]")

        # Can be mixed with range or list, but note that list is expanded first.
        # This works as nestet list & loop:
        table_scan = TableScan(
          (   "X",      "Y",      "Camera"),
          [
            [ "[1, 2]", "Loop(3)", "Snap"],
          ]
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds), "[Set('X', 1.0), Loop('Y', 0, 3, 1, [ Set('Camera', 'Snap') ]), Set('X', 2.0), Loop('Y', 0, 3, 1, [ Set('Camera', 'Snap') ])]")

        # Here, however, the list is _first_ expanded into rows
        table_scan = TableScan(
          (   "X",       "Y",      "Camera"),
          [
            [ "Loop(3)", "[1, 2]", "Snap"],
          ]
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds), "[Loop('X', 0, 3, 1, [ Set('Y', 1.0), Set('Camera', 'Snap') ]), Loop('X', 0, 3, 1, [ Set('Y', 2.0), Set('Camera', 'Snap') ])]")

    def testSpecialColumns(self):
        print "\n=== Special columns ==="
        
        # Commands Start/Next/End turn into Include("lf_start.scn"), Include("lf_next.scn") resp. Include("lf_end.scn") 
        special = { 'Run Control': lambda cell : Include(cell + ".scn"),
                    'Delay':       lambda cell : Delay(parseSeconds(cell)),
                  }
        table_scan = TableScan(
          (   "Run Control", "X", "Delay",    "Wait For", "Value", ),
          [
            [ "Start",      "10", "",         "Neutrons",   "10" ],
            [ "",           "20", "00:01:00", "Neutrons",   "10" ],
            [ "Stop",       "",   "",         "",           "" ],
          ],
          special = special
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds),
                         "[Include('Start.scn'), Set('X', 10.0), Wait('Neutrons', 10.0, comparison='>=', tolerance=0.1), Log('X', 'Neutrons'), Set('X', 20.0), Delay(60), Wait('Neutrons', 10.0, comparison='>=', tolerance=0.1), Log('X', 'Neutrons'), Include('Stop.scn')]")        

    def testParallelLoops(self):
        print "\n=== Parallel Loops ==="
        
        # Loops can be 'parallel'
        table_scan = TableScan(
          (   "+p X",    "+p Y", "Z", "Wait For", "Value", ),
          [
            [ "Loop(3)", "",     "",  "time",     "00:01:00" ],
          ]
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds),
                         "[Parallel(Loop('X', 0, 3, 1)), Delay(60), Log('X')]")

        # .. but the result may not be what users want.
        # This loops X, and in parallel it loops Y, the latter doing the nestest 1 minute wait
        table_scan = TableScan(
          (   "+p X",    "+p Y",    "Z", "Wait For", "Value", ),
          [
            [ "Loop(3)", "Loop(5)", "", "time",      "00:01:00" ],
          ]
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds),
                         "[Parallel(Loop('X', 0, 3, 1), Loop('Y', 0, 5, 1)), Delay(60), Log('X', 'Y')]")
        # Parallel loops will _not_ synchronize their steps.
        # That would need a step-by-step table like this:
        table_scan = TableScan(
          (   "+p X", "+p Y", "Z", "Wait For", "Value", ),
          [
            [ "0",    "0",    "", "time",      "00:01:00" ],
            [ "1",    "1",    "", "time",      "00:01:00" ],
            [ "2",    "2",    "", "time",      "00:01:00" ],
          ]
        )
        cmds = handle(table_scan)
        self.assertEqual(str(cmds),
                         "[Parallel(Set('X', 0.0), Set('Y', 0.0)), Delay(60), Log('X', 'Y'), Parallel(Set('X', 1.0), Set('Y', 1.0)), Delay(60), Log('X', 'Y'), Parallel(Set('X', 2.0), Set('Y', 2.0)), Delay(60), Log('X', 'Y')]")

    def testBadInput(self):
        print "\n=== Bad Input ==="
        
        # No list of rows, just single row
        with self.assertRaises(Exception) as context:
            table_scan = TableScan(
              (   "+p X",    "+p Y", "Z", "Wait For", "Value", ),
                [ "Loop(3)", "",     "",  "time",     "00:01:00" ],
            )
        print("Caught: " + str(context.exception))
        self.assertTrue("Table needs list of rows" in str(context.exception))

        # Missing column in rows
        with self.assertRaises(Exception) as context:
            table_scan = TableScan(
              (   "+p X",    "+p Y", "Z", "Wait For", "Value", ),
              [ [ "Loop(3)", "",     "",  "time",     "00:01:00" ],
                [ "Loop(3)", "",     "",  "time",                ],
              ]
            )
        print("Caught: " + str(context.exception))
        self.assertTrue("Table has 5 columns but row 1 has only 4" in str(context.exception))


        # Missing 'Value' column (either nothing or the wrong column)
        with self.assertRaises(Exception) as context:
            table_scan = TableScan(
              (   "+p X",    "+p Y", "Z", "Wait For" ),
              [ [ "Loop(3)", "",     "",  "time",    ],
              ]
            )
            table_scan.createScan()
        print("Caught: " + str(context.exception))
        self.assertTrue("Wait For column must be followed by Value" in str(context.exception))

        with self.assertRaises(Exception) as context:
            table_scan = TableScan(
              (   "+p X",    "+p Y", "Z", "Wait For", "ShouldBeValue", ),
              [ [ "Loop(3)", "",     "",  "time",     "00:01:00" ],
              ]
            )
            table_scan.createScan()
        print("Caught: " + str(context.exception))
        self.assertTrue("Wait For column must be followed by Value" in str(context.exception))




if __name__ == "__main__":
    unittest.main()

