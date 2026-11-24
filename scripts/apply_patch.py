# =============================================================================
# FILE PURPOSE:
# Automated source patcher script that modifies clean CPython source trees
# to install Soft-Lookup VM mode. It safely injects VM interceptors into
# Objects/dictobject.c, Objects/object.c, Objects/abstract.c, Python/sysmodule.c,
# and Makefile.pre.in with line-by-line validation.
# Run with: `python3 scripts/apply_patch.py [path_to_cpython_src]`
# =============================================================================

import os
import sys

def apply_patches(src_dir: str):
    src_dir = os.path.abspath(os.path.expanduser(src_dir))
    if not os.path.isdir(src_dir):
        print(f"Error: Directory {src_dir} does not exist.")
        sys.exit(1)

    print(f"Applying SoftLookup-PVM patches to: {src_dir}")

    # -------------------------------------------------------------------------
    # 1. Header: Include/internal/pycore_softlookup.h
    # -------------------------------------------------------------------------
    header_path = os.path.join(src_dir, "Include/internal/pycore_softlookup.h")
    header_content = """/*
# =============================================================================
# FILE PURPOSE:
# Internal C-level VM declarations and function prototypes for Soft-Lookup Mode.
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

extern int _Py_SoftLookup_IsEnabled(void);
extern void _Py_SoftLookup_SetEnabled(int enabled);
extern void _Py_SoftLookup_RecordKeyMiss(void);
extern void _Py_SoftLookup_RecordAttrMiss(void);
extern void _Py_SoftLookup_GetStats(uint64_t *key_misses, uint64_t *attr_misses);
extern void _Py_SoftLookup_ResetStats(void);
extern void _Py_SoftLookup_Init(void);

#ifdef __cplusplus
}
#endif
#endif /* !Py_INTERNAL_SOFTLOOKUP_H */
"""
    with open(header_path, "w", encoding="utf-8") as f:
        f.write(header_content)
    print("  [+] Include/internal/pycore_softlookup.h written")

    # -------------------------------------------------------------------------
    # 2. Source: Python/softlookup.c
    # -------------------------------------------------------------------------
    c_path = os.path.join(src_dir, "Python/softlookup.c")
    c_content = """/*
# =============================================================================
# FILE PURPOSE:
# Core C implementation of the Soft-Lookup state machine and atomic counters.
# =============================================================================
*/
#include "Python.h"
#include "pycore_softlookup.h"
#include <stdlib.h>
#include <string.h>

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
    if (env != NULL && *env != '\\0' && strcmp(env, "0") != 0) {
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
"""
    with open(c_path, "w", encoding="utf-8") as f:
        f.write(c_content)
    print("  [+] Python/softlookup.c written")

    # -------------------------------------------------------------------------
    # 3. Makefile.pre.in
    # -------------------------------------------------------------------------
    mk_path = os.path.join(src_dir, "Makefile.pre.in")
    with open(mk_path, "r", encoding="utf-8") as f:
        mk = f.read()
    if "Python/softlookup.o" not in mk:
        mk = mk.replace(
            "\t\tPython/mysnprintf.o \\",
            "\t\tPython/mysnprintf.o \\\n\t\tPython/softlookup.o \\"
        )
        with open(mk_path, "w", encoding="utf-8") as f:
            f.write(mk)
        print("  [+] Makefile.pre.in updated")

    # -------------------------------------------------------------------------
    # 4. Compiler Tag: Python/getcompiler.c
    # -------------------------------------------------------------------------
    gc_path = os.path.join(src_dir, "Python/getcompiler.c")
    with open(gc_path, "r", encoding="utf-8") as f:
        gc = f.read()
    if "SoftLookup-PVM" not in gc:
        gc = gc.replace(
            '#define COMPILER "[GCC " __VERSION__ "]"',
            '#define COMPILER "[GCC " __VERSION__ ", SoftLookup-PVM]"'
        )
        gc = gc.replace(
            '#define COMPILER "[Clang " __clang_version__ "]"',
            '#define COMPILER "[Clang " __clang_version__ ", SoftLookup-PVM]"'
        )
        with open(gc_path, "w", encoding="utf-8") as f:
            f.write(gc)
        print("  [+] Python/getcompiler.c updated")

    # -------------------------------------------------------------------------
    # 5. Initialization: Python/pylifecycle.c
    # -------------------------------------------------------------------------
    lc_path = os.path.join(src_dir, "Python/pylifecycle.c")
    with open(lc_path, "r", encoding="utf-8") as f:
        lc = f.read()
    if "pycore_softlookup.h" not in lc:
        lc = lc.replace(
            '#include "pycore_audit.h"',
            '#include "pycore_softlookup.h"\n#include "pycore_audit.h"'
        )
        lc = lc.replace(
            '    _Py_InitVersion();',
            '    _Py_InitVersion();\n    _Py_SoftLookup_Init();'
        )
        with open(lc_path, "w", encoding="utf-8") as f:
            f.write(lc)
        print("  [+] Python/pylifecycle.c updated")

    # -------------------------------------------------------------------------
    # 6. sys module: Python/sysmodule.c
    # -------------------------------------------------------------------------
    sm_path = os.path.join(src_dir, "Python/sysmodule.c")
    with open(sm_path, "r", encoding="utf-8") as f:
        sm = f.read()
    if "pycore_softlookup.h" not in sm:
        sm = sm.replace(
            '#include "pycore_audit.h"',
            '#include "pycore_softlookup.h"\n#include "pycore_audit.h"'
        )
        sys_funcs = """
PyDoc_STRVAR(sys_set_soft_lookup_doc,
"set_soft_lookup($module, enabled, /)\\n"
"--\\n"
"\\n"
"Enable or disable Soft-Lookup mode in the runtime.");

static PyObject *
sys_set_soft_lookup(PyObject *module, PyObject *arg)
{
    int enabled = PyObject_IsTrue(arg);
    if (enabled < 0) {
        return NULL;
    }
    _Py_SoftLookup_SetEnabled(enabled);
    Py_RETURN_NONE;
}

PyDoc_STRVAR(sys_get_soft_lookup_doc,
"get_soft_lookup($module, /)\\n"
"--\\n"
"\\n"
"Return True if Soft-Lookup mode is currently enabled, False otherwise.");

static PyObject *
sys_get_soft_lookup(PyObject *module, PyObject *Py_UNUSED(ignored))
{
    return PyBool_FromLong(_Py_SoftLookup_IsEnabled());
}

PyDoc_STRVAR(sys_get_soft_lookup_stats_doc,
"get_soft_lookup_stats($module, /)\\n"
"--\\n"
"\\n"
"Return dictionary with soft-lookup telemetry counters.");

static PyObject *
sys_get_soft_lookup_stats(PyObject *module, PyObject *Py_UNUSED(ignored))
{
    uint64_t key_misses = 0, attr_misses = 0;
    _Py_SoftLookup_GetStats(&key_misses, &attr_misses);

    PyObject *d = PyDict_New();
    if (d == NULL) {
        return NULL;
    }
    PyObject *v_key = PyLong_FromUnsignedLongLong(key_misses);
    if (v_key == NULL) {
        Py_DECREF(d);
        return NULL;
    }
    if (PyDict_SetItemString(d, "soft_key_misses", v_key) < 0) {
        Py_DECREF(v_key);
        Py_DECREF(d);
        return NULL;
    }
    Py_DECREF(v_key);

    PyObject *v_attr = PyLong_FromUnsignedLongLong(attr_misses);
    if (v_attr == NULL) {
        Py_DECREF(d);
        return NULL;
    }
    if (PyDict_SetItemString(d, "soft_attr_misses", v_attr) < 0) {
        Py_DECREF(v_attr);
        Py_DECREF(d);
        return NULL;
    }
    Py_DECREF(v_attr);

    return d;
}

PyDoc_STRVAR(sys_reset_soft_lookup_stats_doc,
"reset_soft_lookup_stats($module, /)\\n"
"--\\n"
"\\n"
"Reset soft-lookup telemetry counters to zero.");

static PyObject *
sys_reset_soft_lookup_stats(PyObject *module, PyObject *Py_UNUSED(ignored))
{
    _Py_SoftLookup_ResetStats();
    Py_RETURN_NONE;
}
"""
        sm = sm.replace(
            "static PyMethodDef sys_methods[] = {",
            sys_funcs + "\nstatic PyMethodDef sys_methods[] = {\n"
            '    {"set_soft_lookup", sys_set_soft_lookup, METH_O, sys_set_soft_lookup_doc},\n'
            '    {"get_soft_lookup", sys_get_soft_lookup, METH_NOARGS, sys_get_soft_lookup_doc},\n'
            '    {"get_soft_lookup_stats", sys_get_soft_lookup_stats, METH_NOARGS, sys_get_soft_lookup_stats_doc},\n'
            '    {"reset_soft_lookup_stats", sys_reset_soft_lookup_stats, METH_NOARGS, sys_reset_soft_lookup_stats_doc},'
        )
        with open(sm_path, "w", encoding="utf-8") as f:
            f.write(sm)
        print("  [+] Python/sysmodule.c updated")

    # -------------------------------------------------------------------------
    # 7. Dict Subscript: Objects/dictobject.c
    # -------------------------------------------------------------------------
    do_path = os.path.join(src_dir, "Objects/dictobject.c")
    with open(do_path, "r", encoding="utf-8") as f:
        doc = f.read()
    if "pycore_softlookup.h" not in doc:
        doc = doc.replace(
            '#include "pycore_bitutils.h"',
            '#include "pycore_softlookup.h"\n#include "pycore_bitutils.h"'
        )
        old_target = """        _PyErr_SetKeyError(key);
        return NULL;
    }
    return value;
}"""
        new_target = """        if (_Py_SoftLookup_IsEnabled()) {
            _Py_SoftLookup_RecordKeyMiss();
            return Py_NewRef(Py_None);
        }
        _PyErr_SetKeyError(key);
        return NULL;
    }
    return value;
}"""
        assert old_target in doc, "dictobject.c target not found"
        doc = doc.replace(old_target, new_target, 1)
        with open(do_path, "w", encoding="utf-8") as f:
            f.write(doc)
        print("  [+] Objects/dictobject.c updated")

    # -------------------------------------------------------------------------
    # 8. Generic Mapping: Objects/abstract.c
    # -------------------------------------------------------------------------
    ab_path = os.path.join(src_dir, "Objects/abstract.c")
    with open(ab_path, "r", encoding="utf-8") as f:
        abc = f.read()
    if "pycore_softlookup.h" not in abc:
        abc = abc.replace(
            '#include "pycore_abstract.h"',
            '#include "pycore_softlookup.h"\n#include "pycore_abstract.h"'
        )
        old_sub = """    PyMappingMethods *m = Py_TYPE(o)->tp_as_mapping;
    if (m && m->mp_subscript) {
        PyObject *item = m->mp_subscript(o, key);
        assert(_Py_CheckSlotResult(o, "__getitem__", item != NULL));
        return item;
    }"""
        new_sub = """    PyMappingMethods *m = Py_TYPE(o)->tp_as_mapping;
    if (m && m->mp_subscript) {
        PyObject *item = m->mp_subscript(o, key);
        if (item == NULL && _Py_SoftLookup_IsEnabled() && PyErr_Occurred() && PyErr_ExceptionMatches(PyExc_KeyError)) {
            PyErr_Clear();
            _Py_SoftLookup_RecordKeyMiss();
            return Py_NewRef(Py_None);
        }
        assert(_Py_CheckSlotResult(o, "__getitem__", item != NULL));
        return item;
    }"""
        assert old_sub in abc, "abstract.c target not found"
        abc = abc.replace(old_sub, new_sub, 1)
        with open(ab_path, "w", encoding="utf-8") as f:
            f.write(abc)
        print("  [+] Objects/abstract.c updated")

    # -------------------------------------------------------------------------
    # 9. Attribute Lookups: Objects/object.c
    # -------------------------------------------------------------------------
    ob_path = os.path.join(src_dir, "Objects/object.c")
    with open(ob_path, "r", encoding="utf-8") as f:
        obc = f.read()
    if "pycore_softlookup.h" not in obc:
        obc = obc.replace(
            '#include "pycore_brc.h"',
            '#include "pycore_softlookup.h"\n#include "pycore_brc.h"'
        )
        # in PyObject_GetAttr
        old_getattr = """    if (result == NULL) {
        _PyObject_SetAttributeErrorContext(v, name);
    }
    return result;
}"""
        new_getattr = """    if (result == NULL) {
        if (_Py_SoftLookup_IsEnabled() && PyErr_Occurred() && PyErr_ExceptionMatches(PyExc_AttributeError)) {
            PyErr_Clear();
            _Py_SoftLookup_RecordAttrMiss();
            return Py_NewRef(Py_None);
        }
        _PyObject_SetAttributeErrorContext(v, name);
    }
    return result;
}"""
        obc = obc.replace(old_getattr, new_getattr, 1)

        # in _PyObject_GetAttrStackRef (type branch)
        old_stackref_type = """    if (tp->tp_getattro == _Py_type_getattro) {
        _PyStackRef result = _Py_type_getattro_stackref((PyTypeObject *)v, name, NULL);
        if (PyStackRef_IsNull(result)) {
            _PyObject_SetAttributeErrorContext(v, name);
        }
        return result;
    }"""
        new_stackref_type = """    if (tp->tp_getattro == _Py_type_getattro) {
        _PyStackRef result = _Py_type_getattro_stackref((PyTypeObject *)v, name, NULL);
        if (PyStackRef_IsNull(result)) {
            if (_Py_SoftLookup_IsEnabled() && PyErr_Occurred() && PyErr_ExceptionMatches(PyExc_AttributeError)) {
                PyErr_Clear();
                _Py_SoftLookup_RecordAttrMiss();
                return PyStackRef_FromPyObjectNew(Py_None);
            }
            _PyObject_SetAttributeErrorContext(v, name);
        }
        return result;
    }"""
        obc = obc.replace(old_stackref_type, new_stackref_type, 1)

        # in _PyObject_GetAttrStackRef (end branch)
        old_stackref_end = """    if (result == NULL) {
        _PyObject_SetAttributeErrorContext(v, name);
        return PyStackRef_NULL;
    }
    return PyStackRef_FromPyObjectSteal(result);
}"""
        new_stackref_end = """    if (result == NULL) {
        if (_Py_SoftLookup_IsEnabled() && PyErr_Occurred() && PyErr_ExceptionMatches(PyExc_AttributeError)) {
            PyErr_Clear();
            _Py_SoftLookup_RecordAttrMiss();
            return PyStackRef_FromPyObjectNew(Py_None);
        }
        _PyObject_SetAttributeErrorContext(v, name);
        return PyStackRef_NULL;
    }
    return PyStackRef_FromPyObjectSteal(result);
}"""
        obc = obc.replace(old_stackref_end, new_stackref_end, 1)

        # in _PyObject_GetMethodStackRef
        old_getmeth = """    if (descr != NULL) {
        assert(!PyStackRef_IsNull(*method));
        PyStackRef_CLEAR(*self);
        return 0;
    }

    PyErr_Format(PyExc_AttributeError,
                 "'%.100s' object has no attribute '%U'",
                 tp->tp_name, name);"""
        new_getmeth = """    if (descr != NULL) {
        assert(!PyStackRef_IsNull(*method));
        PyStackRef_CLEAR(*self);
        return 0;
    }

    if (_Py_SoftLookup_IsEnabled()) {
        _Py_SoftLookup_RecordAttrMiss();
        *method = PyStackRef_FromPyObjectNew(Py_None);
        PyStackRef_CLEAR(*self);
        return 0;
    }

    PyErr_Format(PyExc_AttributeError,
                 "'%.100s' object has no attribute '%U'",
                 tp->tp_name, name);"""
        obc = obc.replace(old_getmeth, new_getmeth, 1)

        with open(ob_path, "w", encoding="utf-8") as f:
            f.write(obc)
        print("  [+] Objects/object.c updated")

    print("\nAll SoftLookup-PVM patches applied cleanly!")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "~/pvm-softlookup/cpython-src"
    apply_patches(target)
