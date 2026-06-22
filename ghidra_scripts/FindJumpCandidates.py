# @runtime PyGhidra
# @category XEX Helpers

from collections import defaultdict

from ghidra.program.model.mem import MemoryAccessException


MAX_RESULTS = 10


def ppc_dmem_mask(opcode: int, reg: int, xo: bool = False):
    value = ((opcode << 26) | (reg << 16)) & 0xFFFFFFFF
    mask = 0xFC1F0000 | (0x00000003 if xo else 0)
    return mask & 0xFFFFFFFF, value


def read_u32(program, addr):
    # Uses the program language endianness.
    # For Xbox 360 XEX PPC, this should be big-endian.
    return int(program.getMemory().getInt(addr)) & 0xFFFFFFFF


def scan_executable_words(program, monitor):
    memory = program.getMemory()

    # setjmp: saves to r3
    STFD_MASK, STFD_VALUE = ppc_dmem_mask(54, 3)  # stfd fX, d(r3)
    STD_MASK, STD_VALUE = ppc_dmem_mask(62, 3, True)  # std  rX, d(r3)

    # longjmp: jmp_buf starts in r3, but may be copied to scratch first
    LJ_REGS = [3, 7]
    LFD_PATTERNS = [ppc_dmem_mask(50, r) for r in LJ_REGS]  # lfd fX, d(rN)
    LD_PATTERNS = [ppc_dmem_mask(58, r, True) for r in LJ_REGS]  # ld  rX, d(rN)

    for block in memory.getBlocks():
        monitor.checkCancelled()

        if not block.isExecute():
            continue

        if not block.isInitialized():
            continue

        start = block.getStart()
        length = int(block.getSize()) & ~3

        if length < 4:
            continue

        off = 0
        while off < length:
            monitor.checkCancelled()

            addr = start.add(off)

            try:
                w = read_u32(program, addr)
            except MemoryAccessException:
                off += 4
                continue

            va = int(addr.getOffset())

            if (w & STFD_MASK) == STFD_VALUE:
                yield va, "stfd"

            elif (w & STD_MASK) == STD_VALUE:
                yield va, "std"

            else:
                matched = False

                for mask, value in LFD_PATTERNS:
                    if (w & mask) == value:
                        yield va, "lfd"
                        matched = True
                        break

                if not matched:
                    for mask, value in LD_PATTERNS:
                        if (w & mask) == value:
                            yield va, "ld"
                            break

            off += 4


def cluster(sorted_addrs, max_gap=256):
    if not sorted_addrs:
        return []

    clusters = []

    run_start = sorted_addrs[0]
    run_count = 1
    prev = sorted_addrs[0]

    for a in sorted_addrs[1:]:
        if a - prev <= max_gap:
            run_count += 1
        else:
            clusters.append((run_start, run_count, prev - run_start))
            run_start = a
            run_count = 1

        prev = a

    clusters.append((run_start, run_count, prev - run_start))
    return clusters


def nearest(target, clusters, within=600):
    best = None

    for a, c in clusters:
        if abs(a - target) <= within:
            if best is None or abs(a - target) < abs(best[0] - target):
                best = (a, c)

    return best


def addr_str(addr: int):
    return f"0x{addr:x}"


def build_report(program, monitor):
    by_kind = defaultdict(list)

    for va, kind in scan_executable_words(program, monitor):
        by_kind[kind].append(va)

    for kind in by_kind:
        by_kind[kind].sort()

    MAX_SPAN = 384

    std_clusters = [
        (a, c) for a, c, s in cluster(by_kind["std"]) if c >= 8 and s <= MAX_SPAN
    ]

    stfd_clusters = [
        (a, c) for a, c, s in cluster(by_kind["stfd"]) if c >= 8 and s <= MAX_SPAN
    ]

    ld_clusters = [
        (a, c) for a, c, s in cluster(by_kind["ld"]) if c >= 6 and s <= MAX_SPAN
    ]

    lfd_clusters = [
        (a, c) for a, c, s in cluster(by_kind["lfd"]) if c >= 6 and s <= MAX_SPAN
    ]

    lines = []
    lines.append("XEX: Raw Byte Scan")
    lines.append("=" * 40)
    lines.append("")

    lines.append(f"setjmp candidates: {len(std_clusters)} found")

    if std_clusters:
        for addr, std_cnt in sorted(std_clusters, key=lambda x: x[1], reverse=True)[
            :MAX_RESULTS
        ]:
            nb = nearest(addr, stfd_clusters)

            if nb:
                lines.append(
                    f"  {addr_str(addr)}  stdx{std_cnt}  "
                    f"+stfdx{nb[1]} @ {addr_str(nb[0])}"
                )
            else:
                lines.append(f"  {addr_str(addr)}  stdx{std_cnt}")
    else:
        lines.append("  None.")

    lines.append("")
    lines.append(f"longjmp candidates: {len(ld_clusters)} found")

    if ld_clusters:
        for addr, ld_cnt in sorted(ld_clusters, key=lambda x: x[1], reverse=True)[
            :MAX_RESULTS
        ]:
            nb = nearest(addr, lfd_clusters)

            if nb:
                lines.append(
                    f"  {addr_str(addr)}  ldx{ld_cnt}  +lfdx{nb[1]} @ {addr_str(nb[0])}"
                )
            else:
                lines.append(f"  {addr_str(addr)}  ldx{ld_cnt}")
    else:
        lines.append("  None.")

    lines.append("")
    lines.append(
        f"Raw scan done - {len(std_clusters)} setjmp, {len(ld_clusters)} longjmp"
    )

    lines.append(
        "Total hits: "
        f"std={len(by_kind['std'])}, "
        f"stfd={len(by_kind['stfd'])}, "
        f"ld={len(by_kind['ld'])}, "
        f"lfd={len(by_kind['lfd'])}"
    )

    return "\n".join(lines)


report = build_report(currentProgram, monitor)

# Console copy, useful if the popup is small.
print(report)

# GUI dialog in normal Ghidra; log output in headless.
popup(report)
