package com.luixifer.autostudio.test;
import android.app.*;
import android.content.*;
import android.os.*;
import android.widget.*;
import com.luixifer.autostudio.*;
import org.json.*;
import java.io.*;

/** Real emulator + official GitHub APIs + actual FFmpeg workflow + native codec.
 * Input file URI fixture exercises importer; system SAF picker needs manual review.
 */
public final class DirectorInstrumentation extends Instrumentation {
 Bundle arguments;private void check(boolean b,String message)throws Exception{if(!b)throw new Exception(message);}
 @Override public void onCreate(Bundle b){arguments=b;start();}
 private void click(Activity activity,int id)throws Exception{runOnMainSync(()->((Button)activity.findViewById(id)).performClick());waitForIdleSync();}
 private Activity start(Class<?> cls,String id){Intent i=new Intent(getTargetContext(),cls).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);if(id!=null)i.putExtra("project_id",id);return startActivitySync(i);}
 @Override public void onStart(){Bundle result=new Bundle();try{
  String token=arguments.getString("githubToken");check(TokenFormat.acceptable(token),"Runtime token absent");Context context=getTargetContext();new CredentialStore(context).save(token);DirectorStore store=new DirectorStore(context);
  // Fixture copied into this isolated UID by run-as, not a commercial profile.
  String projectId="11111111111111111111111111111111";JSONObject project=store.load(projectId);check(project.getString("title").contains("ENSAYO"),"Wrong isolated project");
  JSONArray parsed=DirectorStore.parseScript("# Uno\n\nPrimera escena.\n\nSegunda escena.\n\n# Dos\n\nTercera escena.");check(parsed.length()==2&&parsed.getJSONObject(0).getJSONArray("scenes").length()==2,"Script parser failed");
  File original=new File(store.folder(projectId),"media/image1.jpg");String imported=store.importFile(projectId,android.net.Uri.fromFile(original),"visual");check(DirectorStore.sha(original).equals(DirectorStore.sha(new File(store.folder(projectId),imported))),"Importer changed bytes");
  File bundle=store.bundle(projectId);check(bundle.length()>10000,"Empty project bundle");
  Activity activity=start(DirectorActivity.class,projectId);click(activity,2106);
  // Positive confirmation is an actual dialog button, located by its window root.
  // Use a monitor-free accessibility traversal for the explicit confirmation.
  Thread.sleep(800);android.app.UiAutomation ui=getUiAutomation();android.view.accessibility.AccessibilityNodeInfo node=ui.getRootInActiveWindow();
  check(node!=null,"No confirmation window");java.util.List<android.view.accessibility.AccessibilityNodeInfo> buttons=node.findAccessibilityNodeInfosByText("Confirmar y generar");check(!buttons.isEmpty(),"Confirmation button absent");buttons.get(0).performAction(android.view.accessibility.AccessibilityNodeInfo.ACTION_CLICK);waitForIdleSync();
  File jobFile=new File(store.folder(projectId),"job.json");long deadline=System.currentTimeMillis()+900000;JSONObject job=null;while(System.currentTimeMillis()<deadline){Thread.sleep(2500);if(jobFile.isFile()){job=DirectorStore.read(jobFile);if(job.optString("stage").equals("RUNNING"))break;} }
  check(job!=null&&job.optString("stage").equals("RUNNING"),"APK did not dispatch actual workflow");String requestId=job.getString("request_id");
  while(System.currentTimeMillis()<deadline){click(activity,2107);Thread.sleep(8000);job=DirectorStore.read(jobFile);if(job.optString("stage").equals("FAILED"))throw new Exception("Real production failed: "+job);if(job.optString("stage").equals("READY"))break;}
  check(job.optString("stage").equals("READY"),"No verified MP4 recovered within test deadline");JSONObject movie=job.getJSONObject("result");File mp4=new File(store.folder(projectId),"documental-REVISION.mp4");check(DirectorStore.sha(mp4).equals(movie.getString("sha256")),"Downloaded MP4 SHA mismatch");
  runOnMainSync(()->activity.finish());Activity preview=start(DirectorActivity.Preview.class,projectId);Thread.sleep(3000);
  // Independent native MediaPlayer decode and advancing clock.
  android.media.MediaPlayer player=new android.media.MediaPlayer();player.setDataSource(mp4.toString());player.prepare();player.setVolume(0,0);player.start();Thread.sleep(1000);int position=player.getCurrentPosition();check(position>400,"Native playback did not advance");player.release();
  JSONObject report=new JSONObject().put("passed",true).put("request_id",requestId).put("github_run_id",movie.getString("github_run_id")).put("sha256",movie.getString("sha256")).put("duration",movie.getDouble("duration")).put("native_playback_position_ms",position).put("input_method","File URI through real ContentResolver; SAF picker UI requires human test").put("physical_samsung_tested",false);
  File qa=new File(context.getFilesDir(),"director-qa");qa.mkdirs();DirectorStore.write(new File(qa,"roundtrip.json"),report);ui.takeScreenshot().compress(android.graphics.Bitmap.CompressFormat.PNG,100,new FileOutputStream(new File(qa,"preview.png")));result.putString("stream",report.toString(2));finish(Activity.RESULT_OK,result);
 }catch(Exception e){result.putString("stream","DIRECTOR_TEST_FAILED: "+e.toString());finish(Activity.RESULT_CANCELED,result);}}
}
