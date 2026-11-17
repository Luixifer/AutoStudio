package com.luixifer.autostudio.test;
import android.app.*;
import android.content.*;
import android.os.*;
import android.widget.*;
import android.graphics.*;
import com.luixifer.autostudio.*;
import org.json.*;
import java.io.*;

/** Real Android UI -> GitHub REST -> real Actions -> real MP4 -> native decoder.
 * The short-lived CI credential arrives at runtime, never in either APK.
 */
public final class SmokeInstrumentation extends Instrumentation {
    private Bundle args;private JSONObject evidence=new JSONObject();private File qa;
    @Override public void onCreate(Bundle a){super.onCreate(a);args=a;start();}
    private interface Check{boolean ok() throws Exception;}
    private void require(boolean condition,String message) throws Exception{if(!condition)throw new Exception(message);}
    private void await(Check check,int seconds,String message) throws Exception{long until=SystemClock.elapsedRealtime()+seconds*1000L;while(SystemClock.elapsedRealtime()<until){if(check.ok())return;Thread.sleep(500);}throw new Exception(message);}
    private void shot(String name) throws Exception{Bitmap image=getUiAutomation().takeScreenshot();require(image!=null,"Could not capture the real Android display");try(FileOutputStream out=new FileOutputStream(new File(qa,name))){image.compress(Bitmap.CompressFormat.PNG,100,out);}image.recycle();}
    @Override public void onStart(){int code=Activity.RESULT_CANCELED;String mode=args.getString("mode","full");qa=new File(getTargetContext().getFilesDir(),"qa/"+mode);qa.mkdirs();String testToken=args.getString("githubToken");
        try{
            evidence.put("schema",1).put("mode",mode).put("scope","Android emulator UI and native decoder, not a physical Samsung test").put("physical_samsung_tested",false);
            Intent launch=new Intent(getTargetContext(),MainActivity.class);launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);MainActivity initial=(MainActivity)startActivitySync(launch);waitForIdleSync();shot("01-control.png");
            if(mode.equals("full")){
                require(testToken!=null&&testToken.length()>20,"CI runtime credential missing");int probes=0;
                while(true){probes++;try{new GitHubClient(testToken).verifyConnection();break;}catch(java.net.UnknownHostException|java.net.SocketTimeoutException|java.net.ConnectException transientNetwork){if(probes>=6)throw transientNetwork;Thread.sleep(2000);}}
                evidence.put("native_network_probes",probes).put("native_github_api_verified",true).put("runtime_credential_format_accepted",TokenFormat.acceptable(testToken));require(!new CredentialStore(getTargetContext()).connected(),"Expected an isolated fresh test profile");
                ActivityMonitor sm=addMonitor(SettingsActivity.class.getName(),null,false);runOnMainSync(()->initial.findViewById(Ui.SETTINGS).performClick());SettingsActivity settings=(SettingsActivity)sm.waitForActivityWithTimeout(10000);require(settings!=null,"Settings did not open");
                final String credential=testToken;runOnMainSync(()->{((EditText)settings.findViewById(Ui.TOKEN)).setText(credential);settings.findViewById(Ui.CONNECT).performClick();});
                await(()->{
                    if(new CredentialStore(getTargetContext()).connected())return true;
                    final String[] status={""};runOnMainSync(()->status[0]=((TextView)settings.findViewById(Ui.CONNECTION)).getText().toString());
                    if(status[0].startsWith("No se guardó"))throw new Exception("Connection screen: "+status[0]);return false;
                },60,"Real GitHub connection could not be saved");
                require(!getTargetContext().getSharedPreferences("private_connection",0).getAll().toString().contains(testToken),"Credential found in plaintext preferences");evidence.put("credential_encrypted",true);
                await(settings::isFinishing,5,"Settings did not return");waitForIdleSync();
                runOnMainSync(()->{((EditText)initial.findViewById(Ui.TOPIC)).setText("Quimiosíntesis: vida sin Sol en el océano profundo");initial.findViewById(Ui.GENERATE).performClick();});
                JobController jobs=((AutoStudioApp)initial.getApplication()).jobs();await(()->jobs.snapshot().has("request_id"),10,"No request was persisted");String id=jobs.snapshot().getString("request_id");require(GitHubClient.validId(id),"Invalid persisted request ID");
                ActivityMonitor recreated=addMonitor(MainActivity.class.getName(),null,false);runOnMainSync(initial::recreate);MainActivity replacement=(MainActivity)recreated.waitForActivityWithTimeout(10000);require(replacement!=null,"Activity recreation failed");require(jobs.snapshot().getString("request_id").equals(id),"Request changed across recreation");evidence.put("activity_recreation_preserved_request",true);
                await(()->{String status=jobs.snapshot().optString("status");if(status.equals("FAILED"))throw new Exception("Production failed: "+jobs.snapshot().optString("message")+" "+jobs.snapshot().optString("run_url"));return status.equals("READY");},600,"Cloud production did not become READY within 10 minutes");
                evidence.put("request_id",id).put("run_id",jobs.snapshot().optString("run_id")).put("run_url",jobs.snapshot().optString("run_url"));checkPlayback(replacement,jobs,id);
            }else{
                JobController jobs=((AutoStudioApp)initial.getApplication()).jobs();JSONObject restored=jobs.snapshot();require(restored.optString("status").equals("READY"),"Result not restored after process stop");require(new CredentialStore(getTargetContext()).connected(),"Encrypted connection not restored after process stop");require(jobs.history().length()==1,"Unexpected duplicate production history");String id=restored.getString("request_id");evidence.put("request_id",id).put("process_restart_preserved_result",true);checkPlayback(initial,jobs,id);
            }
            evidence.put("passed",true);code=Activity.RESULT_OK;
        }catch(Exception e){try{evidence.put("passed",false).put("failure",e.getClass().getSimpleName()+": "+String.valueOf(e.getMessage()));}catch(Exception ignored){}}
        try{String text=evidence.toString(2);if(testToken!=null&&text.contains(testToken))text="{\"passed\":false,\"failure\":\"Sensitive output blocked\"}";try(FileOutputStream out=new FileOutputStream(new File(qa,mode+".json"))){out.write(text.getBytes(java.nio.charset.StandardCharsets.UTF_8));}}catch(Exception e){code=Activity.RESULT_CANCELED;}
        Bundle result=new Bundle();result.putString("stream",evidence.optBoolean("passed")?"AutoStudio real Android integration passed\n":"AutoStudio integration failed; see isolated QA report\n");finish(code,result);
    }
    private void checkPlayback(MainActivity activity,JobController jobs,String id) throws Exception{
        File video=jobs.video(id);JSONObject result=jobs.snapshot().getJSONObject("result");require(video.isFile(),"No downloaded MP4");require(GitHubClient.sha256(video).equals(result.getJSONObject("video").getString("sha256")),"Downloaded SHA mismatch");
        waitForIdleSync();shot("02-ready.png");ActivityMonitor pm=addMonitor(PlayerActivity.class.getName(),null,false);runOnMainSync(()->activity.findViewById(Ui.PLAY).performClick());PlayerActivity player=(PlayerActivity)pm.waitForActivityWithTimeout(10000);require(player!=null,"Player did not open");
        await(()->{if(player.playbackFailed)throw new Exception("Native Android MediaPlayer failed");return player.firstFrameRendered&&player.playbackPosition()>600;},30,"No genuinely decoded frame or advancing playback position");
        shot("03-playing.png");evidence.put("video_sha256",GitHubClient.sha256(video)).put("video_bytes",video.length()).put("native_video_frame_rendered",true).put("playback_position_ms",player.playbackPosition());
    }
}
