# Architectural Comparison: Upstream CPython vs. SoftLookup-PVM

This document provides a side-by-side breakdown of the CPython virtual machine before and after the **SoftLookup-PVM** modification.

---

## 1. Executive Summary of Changes

| Subsystem | Upstream CPython (Standard) | SoftLookup-PVM (Flavor #4) |
| :--- | :--- | :--- |
| **Missing Dictionary Key** | Sets `KeyError` exception object and returns `NULL`. | If `soft_lookup` enabled: increments `soft_key_misses`, returns `Py_NewRef(Py_None)`. |
| **Missing Generic Mapping Key** | Propagates `KeyError` from `mp_subscript` slot. | If `soft_lookup` enabled: clears `KeyError`, increments `soft_key_misses`, returns `Py_None`. |
| **Missing Object Attribute** | Sets `AttributeError` exception object and returns `NULL`. | If `soft_lookup` enabled: clears `AttributeError`, increments `soft_attr_misses`, returns `Py_None`. |
| **Attribute Bytecode StackRef** | Raises error and fails `_LOAD_ATTR` instruction. | Returns `PyStackRef_FromPyObjectNew(Py_None)` cleanly with balanced reference counts. |
| **Telemetry & Observability** | No telemetry; lookup misses only measurable via exceptions. | High-performance C counters exposed via `sys.get_soft_lookup_stats()`. |
| **Runtime Control** | No runtime toggle. Always strict. | Opt-in runtime toggle via `sys.set_soft_lookup(bool)` & `PVM_SOFT_LOOKUP=1`. |

---

## 2. Side-by-Side Code Diffs

### A. Dictionary Subscript Lookup (`Objects/dictobject.c`)

When evaluating expressions like `dict_obj[key]`, CPython resolves the key using `_PyDict_SubscriptKnownHash`.

```c
/* ============================================================================
 * LOCATION: Objects/dictobject.c -> _PyDict_SubscriptKnownHash()
 * ============================================================================ */

/* ----------------------------------------------------------------------------
 * UPSTREAM CPYTHON (ORIGINAL)
 * ---------------------------------------------------------------------------- */
PyObject *
_PyDict_SubscriptKnownHash(PyObject *self, PyObject *key, Py_hash_t hash)
{
    PyDictObject *mp = (PyDictObject *)self;
    Py_ssize_t ix;
    PyObject *value;

    ix = _Py_dict_lookup_threadsafe(mp, key, hash, &value);
    if (ix == DKIX_ERROR)
        return NULL;
    if (ix == DKIX_EMPTY || value == NULL) {
        if (!PyAnyDict_CheckExact(mp)) {
            /* Look up __missing__ method if we're a subclass. */
            PyObject *missing, *res;
            missing = _PyObject_LookupSpecial(
                    (PyObject *)mp, &_Py_ID(__missing__));
            if (missing != NULL) {
                res = PyObject_CallOneArg(missing, key);
                Py_DECREF(missing);
                return res;
            }
            else if (PyErr_Occurred())
                return NULL;
        }
        _PyErr_SetKeyError(key);
        return NULL;
    }
    return value;
}

/* ----------------------------------------------------------------------------
 * SOFTLOOKUP-PVM (UPGRADED)
 * ---------------------------------------------------------------------------- */
PyObject *
_PyDict_SubscriptKnownHash(PyObject *self, PyObject *key, Py_hash_t hash)
{
    PyDictObject *mp = (PyDictObject *)self;
    Py_ssize_t ix;
    PyObject *value;

    ix = _Py_dict_lookup_threadsafe(mp, key, hash, &value);
    if (ix == DKIX_ERROR)
        return NULL;
    if (ix == DKIX_EMPTY || value == NULL) {
        if (!PyAnyDict_CheckExact(mp)) {
            /* Look up __missing__ method if we're a subclass. */
            PyObject *missing, *res;
            missing = _PyObject_LookupSpecial(
                    (PyObject *)mp, &_Py_ID(__missing__));
            if (missing != NULL) {
                res = PyObject_CallOneArg(missing, key);
                Py_DECREF(missing);
                return res;
            }
            else if (PyErr_Occurred())
                return NULL;
        }
        /* >>> SOFTLOOKUP-PVM INTERCEPTOR <<< */
        if (_Py_SoftLookup_IsEnabled()) {
            _Py_SoftLookup_RecordKeyMiss();
            return Py_NewRef(Py_None);
        }
        /* >>> END INTERCEPTOR <<< */
        _PyErr_SetKeyError(key);
        return NULL;
    }
    return value;
}
```

#### Line-by-Line Architectural Explanation:
1. **Subclass Hook Preserved**: Subclasses implementing `__missing__` (like `collections.defaultdict`) continue to execute their custom handler first.
2. **Atomic Telemetry**: `_Py_SoftLookup_RecordKeyMiss()` atomically increments a 64-bit integer, providing microsecond-level telemetry without locks.
3. **Reference Counting Safety**: `Py_NewRef(Py_None)` increments the reference count of the singleton `Py_None`. When the calling opcode (e.g. `_BINARY_OP_SUBSCR_DICT`) consumes it with `PyStackRef_FromPyObjectSteal(res_o)`, reference ownership transfers cleanly onto the VM stack without memory leaks.

---

### B. Generic Mapping Protocol Subscript (`Objects/abstract.c`)

For user-defined mappings or objects implementing `__getitem__`, lookups route through `PyObject_GetItem`.

```c
/* ============================================================================
 * LOCATION: Objects/abstract.c -> PyObject_GetItem()
 * ============================================================================ */

/* ----------------------------------------------------------------------------
 * UPSTREAM CPYTHON (ORIGINAL)
 * ---------------------------------------------------------------------------- */
PyObject *
PyObject_GetItem(PyObject *o, PyObject *key)
{
    if (o == NULL || key == NULL) {
        return null_error();
    }

    PyMappingMethods *m = Py_TYPE(o)->tp_as_mapping;
    if (m && m->mp_subscript) {
        PyObject *item = m->mp_subscript(o, key);
        assert(_Py_CheckSlotResult(o, "__getitem__", item != NULL));
        return item;
    }
    /* ... Sequence and class subscription logic ... */
}

/* ----------------------------------------------------------------------------
 * SOFTLOOKUP-PVM (UPGRADED)
 * ---------------------------------------------------------------------------- */
PyObject *
PyObject_GetItem(PyObject *o, PyObject *key)
{
    if (o == NULL || key == NULL) {
        return null_error();
    }

    PyMappingMethods *m = Py_TYPE(o)->tp_as_mapping;
    if (m && m->mp_subscript) {
        PyObject *item = m->mp_subscript(o, key);
        /* >>> SOFTLOOKUP-PVM INTERCEPTOR <<< */
        if (item == NULL && _Py_SoftLookup_IsEnabled() && PyErr_Occurred() && PyErr_ExceptionMatches(PyExc_KeyError)) {
            PyErr_Clear();
            _Py_SoftLookup_RecordKeyMiss();
            return Py_NewRef(Py_None);
        }
        /* >>> END INTERCEPTOR <<< */
        assert(_Py_CheckSlotResult(o, "__getitem__", item != NULL));
        return item;
    }
    /* ... Sequence and class subscription logic ... */
}
```

#### Line-by-Line Architectural Explanation:
1. **Specific Exception Discrimination**: `PyErr_ExceptionMatches(PyExc_KeyError)` strictly checks whether the raised exception is a `KeyError`. Other exceptions—such as `TypeError` (e.g., passing a list as a dict key) or `RuntimeError`—are preserved untouched.
2. **Exception Clearing**: Calling `PyErr_Clear()` resets the thread state error indicator, converting an exceptional return into a successful return of `Py_None`.
3. **Debug Assertion Safety**: The interceptor executes *before* `assert(_Py_CheckSlotResult(o, "__getitem__", item != NULL))`, ensuring debug builds of Python remain 100% assertion-clean.

---

### C. Attribute Lookup Protocol (`Objects/object.c`)

When dereferencing an object attribute via `obj.attr` or `getattr(obj, "attr")`:

```c
/* ============================================================================
 * LOCATION: Objects/object.c -> PyObject_GetAttr() & _PyObject_GetAttrStackRef()
 * ============================================================================ */

/* ----------------------------------------------------------------------------
 * UPSTREAM CPYTHON (ORIGINAL)
 * ---------------------------------------------------------------------------- */
PyObject *
PyObject_GetAttr(PyObject *v, PyObject *name)
{
    /* ... Type getattro / getattr resolution ... */
    if (result == NULL) {
        _PyObject_SetAttributeErrorContext(v, name);
    }
    return result;
}

_PyStackRef
_PyObject_GetAttrStackRef(PyObject *v, PyObject *name)
{
    /* ... Type fast path ... */
    if (result == NULL) {
        _PyObject_SetAttributeErrorContext(v, name);
        return PyStackRef_NULL;
    }
    return PyStackRef_FromPyObjectSteal(result);
}

/* ----------------------------------------------------------------------------
 * SOFTLOOKUP-PVM (UPGRADED)
 * ---------------------------------------------------------------------------- */
PyObject *
PyObject_GetAttr(PyObject *v, PyObject *name)
{
    /* ... Type getattro / getattr resolution ... */
    if (result == NULL) {
        /* >>> SOFTLOOKUP-PVM INTERCEPTOR <<< */
        if (_Py_SoftLookup_IsEnabled() && PyErr_Occurred() && PyErr_ExceptionMatches(PyExc_AttributeError)) {
            PyErr_Clear();
            _Py_SoftLookup_RecordAttrMiss();
            return Py_NewRef(Py_None);
        }
        /* >>> END INTERCEPTOR <<< */
        _PyObject_SetAttributeErrorContext(v, name);
    }
    return result;
}

_PyStackRef
_PyObject_GetAttrStackRef(PyObject *v, PyObject *name)
{
    /* ... Type fast path ... */
    if (result == NULL) {
        /* >>> SOFTLOOKUP-PVM INTERCEPTOR <<< */
        if (_Py_SoftLookup_IsEnabled() && PyErr_Occurred() && PyErr_ExceptionMatches(PyExc_AttributeError)) {
            PyErr_Clear();
            _Py_SoftLookup_RecordAttrMiss();
            return PyStackRef_FromPyObjectNew(Py_None);
        }
        /* >>> END INTERCEPTOR <<< */
        _PyObject_SetAttributeErrorContext(v, name);
        return PyStackRef_NULL;
    }
    return PyStackRef_FromPyObjectSteal(result);
}
```

#### Line-by-Line Architectural Explanation:
1. **Dual Path Coverage**:
   - `PyObject_GetAttr` covers C-API calls and `getattr(obj, "attr")`.
   - `_PyObject_GetAttrStackRef` covers the hot Python 3.14+ bytecode opcode `_LOAD_ATTR` (`!(oparg & 1)`).
2. **StackRef Integration**: Python 3.14 utilizes `_PyStackRef` references for bytecode evaluation. Returning `PyStackRef_FromPyObjectNew(Py_None)` creates a valid stack reference, allowing `_LOAD_ATTR` to pop the owner from the evaluation stack and push `None` without triggering bytecode deoptimization.

---

## 3. Behavioral Truth Table

| Operation | Standard Python | SoftLookup-PVM (`soft_lookup=False`) | SoftLookup-PVM (`soft_lookup=True`) |
| :--- | :--- | :--- | :--- |
| `dict["present"]` | Value | Value | Value |
| `dict["missing"]` | ❌ `KeyError` | ❌ `KeyError` | 🟢 `None` (key miss incremented) |
| `dict[{}]` (unhashable) | ❌ `TypeError` | ❌ `TypeError` | ❌ `TypeError` (NOT swallowed) |
| `obj.present` | Value | Value | Value |
| `obj.missing` | ❌ `AttributeError` | ❌ `AttributeError` | 🟢 `None` (attr miss incremented) |
| `list[99]` (out of bounds) | ❌ `IndexError` | ❌ `IndexError` | ❌ `IndexError` (NOT swallowed) |
| `hasattr(obj, "missing")` | `False` | `False` | `False` (intact via `GetOptionalAttr`) |
| `getattr(obj, "missing", 42)` | `42` | `42` | `42` (intact default value) |
