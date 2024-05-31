import struct, ctypes
from ctypes import c_ushort, c_uint16, c_uint32, c_ulong, c_ulonglong, c_long, c_longlong, c_float, c_double, c_ubyte, Union

from .messages_base import BaseStructure


class BaseDouble(BaseStructure):
    _fields_ = [
        ('flt', c_double)
    ]


class BaseFloat(BaseStructure):
    _fields_ = [
        ('flt', c_float)
    ]


class BaseLongLong(BaseStructure):
    _fields_ = [
        ('u64', c_longlong)
    ]


class BaseULongLong(BaseStructure):
    _fields_ = [
        ('u32', c_ulonglong)
    ]


class BaseLong(BaseStructure):
    _fields_ = [
        ('u32', c_long)
    ]


class BaseU32(BaseStructure):
    _fields_ = [
        ('u32', c_uint32)
    ]


class BaseU16(BaseStructure):
    _fields_ = [
        ('u16', c_uint16)
    ]


class DataUnion(Union):
    
    def get_format(self, field_name=''):
        if field_name:
            obj = getattr(self, field_name)
            if issubclass(obj.__class__, ctypes.Array):
                return (obj._type_._type_ * obj._length_)
            else:
                return obj.get_format()
        obj = self._fields_[0][1]
        return (obj._type_._type_ * obj._length_)

    def get_bytes_size(self, field_name=''):
        if field_name:
            obj = getattr(self, field_name)
            if issubclass(obj.__class__, ctypes.Array):
                return (struct.calcsize(obj._type_._type_) * obj._length_)
            else:
                return obj.get_bytes_size()
        obj = self._fields_[0][1]
        return (struct.calcsize(obj._type_._type_) * obj._length_)

    def get_values(self, field_name=''):   # Returns a tuple with values
        if field_name:
            obj = getattr(self, field_name)
            if issubclass(obj.__class__, ctypes.Array):
                values = ()
                for value in obj:
                    var = (value,)
                    values = sum((values, var), ())
                return values
            else:
                return obj.get_values()
        field_name = self._fields_[0][0]
        arr = getattr(self, field_name)
        values = ()
        for value in arr:
            var = (value,)
            values = sum((values, var), ())
        return values
    
    def get_len(self):
        return len(self.get_values())
    
    def store_values(self, values, field_name=''):     # Receives values in tuple to store
        if field_name:
            obj = getattr(self, field_name)
            if issubclass(obj.__class__, ctypes.Array):
                arr = enumerate(obj)
                for e in arr:
                    index = e[0]
                    obj[index] = values[index]
                setattr(self, field_name, obj)
            else:
                obj.store_values(values)
        else:
            field_name = self._fields_[0][0]
            obj = getattr(self, field_name)
            arr = enumerate(obj)
            for e in arr:
                index = e[0]
                obj[index] = values[index]
            setattr(self, field_name, obj)

    def pacself(self):    # Returns structure in bytes format
        frm = self.get_format()
        values = self.get_values()
        data = b''
        for i in range(0, len(frm)):
            f = frm[i]
            value = values[i]
            data = b''.join([data, struct.pack(f, value)])
        return data

    def unpacdata(self, raw_data):
        unpacked_data = struct.unpack(self.get_format(), raw_data)
        return unpacked_data

    def store_from_raw(self, raw_values):
        self.store_values(self.unpacdata(raw_data=raw_values))

    def to_dict(self):
        dict = {}
        for field in self._fields_:
            field_type = field[1]
            key = field[0]
            value = getattr(self, key)

            if not issubclass(field_type, ctypes._SimpleCData):
                aux_dict = value.to_dict()
                value = aux_dict

            dict[key] = value

        return dict


class Dato16(DataUnion):
    _fields_ = [
        ('u8', c_ubyte * 2),
        ('u16', BaseU16)
    ]


class Dato32(DataUnion):
    _fields_ = [
        ('u8', c_ubyte * 4),
        ('u16', c_ushort * 2),
        ('u32', BaseLong),
        ('flt', BaseFloat)
    ]


class Dato64(DataUnion):
    _fields_ = [
        ('u32', c_ulong * 2),
        ('i32', c_long * 2),
        ('i64', BaseULongLong),
        ('u64', BaseLongLong),
        ('flt', BaseDouble)
    ]


###############################################################################################
###################################### Networking #############################################
###############################################################################################

# Definicion tipo IP address (Big-Endian, alineacion a 32bits)

class IpAddr(Dato32):

    def get_int_from_string(self, ip_addr):
        a, b, c, d = ip_addr.split('.')
        return (int(a), int(b), int(c), int(d))

    def store_from_string(self, ip_addr):
        super().store_values(self.get_int_from_string(ip_addr))



class IpU32(BaseStructure):
    _fields_ = [
        ('ip_u32', c_ulong)
    ]


class MacAddr(DataUnion):
    _fields_ = [
        ('u8', c_ubyte * 6),
        ('u16', c_ushort)
    ]


class IpConfig(BaseStructure):
    _fields_ = [
        ('net_msk', IpAddr),
        ('ip_addr', IpAddr)
    ]