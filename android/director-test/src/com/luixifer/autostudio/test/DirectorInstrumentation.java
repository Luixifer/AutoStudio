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
  String token=arguments.getString("githubToken");check(TokenFormat.acceptable(token),"Runtime token absent");int probes=0;while(true){probes++;try{new GitHubClient(token).verifyConnection();break;}catch(java.net.UnknownHostException|java.net.SocketTimeoutException|java.net.ConnectException transientNetwork){if(probes>=6)throw transientNetwork;Thread.sleep(2000);}}
  Context context=getTargetContext();new CredentialStore(context).save(token);DirectorStore store=new DirectorStore(context);
  // Fixture copied into this isolated UID by run-as, not a commercial profile.
  String projectId="11111111111111111111111111111111";JSONObject project=store.load(projectId);check(project.getString("title").contains("ENSAYO"),"Wrong isolated project");
  JSONArray parsed=DirectorStore.parseScript("# Uno\n\nPrimera escena.\n\nSegunda escena.\n\n# Dos\n\nTercera escena.");check(parsed.length()==2&&parsed.getJSONObject(0).getJSONArray("scenes").length()==2,"Script parser failed");
  File original=new File(store.folder(projectId),"media/image1.jpg");String imported=store.importFile(projectId,android.net.Uri.fromFile(original),"visual");check(DirectorStore.sha(original).equals(DirectorStore.sha(new File(store.folder(projectId),imported))),"Importer changed bytes");
  File bundle=store.bundle(projectId);check(bundle.length()>10000,"Empty project bundle");String restored=store.restore(android.net.Uri.fromFile(bundle));check(store.load(restored).getString("title").equals(project.getString("title")),"Project backup not restored");
  Activity activity=start(DirectorActivity.class,projectId);click(activity,2106);
  // Click the actual confirmation button; no alternate dispatch or consent bypass.
  java.lang.reflect.Field field=DirectorActivity.class.getDeclaredField("generationConfirmation");field.setAccessible(true);AlertDialog confirmation=(AlertDialog)field.get(activity);check(confirmation!=null&&confirmation.isShowing(),"No confirmation dialog");
  runOnMainSync(()->confirmation.getButton(android.content.DialogInterface.BUTTON_POSITIVE).performClick());waitForIdleSync();
  File jobFile=new File(store.folder(projectId),"job.json");long deadline=System.currentTimeMillis()+900000;JSONObject job=null;while(System.currentTimeMillis()<deadline){Thread.sleep(2500);if(jobFile.isFile()){job=DirectorStore.read(jobFile);if(job.optString("stage").equals("UNCERTAIN"))throw new Exception("Transport failed: "+job.optString("error"));if(job.optString("stage").equals("RUNNING"))break;} }
  check(job!=null&&job.optString("stage").equals("RUNNING"),"APK did not dispatch actual workflow");String requestId=job.getString("request_id");
  while(System.currentTimeMillis()<deadline){click(activity,2107);Thread.sleep(8000);job=DirectorStore.read(jobFile);if(job.optString("stage").equals("FAILED"))throw new Exception("Real production failed: "+job);if(job.optString("stage").equals("READY"))break;}
  check(job.optString("stage").equals("READY"),"No verified MP4 recovered within test deadline");JSONObject movie=job.getJSONObject("result");File mp4=new File(store.folder(projectId),"documental-REVISION.mp4");check(DirectorStore.sha(mp4).equals(movie.getString("sha256")),"Downloaded MP4 SHA mismatch");
  runOnMainSync(()->activity.finish());Activity preview=start(DirectorActivity.Preview.class,projectId);Thread.sleep(3000);
  final int[] positionValue={0};final boolean[] rendered={false};for(int i=0;i<20;i++){Thread.sleep(500);runOnMainSync(()->{DirectorActivity.Preview p=(DirectorActivity.Preview)preview;positionValue[0]=p.playbackPosition();rendered[0]=p.hasRenderedVideoFrame();});if(rendered[0]&&positionValue[0]>400)break;}
  int position=positionValue[0];check(rendered[0]&&position>400,"Native VideoView did not render a frame and advance playback");
  JSONObject report=new JSONObject().put("passed",true).put("request_id",requestId).put("github_run_id",movie.getString("github_run_id")).put("sha256",movie.getString("sha256")).put("duration",movie.getDouble("duration")).put("native_playback_position_ms",position).put("actual_video_frame_rendered",rendered[0]).put("project_zip_backup_restored",true).put("native_network_probes",probes).put("input_method","File URI through real ContentResolver; SAF picker UI requires human test").put("physical_samsung_tested",false);
  File qa=new File(context.getFilesDir(),"director-qa");qa.mkdirs();DirectorStore.write(new File(qa,"roundtrip.json"),report);getUiAutomation().takeScreenshot().compress(android.graphics.Bitmap.CompressFormat.PNG,100,new FileOutputStream(new File(qa,"preview.png")));result.putString("stream",report.toString(2));finish(Activity.RESULT_OK,result);
 }catch(Exception e){String message=e.toString();String token=arguments.getString("githubToken");if(token!=null)message=message.replace(token,"[REDACTED]");try{File qa=new File(getTargetContext().getFilesDir(),"director-qa");qa.mkdirs();DirectorStore.write(new File(qa,"roundtrip.json"),new JSONObject().put("passed",false).put("error",message).put("physical_samsung_tested",false));}catch(Exception ignored){}result.putString("stream","DIRECTOR_TEST_FAILED: "+message);finish(Activity.RESULT_CANCELED,result);}}
}
