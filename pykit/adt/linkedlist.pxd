cdef class LinkableItem(object):
    cdef public data, _prev, _next

cdef class LinkedList(object):
    cdef public _head, _tail, size
