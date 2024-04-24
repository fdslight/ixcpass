#define  PY_SSIZE_T_CLEAN
#define  PY_SSIZE_T_CLEAN

#include<Python.h>
#include<structmember.h>
#include<execinfo.h>
#include<signal.h>
#include<sys/types.h>
#include<sys/socket.h>
#include<netinet/in.h>
#include<arpa/inet.h>

#include "../../../pywind/clib/netif/tuntap.h"

typedef struct{
    PyObject_HEAD
}proxy_object;


static void
proxy_dealloc(proxy_object *self)
{
}

static PyObject *
proxy_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    proxy_object *self;
    self=(proxy_object *)type->tp_alloc(type,0);
    if(NULL==self) return NULL;

    return (PyObject *)self;
}

static int
proxy_init(proxy_object *self,PyObject *args,PyObject *kwds)
{
    return 0;
}

/// 打开tun设备
static PyObject *
proxy_tap_open(PyObject *self,PyObject *args)
{
    const char *name;
    char new_name[512];
    int fd;

    if(!PyArg_ParseTuple(args,"s",&name)) return NULL;
    
    strcpy(new_name,name);

    fd=tapdev_create(new_name);
    if(fd<0){
        return PyLong_FromLong(fd);
    }

    tapdev_up(name);
    tapdev_set_nonblocking(fd);

    return PyLong_FromLong(fd);
}

/// 关闭tun设备
static PyObject *
proxy_tap_close(PyObject *self,PyObject *args)
{
    const char *name;
    int fd;

    if(!PyArg_ParseTuple(args,"is",&fd,&name)) return NULL;

    tapdev_close(fd,name);

    Py_RETURN_NONE;
}


static PyMemberDef proxy_members[]={
    {NULL}
};

static PyMethodDef proxy_methods[]={

    {"tap_open",(PyCFunction)proxy_tap_open,METH_VARARGS,"open tap device"},
    {"tap_close",(PyCFunction)proxy_tap_close,METH_VARARGS,"close tap device"},
    
    {NULL,NULL,0,NULL}
};

static PyTypeObject proxy_type={
    PyVarObject_HEAD_INIT(NULL,0)
    .tp_name="proxy.proxy",
    .tp_doc="python proxy helper library",
    .tp_basicsize=sizeof(proxy_object),
    .tp_itemsize=0,
    .tp_flags=Py_TPFLAGS_DEFAULT,
    .tp_new=proxy_new,
    .tp_init=(initproc)proxy_init,
    .tp_dealloc=(destructor)proxy_dealloc,
    .tp_members=proxy_members,
    .tp_methods=proxy_methods
};

static struct PyModuleDef proxy_module={
    PyModuleDef_HEAD_INIT,
    "proxy",
    NULL,
    -1,
    proxy_methods
};

PyMODINIT_FUNC
PyInit_proxy(void){
    PyObject *m;

    m=PyModule_Create(&proxy_module);
    if(NULL==m) return NULL;

    Py_INCREF(&proxy_type);
    if(PyModule_AddObject(m,"proxy",(PyObject *)&proxy_type)<0){
        Py_DECREF(&proxy_type);
        Py_DECREF(m);
        return NULL;
    }
    
    return m;
}