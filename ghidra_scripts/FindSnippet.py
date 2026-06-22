# @runtime PyGhidra
# @category XEX Helpers

import re

from javax.swing import (
    JOptionPane,
    JScrollPane,
    JTextArea,
    JPanel,
    JCheckBox,
    JLabel,
    JSpinner,
    SpinnerNumberModel,
    BoxLayout,
)
from java.awt import Dimension, BorderLayout, FlowLayout
from java.util.prefs import Preferences

PREFS = Preferences.userRoot().node("ghidra/find_snippet")

PREF_CAP_ENABLED = "cap_enabled"
PREF_CAP_AMOUNT = "cap_amount"


GPR_RE = re.compile(r"\br([0-9]|[12][0-9]|3[01])\b", re.IGNORECASE)
FPR_RE = re.compile(r"\bf([0-9]|[12][0-9]|3[01])\b", re.IGNORECASE)
HEX_RE = re.compile(r"[-+]?0x[0-9a-fA-F]+")
DEC_RE = re.compile(r"(?<!\w)[-+]?\d+(?!\w)")


class BlockNormalizer(object):
    def __init__(self):
        self.gpr_map = {}
        self.fpr_map = {}
        self.next_gpr = 0
        self.next_fpr = 0

    def map_gpr(self, match):
        reg = match.group(0).lower()

        if reg not in self.gpr_map:
            self.gpr_map[reg] = f"GPR_{len(self.gpr_map)}_"

        return self.gpr_map[reg]

    def map_fpr(self, match):
        reg = match.group(0).lower()

        if reg not in self.fpr_map:
            self.fpr_map[reg] = "F%d" % self.next_fpr
            self.next_fpr += 1

        return self.fpr_map[reg]

    def normalize_parts(self, mnemonic, operands):
        norm_operands = []

        for op in operands:
            op = str(op)

            op = re.sub(r"\bctr\b", "CTR", op, flags=re.IGNORECASE)
            op = re.sub(r"\blr\b", "LR", op, flags=re.IGNORECASE)
            op = re.sub(r"\bxer\b", "XER", op, flags=re.IGNORECASE)

            # Normalize register names first so DEC_RE can't match trailing
            # digits inside a register token (e.g. the second '1' in "r11").
            op = FPR_RE.sub(self.map_fpr, op)
            op = GPR_RE.sub(self.map_gpr, op)

            # Now that registers are gone, normalize immediates and offsets.
            op = HEX_RE.sub("IMM", op)
            op = DEC_RE.sub("IMM", op)

            norm_operands.append(op)

        if norm_operands:
            return "%s %s" % (mnemonic.lower(), ",".join(norm_operands))

        return mnemonic.lower()


def parse_snippet(snippet):
    result = []

    for line in str(snippet).splitlines():
        line = line.strip()

        if line == "":
            continue

        if line.startswith("#"):
            continue

        parts = line.split(None, 1)

        mnemonic = parts[0].lower()
        operands = []

        if len(parts) > 1:
            operands = [
                x.strip().replace(" ", "") for x in parts[1].split(",") if x.strip()
            ]

        result.append((mnemonic, operands))

    return result


def capture_snippet(title="Paste Assembly Snippet"):
    # Load previous values
    saved_cap_enabled = PREFS.getBoolean(PREF_CAP_ENABLED, False)
    saved_cap_amount = PREFS.getInt(PREF_CAP_AMOUNT, 100)

    text_area = JTextArea()
    text_area.setEditable(True)
    text_area.setLineWrap(False)

    scroll = JScrollPane(text_area)
    scroll.setPreferredSize(Dimension(700, 400))

    cap_checkbox = JCheckBox("Cap results?")
    cap_checkbox.setSelected(saved_cap_enabled)

    cap_spinner = JSpinner(SpinnerNumberModel(saved_cap_amount, 1, 1000000, 1))
    cap_spinner.setEnabled(saved_cap_enabled)

    def on_cap_toggle(event):
        cap_spinner.setEnabled(cap_checkbox.isSelected())

    cap_checkbox.addActionListener(on_cap_toggle)

    # First line: checkbox
    checkbox_row = JPanel(FlowLayout(FlowLayout.LEFT))
    checkbox_row.add(cap_checkbox)

    # Second line: cap amount input
    amount_row = JPanel(FlowLayout(FlowLayout.LEFT))
    amount_row.add(JLabel("Max results:"))
    amount_row.add(cap_spinner)

    # Vertical layout, like display:block-ish stacking
    options_panel = JPanel()
    options_panel.setLayout(BoxLayout(options_panel, BoxLayout.Y_AXIS))
    options_panel.add(checkbox_row)
    options_panel.add(amount_row)

    panel = JPanel(BorderLayout())
    panel.add(scroll, BorderLayout.CENTER)
    panel.add(options_panel, BorderLayout.SOUTH)

    result = JOptionPane.showConfirmDialog(
        None, panel, title, JOptionPane.OK_CANCEL_OPTION, JOptionPane.PLAIN_MESSAGE
    )

    if result == JOptionPane.OK_OPTION:
        text = text_area.getText()

        cap_enabled = cap_checkbox.isSelected()
        cap_amount_value = int(cap_spinner.getValue())

        # Save values for next run
        PREFS.putBoolean(PREF_CAP_ENABLED, cap_enabled)
        PREFS.putInt(PREF_CAP_AMOUNT, cap_amount_value)

        if cap_enabled:
            cap_amount = cap_amount_value
        else:
            cap_amount = None

        return text, cap_amount

    return None


def instruction_to_parts(instr):
    mnemonic = instr.getMnemonicString().lower()

    operands = []

    for i in range(instr.getNumOperands()):
        op = instr.getDefaultOperandRepresentation(i)
        if op:
            operands.append(str(op).strip().replace(" ", ""))

    return (mnemonic, operands)


def candidate_matches_at(listing, start_instr, pattern_norm):
    normalizer = BlockNormalizer()

    instr = start_instr

    for pattern_line in pattern_norm:
        if instr is None:
            return None

        mnemonic, operands = instruction_to_parts(instr)
        candidate_line = normalizer.normalize_parts(mnemonic, operands)

        if candidate_line != pattern_line:
            return None

        instr = listing.getInstructionAfter(instr.getMinAddress())

    return True


def normalize_pattern(pattern_parts):
    normalizer = BlockNormalizer()
    result = []

    for mnemonic, operands in pattern_parts:
        result.append(normalizer.normalize_parts(mnemonic, operands))

    return result


def main():
    captured = capture_snippet()

    if captured is None:
        return

    snippet, cap_amount = captured

    if snippet.strip() == "":
        return

    pattern_parts = parse_snippet(snippet)
    pattern_norm = normalize_pattern(pattern_parts)

    if len(pattern_parts) == 0:
        popup("No usable instructions in snippet.")
        return

    println("Normalized pattern:")
    for line in pattern_norm:
        println("  " + line)

    memory = currentProgram.getMemory()
    listing = currentProgram.getListing()

    matches = []
    first_pattern_mnemonic = pattern_parts[0][0].lower()
    instr_iter = listing.getInstructions(memory.getExecuteSet(), True)
    hit_cap = False

    while instr_iter.hasNext() and not monitor.isCancelled():
        i0 = instr_iter.next()

        # Very cheap first filter.
        if i0.getMnemonicString().lower() != first_pattern_mnemonic:
            continue

        if candidate_matches_at(listing, i0, pattern_norm):
            matches.append(i0.getMinAddress())

            if cap_amount is not None and len(matches) >= cap_amount:
                hit_cap = True
                break

            println("")
            println("MATCH at %s" % i0.getMinAddress())

            instr = i0
            for _ in range(len(pattern_norm)):
                println("  %s  %s" % (instr.getMinAddress(), instr.toString()))
                instr = listing.getInstructionAfter(instr.getMinAddress())

    if len(matches) == 0:
        popup("No matches found.")
    else:
        popup(
            "Found %d match(es); %s"
            % (len(matches), "Results cap reached." if hit_cap else "")
        )


main()
