#!/usr/bin/env python3
"""Production C envelope checks against independent Python struct/zlib fixtures."""
import argparse,ctypes as c,json,os,struct,subprocess,tempfile,zlib
from pathlib import Path
class Binding(c.Structure):_fields_=[(n,c.c_uint32) for n in ('rom_crc','code_crc','layout_crc','config_crc')]
class Owner(c.Structure):_fields_=[('id',c.c_uint32),('bytes',c.c_uint32)]
class Progress(c.Structure):_fields_=[('guest',c.c_uint32),('render',c.c_uint32)]
U8=c.POINTER(c.c_ubyte);Read=c.CFUNCTYPE(c.c_int,c.c_uint32,c.c_uint,U8)
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--cc',default=os.environ.get('CC','gcc'));ap.add_argument('--output',type=Path)
    a=ap.parse_args();root=Path(__file__).resolve().parents[1];cases=0
    with tempfile.TemporaryDirectory(prefix='s64-state-format-') as d:
        dll=Path(d)/('format.dll' if os.name=='nt' else 'format.so')
        cmd=[a.cc,'-std=c11','-O2','-shared','-Wall','-Wextra','-Werror']
        if os.name=='nt':cmd+=['-Wl,--export-all-symbols']
        else:cmd+=['-fPIC']
        subprocess.run(cmd+[str(root/'src/scene_state_format.c'),'-o',str(dll)],check=True)
        lib=c.CDLL(str(dll));lib.scene_state_header.argtypes=[U8,c.POINTER(Binding),c.POINTER(Owner),c.c_uint,Progress,c.c_uint32]
        lib.scene_state_validate.argtypes=[Read,U8,c.c_uint32,c.POINTER(Binding),c.POINTER(Owner),c.c_uint,c.POINTER(Progress)]
        owners=(Owner*3)(Owner(1,13),Owner(7,512),Owner(9,600));bind=Binding(0x12345678,0x9abcdef0,31,47)
        payload=bytes((i*73+29)&255 for i in range(1125));offset=0;table=b''
        for owner in owners:table+=struct.pack('>III',owner.id,owner.bytes,offset);offset+=owner.bytes
        body=table+payload;header=(c.c_ubyte*64)()
        assert lib.scene_state_header(header,c.byref(bind),owners,3,Progress(0xffffffff,0xffffffff),zlib.crc32(body))==1
        values=list(struct.unpack('>16I',bytes(header)));assert values[:5]==[0x53363453,1,64,3,1125]
        expected=struct.pack('>16I',*values[:12],0,*values[13:]);assert values[12]==zlib.crc32(expected)
        golden=bytes(header)+body
        def test(raw,result,*,binding=bind,selected=owners,count=3,available=None,fail=0):
            nonlocal cases
            raw=bytes(raw);calls=0;callback_errors=[]
            @Read
            def read(offset,size,output):
                nonlocal calls
                calls+=1
                if calls==fail or offset+size>len(raw):return 0
                try:c.memmove(output,raw[offset:offset+size],size);return 1
                except Exception as error:callback_errors.append(error);return 0
            progress=Progress(101,202);scratch=(c.c_ubyte*512)()
            actual=lib.scene_state_validate(read,scratch,len(raw) if available is None else available,
                c.byref(binding),selected,count,c.byref(progress))
            assert not callback_errors,callback_errors
            assert actual==result,(cases,actual,result)
            assert (progress.guest,progress.render)==((0xffffffff,0xffffffff) if result==1 else (101,202))
            cases+=1;return calls
        assert test(golden,1)==7
        for field in range(16):
            changed=bytearray(golden);changed[4*field+3]^=1;test(changed,0)
        for position in range(64,len(golden)):
            changed=bytearray(golden);changed[position]^=0x80;test(changed,0)
        for size in (0,63,64,65,len(golden)-1,len(golden)+1):test(golden[:size] if size<=len(golden) else golden+b'\0',0)
        for field in range(4):
            wrong=Binding(bind.rom_crc,bind.code_crc,bind.layout_crc,bind.config_crc)
            setattr(wrong,Binding._fields_[field][0],getattr(wrong,Binding._fields_[field][0])^1)
            assert test(golden,0,binding=wrong)==1
        for fail in range(1,8):test(golden,-1,fail=fail)
        for bad in ((Owner(1,0),),(Owner(1,0x400000),),(Owner(1,4),Owner(1,4))):
            selected=(Owner*len(bad))(*bad);assert test(golden,0,selected=selected,count=len(bad))==0
        assert test(golden,0,count=0)==0
        assert test(golden,0,count=33)==0
        # Recompute both CRCs: descriptor aliases/reordering still fail whitelist.
        for word in range(9):
            changed=bytearray(golden);changed[64+word*4+3]^=1
            struct.pack_into('>I',changed,44,zlib.crc32(changed[64:]))
            struct.pack_into('>I',changed,48,0);struct.pack_into('>I',changed,48,zlib.crc32(changed[:64]))
            test(changed,0)
        result=dict(passed=True,cases=cases,production_C=True,independent_BE_zlib_oracle=True,
                    wrong_bindings_whitelist_bounds_truncation_checksum_IO_rejected=True,
                    result_unchanged_on_failure=True,machine_mutation=False,native_acceptance=False,
                    complete_serializer_or_restore=False)
        if a.output:a.output.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result))
        # Windows keeps the loaded DLL locked until process exit. Temp cleanup
        # may retain this one private runtime temp file; close it explicitly.
        if os.name=='nt':c.windll.kernel32.FreeLibrary(c.c_void_p(lib._handle))
if __name__=='__main__':main()
