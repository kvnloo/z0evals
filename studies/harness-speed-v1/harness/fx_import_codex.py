# Import ~/.codex/auth.json ChatGPT tokens into fx's ~/.fx/chatgpt-auth.json. Never prints token values.
import json,os,base64,tempfile,sys
H=os.path.expanduser
src=json.load(open(H('~/.codex/auth.json')))
t=src['tokens']
acc,ref,aid=t['access_token'],t['refresh_token'],t.get('account_id')
p=acc.split('.')[1]; p+='='*(-len(p)%4); claims=json.loads(base64.urlsafe_b64decode(p))
aid=aid or claims['https://api.openai.com/auth']['chatgpt_account_id']
out={"version":1,"access_token":acc,"refresh_token":ref,"expires_at_ms":int(claims['exp'])*1000,"account_id":aid}
d=H('~/.fx'); os.makedirs(d,exist_ok=True); os.chmod(d,0o700)
dst=os.path.join(d,'chatgpt-auth.json')
if os.path.exists(dst) and '--force' not in sys.argv: sys.exit('exists; refusing')
fd,tmp=tempfile.mkstemp(dir=d,prefix='.chatgpt-auth.'); os.fchmod(fd,0o600)
with os.fdopen(fd,'w') as f: f.write(json.dumps(out,separators=(',',':'))+'\n')
os.replace(tmp,dst)
print('wrote',dst,'mode',oct(os.stat(dst).st_mode&0o777),'expires_at_ms',out['expires_at_ms'],'account_id_len',len(aid))
