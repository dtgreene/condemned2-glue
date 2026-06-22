#include <rex/hook.h>

#include "condemned2_glue_logging.h"

void EnableCheats(PPCRegister& r3) {
	r3.u32 = 0;
}

void RetailCheck(PPCRegister& r3) {
	r3.u32 = 1;
}


static std::string ResolveFmt(const char* fmt, uint8_t* membase,
	const PPCRegister* const args[], int nargs) {
	std::string result;
	result.reserve(128);
	int arg_idx = 0;

	for (const char* p = fmt; *p;) {
		if (*p == '\n' || *p == '\r') { p++; continue; }
		if (*p != '%') { result += *p++; continue; }

		const char* spec_start = p++;
		if (*p == '%') { result += '%'; p++; continue; }

		while (*p && std::strchr("-+ #0", *p)) p++;
		while (*p && std::isdigit((unsigned char)*p)) p++;

		if (*p == '.') { p++; while (*p && std::isdigit((unsigned char)*p)) p++; }

		const char type = *p ? *p++ : '\0';
		if (!type || arg_idx >= nargs) continue;

		std::string spec(spec_start, p);
		const PPCRegister& reg = *args[arg_idx++];
		char buf[128];

		switch (type) {
		case 'd':
		case 'i': {
			std::snprintf(buf, sizeof(buf), spec.c_str(), (int32_t)reg.u32);
			result += buf;
			break;
		}
		case 'u':
		case 'o': {
			std::snprintf(buf, sizeof(buf), spec.c_str(), reg.u32);
			result += buf;
			break;
		}
		case 'x':
		case 'X': {
			std::snprintf(buf, sizeof(buf), spec.c_str(), reg.u32);
			result += buf;
			break;
		}
		case 'p': {
			std::snprintf(buf, sizeof(buf), spec.c_str(), (void*)(uintptr_t)reg.u32);
			result += buf;
			break;
		}
		case 's': {
			if (reg.u32) {
				result += reinterpret_cast<const char*>(membase + reg.u32);
			}
			else {
				result += "(null)";
			}
			break;
		}
				// Skipping floats for now
		default: {
			result += spec;
			break;
		}
		}
	}

	const auto start = result.find_first_not_of(' ');
	return start != std::string::npos ? result.substr(start) : std::string{};
}

static void StubbedLogger(std::string_view prefix, const PPCRegister& fmtReg, const PPCRegister* const args[], int argCount) {
	const uint32_t fmtAddr = fmtReg.u32;
	if (!fmtAddr)
		return;

	auto* ks = rex::system::kernel_state();
	if (!ks || !ks->memory())
		return;

	auto* membase = ks->memory()->virtual_membase();
	if (!membase)
		return;

	static std::unordered_set<uint32_t> seen;
	if (!seen.insert(fmtAddr).second)
		return;

	const char* fmt = reinterpret_cast<const char*>(membase + fmtAddr);
	const std::string resolved = ResolveFmt(fmt, membase, args, argCount);

	C2_INFO("{}: [{:#x}] \"{}\"", prefix, fmtAddr, resolved);
}

void StubbedLogger1(
	PPCRegister& r4, PPCRegister& r5,
	PPCRegister& r6, PPCRegister& r7, PPCRegister& r8,
	PPCRegister& r9, PPCRegister& r10) {

	// r4 is format
	const PPCRegister* args[] = {
		&r5, &r6, &r7, &r8, &r9, &r10,
	};

	StubbedLogger("StubbedLogger1", r4, args, static_cast<int>(std::size(args)));
}

void StubbedLogger2(
	PPCRegister& r3, PPCRegister& r4, PPCRegister& r5,
	PPCRegister& r6, PPCRegister& r7, PPCRegister& r8,
	PPCRegister& r9, PPCRegister& r10) {

	// r3 is format
	const PPCRegister* args[] = {
		&r4, &r5, &r6, &r7, &r8, &r9, &r10,
	};

	StubbedLogger("StubbedLogger2", r3, args, static_cast<int>(std::size(args)));
}

//REX_EXTERN(__imp__D3DDevice_EndTiling);
//
//REX_HOOK_RAW(D3DDevice_EndTiling) {
//	ctx.r3.u32;
//
//	__imp__D3DDevice_EndTiling(ctx, base);
//
//	// Post-hook: inspect or modify state after
//}