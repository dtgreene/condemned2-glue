# Some Xbox 360 functions begin by moving LR into r12 and calling a compiler
# helper such as __savegprlr_*. Ghidra may mark those helper calls as
# CALL_RETURN / no-fallthrough, which prevents disassembly from continuing
# into the actual function body. This script scans for that prologue shape
# and explicitly disassembles the instruction immediately after the
# branch-and-link.

# @category Analysis
# @runtime PyGhidra


from ghidra.app.cmd.disassemble import DisassembleCommand

listing = currentProgram.getListing()
memory = currentProgram.getMemory()


def op_text(inst, idx):
    return inst.getDefaultOperandRepresentation(idx).replace(" ", "").lower()


def is_move(inst):
    if inst is None:
        return False

    mnem = inst.getMnemonicString().lower()

    if mnem == "mfspr":
        return op_text(inst, 0) == "r12" and op_text(inst, 1) == "lr"
    if mnem == "mflr":
        return op_text(inst, 0) == "r12"

    return False


def is_bl(inst):
    return inst is not None and inst.getMnemonicString().lower() == "bl"


def run_disasm(addr):
    if addr is None or memory.getBlock(addr) is None:
        return False
    if listing.getInstructionAt(addr) is not None:
        return True

    cmd = DisassembleCommand(addr, None, True)
    ok = cmd.applyTo(currentProgram, monitor)

    if not ok:
        println("Disassemble failed at %s: %s" % (addr, cmd.getStatusMsg()))

    return ok


def main():
    seen = 0
    disassembled = 0
    instr_iter = listing.getInstructions(memory.getExecuteSet(), True)

    while instr_iter.hasNext() and not monitor.isCancelled():
        i0 = instr_iter.next()

        if not is_move(i0):
            continue

        i1 = listing.getInstructionAt(i0.getAddress().add(i0.getLength()))

        if not is_bl(i1):
            continue

        seen += 1
        fallthrough = i1.getAddress().add(i1.getLength())

        if run_disasm(fallthrough):
            disassembled += 1

    println("Xbox 360 PPC prologue scan complete.")
    println("mfspr r12,LR + bl patterns seen: %d" % seen)
    println("fallthrough disassembly attempted/succeeded: %d" % disassembled)


main()
