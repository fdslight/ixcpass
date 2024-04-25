#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <fcntl.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <linux/if.h>
#include <linux/if_tun.h>
#include <errno.h>
#include <net/route.h>
#include <sys/ioctl.h>
#include<sys/socket.h>
#include<string.h>
#include<sys/ioctl.h>
#include<netinet/in.h>
#include<structmember.h>

#include "../../../pywind/clib/netif/tuntap.h"

static PyObject *
tap_open(PyObject *self,PyObject *args)
{
	const char *dev_name;
	char my_name[256];
	int rs;
	if(!PyArg_ParseTuple(args,"s",&dev_name)) return NULL;
	
	strcpy(my_name,dev_name);

	rs=tapdev_create(my_name);
	if(rs>=0){
		tapdev_set_nonblocking(rs);
		tapdev_up(my_name);
	}

	return PyLong_FromLong(rs);
}


static PyObject *
tap_close(PyObject *self, PyObject *args)
{
	int fd;

	if (!PyArg_ParseTuple(args, "i", &fd))
		return NULL;

	close(fd);

	Py_RETURN_NONE;
}

static PyMethodDef UtilsMethods[] = {
	{"tap_open",(PyCFunction)tap_open,METH_VARARGS,"open tap device"},
	{"tap_close",(PyCFunction)tap_close,METH_VARARGS,"close tap device"},

	{NULL,NULL,0,NULL}
};

static struct PyModuleDef utilsmodule = {
	PyModuleDef_HEAD_INIT,
	"pytap",
	NULL,
	-1,
	UtilsMethods
};


PyMODINIT_FUNC
PyInit_pytap(void)
{
	PyObject *m;

	m = PyModule_Create(&utilsmodule);

	if (NULL == m) return NULL;

	return m;

}
