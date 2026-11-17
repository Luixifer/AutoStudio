#!/usr/bin/env python3
"""Build native Java APKs with official Android SDK tools. No Gradle/plugin download.
ANDROID_HOME/ANDROID_SDK_ROOT and a full JDK 17+ are required. Debug signing only.
"""
import hashlib,json,os,shutil,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];PROJECT=ROOT/'android';OUT=ROOT/'build/android'
PACKAGE='com.luixifer.autostudio.lab';APP_NAME='AutoStudio-Control-0.3.0-lab.apk'
def run(*args):subprocess.run([str(x) for x in args],check=True)
def main():
    sdk=Path(os.environ.get('ANDROID_HOME',os.environ.get('ANDROID_SDK_ROOT','/nonexistent')));java=Path(os.environ.get('JAVA_HOME','/nonexistent'))
    tools=sdk/'build-tools/35.0.0';platform=sdk/'platforms/android-35/android.jar'
    if not platform.is_file() or not (java/'bin/javac').is_file():raise RuntimeError('Need Android platform 35, build-tools 35.0.0 and a full JDK. See android/README.md.')
    os.environ['PATH']=str(java/'bin')+os.pathsep+os.environ['PATH'];os.environ['JAVA_HOME']=str(java)
    OUT.mkdir(parents=True,exist_ok=True);unit=OUT/'unit';unit.mkdir(exist_ok=True)
    run(java/'bin/javac','-encoding','UTF-8','-d',unit,PROJECT/'app/src/com/luixifer/autostudio/TokenFormat.java',PROJECT/'test/unit/TokenFormatTest.java')
    run(java/'bin/java','-cp',unit,'TokenFormatTest')
    work=OUT/'work';shutil.rmtree(work,ignore_errors=True);work.mkdir();classes=work/'classes';classes.mkdir();gen=work/'gen';gen.mkdir();res=work/'res';res.mkdir();dex=work/'dex';dex.mkdir()
    run(tools/'aapt2','compile','--dir',PROJECT/'app/res','-o',res)
    run(tools/'aapt2','link','-I',platform,'--manifest',PROJECT/'app/AndroidManifest.xml','--java',gen,'-o',work/'base.apk',*sorted(res.glob('*.flat')))
    sources=[*sorted((PROJECT/'app/src').rglob('*.java')),*sorted(gen.rglob('*.java'))]
    run(java/'bin/javac','-encoding','UTF-8','-source','8','-target','8','-bootclasspath',str(platform)+os.pathsep+str(tools/'core-lambda-stubs.jar'),'-d',classes,*sources)
    run(tools/'d8','--lib',platform,'--min-api','26','--output',dex,*sorted(classes.rglob('*.class')))
    unsigned=work/'unsigned.apk';shutil.copy2(work/'base.apk',unsigned)
    with zipfile.ZipFile(unsigned,'a') as z:
        for f in dex.glob('*.dex'):z.write(f,f.name,compress_type=zipfile.ZIP_STORED)
    key=Path(os.environ.get('AUTOSTUDIO_DEBUG_KEYSTORE',str(ROOT/'.cache/android-debug.keystore')));key.parent.mkdir(exist_ok=True,parents=True)
    if not key.exists():run(java/'bin/keytool','-genkeypair','-keystore',key,'-storepass','android','-alias','androiddebugkey','-keypass','android','-keyalg','RSA','-keysize','2048','-validity','10000','-dname','CN=Android Debug,O=AutoStudio Lab,C=ES','-noprompt')
    def sign(source,target):
        aligned=work/(target.stem+'-aligned.apk');run(tools/'zipalign','-f','4',source,aligned);run(tools/'apksigner','sign','--ks',key,'--ks-key-alias','androiddebugkey','--ks-pass','pass:android','--key-pass','pass:android','--out',target,aligned);run(tools/'apksigner','verify','--verbose','--print-certs',target)
    target=OUT/APP_NAME;sign(unsigned,target)
    # Separate instrumentation APK: never distributed as the control app.
    testclasses=work/'testclasses';testclasses.mkdir();testdex=work/'testdex';testdex.mkdir()
    testmanifest=PROJECT/'test/AndroidManifest.xml'
    if testmanifest.exists():
        run(java/'bin/javac','-encoding','UTF-8','-source','8','-target','8','-bootclasspath',str(platform)+os.pathsep+str(tools/'core-lambda-stubs.jar'),'-cp',classes,'-d',testclasses,*sorted((PROJECT/'test/src').rglob('*.java')))
        run(tools/'d8','--lib',platform,'--classpath',classes,'--min-api','26','--output',testdex,*sorted(testclasses.rglob('*.class')))
        run(tools/'aapt2','link','-I',platform,'--manifest',testmanifest,'-o',work/'test-base.apk')
        with zipfile.ZipFile(work/'test-base.apk','a') as z:
            for f in testdex.glob('*.dex'):z.write(f,f.name,compress_type=zipfile.ZIP_STORED)
        sign(work/'test-base.apk',OUT/'autostudio-instrumentation.apk')
    info={'schema':1,'application_id':PACKAGE,'version_name':'0.3.0-lab','signing':'debug-only; no release credentials','architectures':'Java DEX, no native libraries; runs on ARM64 or x86_64 Android API 26+','apk':target.name,'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'github_run_id':os.environ.get('GITHUB_RUN_ID'),'worktree_dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),'physical_samsung_tested':False}
    (OUT/'apk-info.json').write_text(json.dumps(info,indent=2)+'\n');(OUT/'SHA256SUMS').write_text(info['sha256']+'  '+target.name+'\n');print('REAL_APK',target)
if __name__=='__main__':main()
