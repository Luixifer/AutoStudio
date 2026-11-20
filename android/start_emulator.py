"""Start the real isolated Android AVD, with explicit SDK executables and homes."""
import os,subprocess,time
from pathlib import Path

def toolchain(env=None):
    env=dict(os.environ if env is None else env);sdk=Path(env['ANDROID_HOME']).resolve()
    base=Path(env.get('ANDROID_USER_HOME',str(Path(env['RUNNER_TEMP'])/'autostudio-android'))).resolve()
    avds=Path(env.get('ANDROID_AVD_HOME',str(base/'avd'))).resolve()
    env.update(ANDROID_USER_HOME=str(base),ANDROID_AVD_HOME=str(avds),ANDROID_EMULATOR_HOME=str(base))
    tools={'adb':sdk/'platform-tools/adb','emulator':sdk/'emulator/emulator','avdmanager':sdk/'cmdline-tools/latest/bin/avdmanager'}
    return env,tools,base,avds

def main():
    env,tools,base,avds=toolchain();base.mkdir(exist_ok=True,parents=True);avds.mkdir(exist_ok=True,parents=True)
    for name,path in tools.items():
        if not path.is_file() or not os.access(path,os.X_OK):raise RuntimeError(f'Missing official SDK executable: {name} at {path}')
    def run(name,*args,**kwargs):return subprocess.run([str(tools[name]),*args],env=env,check=True,timeout=120,**kwargs)
    run('adb','version');run('avdmanager','create','avd','--force','--name','AutoStudio','--package',env['ANDROID_IMAGE'],'--device','pixel_6','--path',str(avds/'AutoStudio.avd'),input='no\n',text=True)
    ini=avds/'AutoStudio.ini'
    # Define the pointer explicitly if different SDK generations choose another default.
    if not ini.exists():ini.write_text(f'avd.ini.encoding=UTF-8\npath={avds/"AutoStudio.avd"}\ntarget=android-35\n')
    if not (avds/'AutoStudio.avd/config.ini').is_file():raise RuntimeError('avdmanager did not create an actual device configuration.')
    names=subprocess.check_output([str(tools['emulator']),'-list-avds'],env=env,text=True)
    print('SDK paths verified. AVDs:',names.strip(),flush=True)
    if 'AutoStudio' not in names.splitlines():raise RuntimeError('Emulator cannot find the AVD created by avdmanager.')
    Path('reports').mkdir(exist_ok=True)
    with open('reports/emulator.log','w') as log:
        process=subprocess.Popen([str(tools['emulator']),'-avd','AutoStudio','-no-window','-no-metrics','-no-audio','-no-boot-anim','-no-snapshot','-dns-server','8.8.8.8,8.8.4.4','-gpu','swiftshader','-camera-back','none','-camera-front','none','-memory','2048','-cores','2','-accel','on'],env=env,stdout=log,stderr=subprocess.STDOUT)
    Path('reports/emulator.pid').write_text(str(process.pid))
    run('adb','wait-for-device');deadline=time.monotonic()+300
    while time.monotonic()<deadline:
        if process.poll() is not None:raise RuntimeError('Real emulator exited; see reports/emulator.log.')
        boot=subprocess.run([str(tools['adb']),'shell','getprop','sys.boot_completed'],env=env,text=True,capture_output=True,timeout=15)
        if boot.returncode==0 and boot.stdout.strip()=='1':break
        time.sleep(2)
    else:raise RuntimeError('Android did not finish booting within five minutes.')
    for args in [('wm','size','450x800'),('wm','density','160'),('settings','put','global','window_animation_scale','0'),('settings','put','global','transition_animation_scale','0'),('settings','put','global','animator_duration_scale','0'),('input','keyevent','82')]:run('adb','shell',*args)
    run('adb','install',env.get('AUTOSTUDIO_EMULATOR_APK','build/android/AutoStudio-Control-0.4.0-lab.apk'));run('adb','install','build/android/autostudio-instrumentation.apk')
    print('Actual Android 15 booted and both APKs installed.',flush=True)
if __name__=='__main__':main()
