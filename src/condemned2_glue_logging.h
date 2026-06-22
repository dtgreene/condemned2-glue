#pragma once

#include <rex/logging.h>

REXLOG_DEFINE_CATEGORY(c2)

#define C2_TRACE(...)    REXLOG_CAT_TRACE(::rex::log::c2(), __VA_ARGS__)
#define C2_DEBUG(...)    REXLOG_CAT_DEBUG(::rex::log::c2(), __VA_ARGS__)
#define C2_INFO(...)     REXLOG_CAT_INFO(::rex::log::c2(), __VA_ARGS__)
#define C2_WARN(...)     REXLOG_CAT_WARN(::rex::log::c2(), __VA_ARGS__)
#define C2_ERROR(...)    REXLOG_CAT_ERROR(::rex::log::c2(), __VA_ARGS__)
#define C2_CRITICAL(...) REXLOG_CAT_CRITICAL(::rex::log::c2(), __VA_ARGS__)
