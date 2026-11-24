/*
# =============================================================================
# FILE PURPOSE:
# Header file defining internal C-level VM declarations and function prototypes
# for CPython Soft-Lookup Mode. This file exposes runtime toggle switches, telemetry
# counter accessors, and initialization routines linked directly into Python's core.
# It is compiled into CPython via Include/internal/pycore_softlookup.h.
# =============================================================================
*/

#ifndef Py_INTERNAL_SOFTLOOKUP_H
#define Py_INTERNAL_SOFTLOOKUP_H
#ifdef __cplusplus
extern "C" {
#endif

#ifndef Py_BUILD_CORE
#  error "this header requires Py_BUILD_CORE define"
#endif

#include <stdint.h>

/*
 * C-level API for Python Soft-Lookup Mode
 */

/* Returns 1 if Soft-Lookup mode is active, 0 otherwise */
extern int _Py_SoftLookup_IsEnabled(void);

/* Enables (enabled != 0) or disables (enabled == 0) Soft-Lookup mode */
extern void _Py_SoftLookup_SetEnabled(int enabled);

/* Telemetry counters */
extern void _Py_SoftLookup_RecordKeyMiss(void);
extern void _Py_SoftLookup_RecordAttrMiss(void);
extern void _Py_SoftLookup_GetStats(uint64_t *key_misses, uint64_t *attr_misses);
extern void _Py_SoftLookup_ResetStats(void);

/* One-time initialization checking environment variable PVM_SOFT_LOOKUP */
extern void _Py_SoftLookup_Init(void);

#ifdef __cplusplus
}
#endif
#endif /* !Py_INTERNAL_SOFTLOOKUP_H */
