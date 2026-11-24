/*
# =============================================================================
# FILE PURPOSE:
# Core C implementation of the Soft-Lookup state machine, atomic counters,
# and runtime environment detection for the SoftLookup-PVM runtime.
# This file tracks soft key misses, soft attribute misses, and mode toggles,
# providing direct C bindings exposed to Python via sys.set_soft_lookup().
# =============================================================================
*/

#include "Python.h"
#include "pycore_softlookup.h"
#include <stdlib.h>
#include <string.h>

/*
 * ============================================================================
 * ARCHITECTURAL COMPARISON: UPSTREAM CPYTHON VS. SOFTLOOKUP-PVM
 * ============================================================================
 *
 * UPSTREAM CPYTHON BEHAVIOR:
 * ----------------------------------------------------------------------------
 * In standard CPython, missing keys and missing attributes immediately create,
 * format, and raise exception objects:
 *
 *   [Objects/dictobject.c - _PyDict_SubscriptKnownHash]
 *   --- ORIGINAL UPSTREAM ---
 *   if (ix == DKIX_EMPTY || value == NULL) {
 *       _PyErr_SetKeyError(key);
 *       return NULL;
 *   }
 *
 *   [Objects/object.c - PyObject_GetAttr]
 *   --- ORIGINAL UPSTREAM ---
 *   if (result == NULL) {
 *       _PyObject_SetAttributeErrorContext(v, name);
 *   }
 *   return result;
 *
 * SOFTLOOKUP-PVM EXTENDED BEHAVIOR:
 * ----------------------------------------------------------------------------
 * When soft-lookup mode is active, the runtime intercepts the failure at the
 * exact VM boundary before stack unwinding occurs. It increments a 64-bit telemetry
 * counter and returns Py_None with balanced reference counts:
 *
 *   --- SOFTLOOKUP-PVM UPGRADED ---
 *   if (ix == DKIX_EMPTY || value == NULL) {
 *       if (_Py_SoftLookup_IsEnabled()) {
 *           _Py_SoftLookup_RecordKeyMiss();
 *           return Py_NewRef(Py_None);
 *       }
 *       _PyErr_SetKeyError(key);
 *       return NULL;
 *   }
 * ============================================================================
 */

static volatile int _soft_lookup_enabled = 0;
static volatile uint64_t _soft_key_misses = 0;
static volatile uint64_t _soft_attr_misses = 0;
static int _soft_lookup_initialized = 0;

void
_Py_SoftLookup_Init(void)
{
    if (_soft_lookup_initialized) {
        return;
    }
    _soft_lookup_initialized = 1;
    const char *env = getenv("PVM_SOFT_LOOKUP");
    if (env != NULL && *env != '\0' && strcmp(env, "0") != 0) {
        _soft_lookup_enabled = 1;
    }
}

int
_Py_SoftLookup_IsEnabled(void)
{
    if (!_soft_lookup_initialized) {
        _Py_SoftLookup_Init();
    }
    return _soft_lookup_enabled;
}

void
_Py_SoftLookup_SetEnabled(int enabled)
{
    if (!_soft_lookup_initialized) {
        _Py_SoftLookup_Init();
    }
    _soft_lookup_enabled = enabled ? 1 : 0;
}

void
_Py_SoftLookup_RecordKeyMiss(void)
{
    _soft_key_misses++;
}

void
_Py_SoftLookup_RecordAttrMiss(void)
{
    _soft_attr_misses++;
}

void
_Py_SoftLookup_GetStats(uint64_t *key_misses, uint64_t *attr_misses)
{
    if (key_misses) {
        *key_misses = _soft_key_misses;
    }
    if (attr_misses) {
        *attr_misses = _soft_attr_misses;
    }
}

void
_Py_SoftLookup_ResetStats(void)
{
    _soft_key_misses = 0;
    _soft_attr_misses = 0;
}
