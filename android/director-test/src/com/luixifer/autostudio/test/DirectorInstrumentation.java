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
 private void collectText(android.view.View view,java.util.List<android.widget.TextView> out){if(view instanceof android.widget.TextView)out.add((android.widget.TextView)view);if(view instanceof android.view.ViewGroup){android.view.ViewGroup group=(android.view.ViewGroup)view;for(int i=0;i<group.getChildCount();i++)collectText(group.getChildAt(i),out);}}
 @Override public void onCreate(Bundle b){arguments=b;start();}
 private void click(Activity activity,int id)throws Exception{runOnMainSync(()->((Button)activity.findViewById(id)).performClick());waitForIdleSync();}
 private void checkUiError(Activity activity)throws Exception{java.lang.reflect.Field f=DirectorActivity.class.getDeclaredField("lastOperationError");f.setAccessible(true);String error=(String)f.get(activity);if(error!=null)throw new Exception("Actual UI error: "+error);}
 private Activity start(Class<?> cls,String id){Intent i=new Intent(getTargetContext(),cls).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);if(id!=null)i.putExtra("project_id",id);return startActivitySync(i);}
 private void recovery()throws Exception{
  Context context=getTargetContext();DirectorStore store=new DirectorStore(context);String projectId="11111111111111111111111111111111";File dir=store.folder(projectId);JSONObject before=DirectorStore.read(new File(dir,"job.json"));check(before.getString("stage").equals("READY"),"Completed job not restored");check(new CredentialStore(context).connected(),"Encrypted credential not restored");
  Activity project=start(DirectorActivity.class,projectId);ActivityMonitor monitor=addMonitor(DirectorActivity.Preview.class.getName(),null,false);click(project,2119);
  Activity preview=monitor.waitForActivityWithTimeout(10000);check(preview!=null,"Recovered preview did not open from its real button");removeMonitor(monitor);final boolean[] frame={false};final int[] position={0};for(int i=0;i<20;i++){Thread.sleep(500);runOnMainSync(()->{DirectorActivity.Preview p=(DirectorActivity.Preview)preview;frame[0]=p.hasRenderedVideoFrame();position[0]=p.playbackPosition();});if(frame[0]&&position[0]>400)break;}
  check(frame[0]&&position[0]>400,"Recovered VideoView did not render");click(preview,2301);
  android.net.Uri exported=null;long until=System.currentTimeMillis()+45000;
  while(System.currentTimeMillis()<until){Thread.sleep(500);try(android.database.Cursor c=context.getContentResolver().query(android.provider.MediaStore.Downloads.EXTERNAL_CONTENT_URI,new String[]{"_id","_size","is_pending","_display_name"},"_display_name=?",new String[]{"AutoStudio-Director-11111111.mp4"},null)){if(c!=null)while(c.moveToNext())if(c.getInt(2)==0&&c.getLong(1)>0)exported=android.content.ContentUris.withAppendedId(android.provider.MediaStore.Downloads.EXTERNAL_CONTENT_URI,c.getLong(0));}if(exported!=null)break;}
  check(exported!=null,"No complete exported file in MediaStore Downloads");java.security.MessageDigest sha=java.security.MessageDigest.getInstance("SHA-256");try(InputStream in=context.getContentResolver().openInputStream(exported)){check(in!=null,"Cannot read owned download");byte[] b=new byte[65536];int n;while((n=in.read(b))!=-1)sha.update(b,0,n);}StringBuilder hash=new StringBuilder();for(byte b:sha.digest())hash.append(String.format(java.util.Locale.ROOT,"%02x",b&255));check(hash.toString().equals(before.getJSONObject("result").getString("sha256")),"Exported download SHA mismatch");
  JSONObject after=DirectorStore.read(new File(dir,"job.json"));check(after.getString("request_id").equals(before.getString("request_id")),"Recovery generated another request");JSONObject report=new JSONObject().put("passed",true).put("process_restart_preserved_project",true).put("encrypted_connection_restored",true).put("actual_video_frame_rendered",frame[0]).put("native_playback_position_ms",position[0]).put("download_export_sha256",hash.toString()).put("request_id",after.getString("request_id")).put("physical_samsung_tested",false);File qa=new File(context.getFilesDir(),"director-qa");qa.mkdirs();DirectorStore.write(new File(qa,"recovery.json"),report);Bundle result=new Bundle();result.putString("stream",report.toString(2));finish(Activity.RESULT_OK,result);
 }
 @Override public void onStart(){Bundle result=new Bundle();try{
  if("recovery".equals(arguments.getString("mode"))){recovery();return;}
  String token=arguments.getString("githubToken");check(TokenFormat.acceptable(token),"Runtime token absent");int probes=0;while(true){probes++;try{new GitHubClient(token).verifyConnection();break;}catch(java.net.UnknownHostException|java.net.SocketTimeoutException|java.net.ConnectException transientNetwork){if(probes>=6)throw transientNetwork;Thread.sleep(2000);}}
  Context context=getTargetContext();new CredentialStore(context).save(token);DirectorStore store=new DirectorStore(context);
  // Fixture copied into this isolated UID by run-as, not a commercial profile.
  String projectId="11111111111111111111111111111111";JSONObject project=store.load(projectId);check(project.getString("title").contains("ENSAYO"),"Wrong isolated project");
  JSONArray parsed=DirectorStore.parseScript("# Uno\n\nPrimera escena.\n\nSegunda escena.\n\n# Dos\n\nTercera escena.");check(parsed.length()==2&&parsed.getJSONObject(0).getJSONArray("scenes").length()==2,"Script parser failed");
  File original=new File(store.folder(projectId),"media/image1.jpg");String imported=store.importFile(projectId,android.net.Uri.fromFile(original),"visual");check(DirectorStore.sha(original).equals(DirectorStore.sha(new File(store.folder(projectId),imported))),"Importer changed bytes");
  JSONObject voice=project.getJSONArray("chapters").getJSONObject(0).getJSONArray("scenes").getJSONObject(0).optJSONObject("voice");if(voice!=null){File mp3=new File(store.folder(projectId),voice.getString("path"));String importedVoice=store.importFile(projectId,android.net.Uri.fromFile(mp3),"voice");check(DirectorStore.sha(mp3).equals(DirectorStore.sha(new File(store.folder(projectId),importedVoice))),"MP3 importer changed bytes");}
  File bundle=store.bundle(projectId);check(bundle.length()>10000,"Empty project bundle");String restored=store.restore(android.net.Uri.fromFile(bundle));check(store.load(restored).getString("title").equals(project.getString("title")),"Project backup not restored");
  Activity settings=start(SettingsActivity.class,null);final boolean[] correctPermission={false};runOnMainSync(()->{java.util.List<android.widget.TextView> labels=new java.util.ArrayList<>();collectText(settings.getWindow().getDecorView(),labels);correctPermission[0]=labels.stream().anyMatch(v->v.getText().toString().contains("Contents → lectura y escritura"));});check(correctPermission[0],"Director settings requested insufficient permissions");runOnMainSync(()->settings.finish());
  // Test the new home and actual simple editor; retain the legacy store checks above.
  Activity home=start(DirectorActivity.class,null);check(home.findViewById(2400)!=null,"Simple home missing");runOnMainSync(()->home.finish());
  project.put("_quick",new JSONObject().put("text","").put("images",new JSONArray()));store.save(projectId,project);
  Activity activity=start(DirectorActivity.class,projectId);
  final String quickScript="Esta es una prueba del editor sencillo. El texto se reparte entre las imágenes sin preparar escenas manualmente. La narración y los subtítulos se montan en la nube.";
  runOnMainSync(()->{((EditText)activity.findViewById(2401)).setText("ENSAYO · EDITOR SENCILLO");((EditText)activity.findViewById(2402)).setText(quickScript);});
  Intent selected=new Intent();android.net.Uri first=android.net.Uri.fromFile(new File(store.folder(projectId),"media/image1.jpg")),second=android.net.Uri.fromFile(new File(store.folder(projectId),"media/image2.jpg"));ClipData clips=ClipData.newRawUri("Imágenes de prueba",first);clips.addItem(new ClipData.Item(second));selected.setClipData(clips);
  runOnMainSync(()->((DirectorActivity)activity).onActivityResult(30,Activity.RESULT_OK,selected));waitForIdleSync();
  long importDeadline=System.currentTimeMillis()+30000;while(System.currentTimeMillis()<importDeadline){Thread.sleep(300);checkUiError(activity);if(store.load(projectId).getJSONObject("_quick").getJSONArray("images").length()==2)break;}
  JSONObject simple=store.load(projectId);check(simple.getJSONObject("_quick").getJSONArray("images").length()==2,"Multiple image selection not imported");check(simple.getJSONObject("_quick").getString("text").equals(quickScript),"Script lost during image import");
  File quickQa=new File(context.getFilesDir(),"director-qa");quickQa.mkdirs();Thread.sleep(500);getUiAutomation().takeScreenshot().compress(android.graphics.Bitmap.CompressFormat.PNG,100,new FileOutputStream(new File(quickQa,"simple-editor.png")));
  click(activity,2106);
  JSONObject compiled=store.load(projectId);JSONArray autoScenes=compiled.getJSONArray("chapters").getJSONObject(0).getJSONArray("scenes");check(autoScenes.length()==2,"Automatic image/text association missing");check((autoScenes.getJSONObject(0).getString("narration")+" "+autoScenes.getJSONObject(1).getString("narration")).equals(quickScript),"Automatic grouping lost text");

  // Click the actual confirmation button; no alternate dispatch or consent bypass.
  java.lang.reflect.Field field=DirectorActivity.class.getDeclaredField("generationConfirmation");field.setAccessible(true);AlertDialog confirmation=(AlertDialog)field.get(activity);check(confirmation!=null&&confirmation.isShowing(),"No confirmation dialog");
  runOnMainSync(()->confirmation.getButton(android.content.DialogInterface.BUTTON_POSITIVE).performClick());waitForIdleSync();
  File jobFile=new File(store.folder(projectId),"job.json");long deadline=System.currentTimeMillis()+900000;JSONObject job=null;while(System.currentTimeMillis()<deadline){Thread.sleep(2500);checkUiError(activity);if(jobFile.isFile()){job=DirectorStore.read(jobFile);if(job.optString("stage").equals("UNCERTAIN"))throw new Exception("Transport failed: "+job.optString("error"));if(job.optString("stage").equals("RUNNING"))break;} }
  check(job!=null&&job.optString("stage").equals("RUNNING"),"APK did not dispatch actual workflow");String requestId=job.getString("request_id");
  while(System.currentTimeMillis()<deadline){click(activity,2107);Thread.sleep(8000);checkUiError(activity);job=DirectorStore.read(jobFile);if(job.optString("stage").equals("FAILED"))throw new Exception("Real production failed: "+job);if(job.optString("stage").equals("READY"))break;}
  check(job.optString("stage").equals("READY"),"No verified MP4 recovered within test deadline");JSONObject movie=job.getJSONObject("result");File mp4=new File(store.folder(projectId),"documental-REVISION.mp4");check(DirectorStore.sha(mp4).equals(movie.getString("sha256")),"Downloaded MP4 SHA mismatch");
  runOnMainSync(()->activity.finish());Activity preview=start(DirectorActivity.Preview.class,projectId);Thread.sleep(3000);
  final int[] positionValue={0};final boolean[] rendered={false};for(int i=0;i<20;i++){Thread.sleep(500);runOnMainSync(()->{DirectorActivity.Preview p=(DirectorActivity.Preview)preview;positionValue[0]=p.playbackPosition();rendered[0]=p.hasRenderedVideoFrame();});if(rendered[0]&&positionValue[0]>400)break;}
  int position=positionValue[0];check(rendered[0]&&position>400,"Native VideoView did not render a frame and advance playback");
  JSONObject report=new JSONObject().put("passed",true).put("request_id",requestId).put("github_run_id",movie.getString("github_run_id")).put("sha256",movie.getString("sha256")).put("duration",movie.getDouble("duration")).put("native_playback_position_ms",position).put("actual_video_frame_rendered",rendered[0]).put("simple_editor_title_text_multiple_images",true).put("automatic_scene_association_preserves_script",true).put("project_zip_backup_restored",true).put("settings_contents_write_instructions_verified",true).put("native_network_probes",probes).put("input_method","File URI through real ContentResolver; SAF picker UI requires human test").put("physical_samsung_tested",false);
  File qa=new File(context.getFilesDir(),"director-qa");qa.mkdirs();DirectorStore.write(new File(qa,"roundtrip.json"),report);getUiAutomation().takeScreenshot().compress(android.graphics.Bitmap.CompressFormat.PNG,100,new FileOutputStream(new File(qa,"preview.png")));result.putString("stream",report.toString(2));finish(Activity.RESULT_OK,result);
 }catch(Exception e){String message=e.toString();String token=arguments.getString("githubToken");if(token!=null)message=message.replace(token,"[REDACTED]");try{File qa=new File(getTargetContext().getFilesDir(),"director-qa");qa.mkdirs();DirectorStore.write(new File(qa,"recovery".equals(arguments.getString("mode"))?"recovery.json":"roundtrip.json"),new JSONObject().put("passed",false).put("error",message).put("physical_samsung_tested",false));}catch(Exception ignored){}result.putString("stream","DIRECTOR_TEST_FAILED: "+message);finish(Activity.RESULT_CANCELED,result);}}
}
