"""Measure a real local command. Linux resource counters are not Android metrics."""
import argparse,json,resource,subprocess,time
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--report',type=Path,required=True);p.add_argument('command',nargs=argparse.REMAINDER);a=p.parse_args();command=a.command[1:] if a.command[:1]==['--'] else a.command
 if not command:raise ValueError('Falta comando')
 start=time.monotonic();result=subprocess.run(command);r=resource.getrusage(resource.RUSAGE_CHILDREN)
 report={'exit_code':result.returncode,'elapsed_seconds':round(time.monotonic()-start,3),'child_user_cpu_seconds':r.ru_utime,'child_system_cpu_seconds':r.ru_stime,'child_max_rss_kib':r.ru_maxrss,'scope':'Linux process resource counters; not a physical Android measurement','physical_samsung_tested':False}
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n');raise SystemExit(result.returncode)
if __name__=='__main__':main()
