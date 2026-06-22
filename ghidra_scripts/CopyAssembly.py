# @runtime PyGhidra
# @category XEX Helpers

from java.awt import Toolkit
from java.awt.datatransfer import StringSelection


def format_instruction(instr):
    mnemonic = instr.getMnemonicString()

    operands = []
    for i in range(instr.getNumOperands()):
        op = instr.getDefaultOperandRepresentation(i)
        if op:
            operands.append(str(op))

    if operands:
        return "%-10s %s" % (mnemonic, ",".join(operands))

    return mnemonic


def copy_to_clipboard(text):
    clipboard = Toolkit.getDefaultToolkit().getSystemClipboard()
    clipboard.setContents(StringSelection(text), None)


def main():
    sel = currentSelection

    if sel is None or sel.isEmpty():
        sel = currentHighlight

    if sel is None or sel.isEmpty():
        popup("Select some instructions first.")
    else:
        listing = currentProgram.getListing()
        instrs = listing.getInstructions(sel, True)

        lines = []

        for instr in instrs:
            lines.append(format_instruction(instr))

        output = "\n".join(lines)

        println(output)
        copy_to_clipboard(output)


main()
