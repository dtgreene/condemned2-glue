# @runtime PyGhidra
# @category XEX Helpers

import re

from ghidra.program.model.symbol import SourceType
from ghidra.util.exception import DuplicateNameException, InvalidInputException
from javax.swing import JTextArea, JScrollPane, JOptionPane
from java.awt import Dimension


ENTRY_RE = re.compile(r'^\s*(0x[0-9a-fA-F]+)\s*=\s*\{\s*name\s*=\s*"([^"]+)"\s*\}\s*$')


def capture_text(title="Paste address/name mappings"):
    text_area = JTextArea()
    text_area.setEditable(True)
    text_area.setLineWrap(False)

    scroll = JScrollPane(text_area)
    scroll.setPreferredSize(Dimension(800, 500))

    result = JOptionPane.showConfirmDialog(
        None, scroll, title, JOptionPane.OK_CANCEL_OPTION, JOptionPane.PLAIN_MESSAGE
    )

    if result == JOptionPane.OK_OPTION:
        return text_area.getText()

    return None


def parse_entries(text):
    entries = []

    for line_no, line in enumerate(text.splitlines(), 1):
        line = line.strip()

        if not line:
            continue

        m = ENTRY_RE.match(line)
        if not m:
            print("Skipping unrecognized line %d: %s" % (line_no, line))
            continue

        entries.append((m.group(1), m.group(2)))

    return entries


def has_user_symbol_at(symbol_table, addr):
    symbols = symbol_table.getSymbols(addr)

    for sym in symbols:
        if sym.getSource() == SourceType.USER_DEFINED:
            return True

    return False


def make_fallback_name(name, addr):
    addr_suffix = str(addr).replace(":", "_")
    return "%s_%s" % (name, addr_suffix)


def apply_name(addr, name):
    symbol_table = currentProgram.getSymbolTable()
    function_manager = currentProgram.getFunctionManager()

    if has_user_symbol_at(symbol_table, addr):
        print("SKIP %s: already has user-defined symbol" % addr)
        return False

    func = function_manager.getFunctionAt(addr)

    try:
        if func is not None:
            func.setName(name, SourceType.USER_DEFINED)
            print("RENAMED FUNCTION %s -> %s" % (addr, name))
        else:
            sym = symbol_table.createLabel(addr, name, SourceType.USER_DEFINED)
            sym.setPrimary()
            print("CREATED LABEL %s -> %s" % (addr, name))

        return True

    except DuplicateNameException:
        fallback = make_fallback_name(name, addr)

        if func is not None:
            func.setName(fallback, SourceType.USER_DEFINED)
            print("RENAMED FUNCTION %s -> %s" % (addr, fallback))
        else:
            sym = symbol_table.createLabel(addr, fallback, SourceType.USER_DEFINED)
            sym.setPrimary()
            print("CREATED LABEL %s -> %s" % (addr, fallback))

        return True

    except InvalidInputException as e:
        print("INVALID NAME %s at %s: %s" % (name, addr, e))
        return False

    except Exception as e:
        print("FAILED %s %s: %s" % (addr, name, e))
        return False


def main():
    text = capture_text()

    if text is None:
        return

    if not text.strip():
        return

    entries = parse_entries(text)

    if not entries:
        print("No valid entries found.")
        return

    tx = currentProgram.startTransaction("Apply pasted address labels")
    commit = False

    applied = 0
    skipped_or_failed = 0

    try:
        for addr_text, name in entries:
            if monitor.isCancelled():
                break

            addr = toAddr(addr_text)

            if addr is None:
                print("BAD ADDRESS: %s" % addr_text)
                skipped_or_failed += 1
                continue

            if apply_name(addr, name):
                applied += 1
            else:
                skipped_or_failed += 1

        commit = True

    finally:
        currentProgram.endTransaction(tx, commit)

    print("")
    print("Done.")
    print("Applied: %d" % applied)
    print("Skipped/failed: %d" % skipped_or_failed)


main()
