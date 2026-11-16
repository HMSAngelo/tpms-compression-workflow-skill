"""Version-locked nTop 5.9.2 container adapter for existing project copies.

Preserves unknown sections byte-for-byte. This is a locally verified pilot,
not a vendor-supported general notebook authoring API.
"""
import json,struct
from pathlib import Path

MAGIC=b'MAGIC@@9'
class Chunk:
    def __init__(self,header,payload):
        self.header=header; self.payload=payload
        self.kind=header[8:24].split(b'\0')[0].decode('ascii')
        self.name=header[24:40].split(b'\0')[0].decode('ascii')
    @classmethod
    def read(cls,data,start=0):
        if data[start:start+8]!=MAGIC:raise ValueError('Unknown chunk magic')
        size=struct.unpack_from('<Q',data,start+40)[0];end=start+128+size
        if end>len(data):raise ValueError('Truncated chunk')
        return cls(data[start:start+128],data[start+128:end]),end
    def pack(self):
        header=bytearray(self.header);struct.pack_into('<Q',header,40,len(self.payload))
        return bytes(header)+self.payload
    def children(self):
        if self.kind!='ntopfn':raise ValueError('Not a function chunk')
        out=[];pos=0
        while pos<len(self.payload):
            child,pos=Chunk.read(self.payload,pos);out.append(child)
        return out
    def cache_index(self):
        if self.kind!='cache1':raise ValueError('Not a cache chunk')
        offset=struct.unpack_from('<Q',self.payload,0)[0]
        index,end=Chunk.read(self.payload,offset)
        if index.kind.lower()!='json' or index.name!='index' or end!=len(self.payload):
            raise ValueError('Unsupported cache layout')
        return offset,index

class Notebook:
    def __init__(self,data):
        if data[:8]!=b'MAGIC%$1':raise ValueError('Unsupported notebook container')
        n=struct.unpack_from('<Q',data,8)[0]
        if not 1<=n<=10000:raise ValueError('Invalid section count')
        self.header=data[:24+24*n+80];self.sections=[]
        start=len(self.header);prev=0
        for i in range(n):
            name=data[24+24*i:40+24*i].split(b'\0')[0].decode('ascii')
            end=struct.unpack_from('<Q',data,40+24*i)[0]
            chunk,pos=Chunk.read(data,start+prev)
            if pos!=start+end or chunk.name!=name:raise ValueError('Section table mismatch')
            self.sections.append(chunk);prev=end
        if start+prev!=len(data):raise ValueError('Trailing or missing bytes')
        version=json.loads(self.get('turhe').payload).get('turver')
        if version!=[5,9,2]:raise ValueError('Only 5.9.2 is supported: '+repr(version))
    def get(self,name):
        found=[c for c in self.sections if c.name==name]
        if len(found)!=1:raise ValueError('Ambiguous section '+name)
        return found[0]
    def pack(self):
        header=bytearray(self.header);body=[];total=0
        for i,chunk in enumerate(self.sections):
            part=chunk.pack();body.append(part);total+=len(part)
            struct.pack_into('<Q',header,40+24*i,total)
        return bytes(header)+b''.join(body)

def retarget(source,destination,paths,empty_cache_donor):
    source=Path(source);destination=Path(destination)
    if destination.exists() or destination.resolve()==source.resolve():raise ValueError('Output must be a new project copy')
    original=source.read_bytes();notebook=Notebook(original)
    if notebook.pack()!=original:raise ValueError('Lossless roundtrip failed')
    main=notebook.get('main');children=main.children()
    fn=next(c for c in children if c.name=='fn')
    graph=json.loads(fn.payload)
    if any('command' in n.get('func','').lower() for n in graph['code']):raise ValueError('Command blocks are excluded')
    leaves=next(c for c in children if c.name=='leaves')
    offset,index=leaves.cache_index();records=json.loads(index.payload)
    baseline_records=json.loads(index.payload)
    changes=[]
    for record in records:
        if record.get('type')=='file_path':
            key=str(record['id'])
            if key not in paths:raise ValueError('Unmapped file path leaf '+key)
            value=record['value'];old=value['val'];value['val']=str(paths[key]).replace('\\','/')
            changes.append({'node':key,'original':old,'replacement':value['val']})
    if {c['node'] for c in changes}!=set(paths):raise ValueError('Path map does not match source leaves')
    # Only file-path values change; source graph and all numerical parameters remain intact.
    index.payload=json.dumps(records,ensure_ascii=False,separators=(',',':')).encode('utf-8')
    leaves.payload=leaves.payload[:offset]+index.pack()
    main.payload=b''.join(c.pack() for c in children)
    donor=Notebook(Path(empty_cache_donor).read_bytes()).get('cache')
    _,donor_index=donor.cache_index()
    if json.loads(donor_index.payload)!=[]:raise ValueError('Donor computational cache is not empty')
    target_cache=notebook.get('cache');target_cache.payload=donor.payload
    result=notebook.pack();check=Notebook(result)
    check_fn=next(c for c in check.get('main').children() if c.name=='fn')
    if check_fn.payload!=fn.payload:raise ValueError('Geometry/meshing function graph changed')
    check_leaves=next(c for c in check.get('main').children() if c.name=='leaves')
    _,check_index=check_leaves.cache_index();actual=json.loads(check_index.payload)
    before_nonpaths=[r for r in baseline_records if r.get('type')!='file_path']
    after_nonpaths=[r for r in actual if r.get('type')!='file_path']
    if before_nonpaths!=after_nonpaths:raise ValueError('A non-path input value changed')
    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(result)
    return {'source':str(source),'destination':str(destination),'lossless_baseline':True,'version':[5,9,2],
            'graph_unchanged':True,'numeric_parameters_unchanged':True,'computed_cache_cleared':True,'path_changes':changes}
