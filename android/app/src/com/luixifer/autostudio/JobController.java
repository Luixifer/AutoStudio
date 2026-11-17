package com.luixifer.autostudio;
import android.content.*;
import android.os.*;
import org.json.*;
import java.io.*;
import java.util.*;
import java.util.concurrent.*;

/** One persisted request at a time. Poll only while a control screen is visible. */
public final class JobController {
    public interface Listener{void changed(JSONObject state);}
    private final Context context;private final SharedPreferences prefs;private final Handler main=new Handler(Looper.getMainLooper());
    private final ScheduledExecutorService worker=Executors.newSingleThreadScheduledExecutor();
    private Listener listener;private JSONObject state;private ScheduledFuture<?> timer;private int errors;
    public JobController(Context c){context=c.getApplicationContext();prefs=context.getSharedPreferences("production_state",0);try{state=new JSONObject(prefs.getString("active","{}"));}catch(Exception e){state=new JSONObject();}}
    public synchronized JSONObject snapshot(){try{return new JSONObject(state.toString());}catch(Exception e){return new JSONObject();}}
    public synchronized JSONArray history(){try{return new JSONArray(prefs.getString("history","[]"));}catch(Exception e){return new JSONArray();}}
    public synchronized boolean busy(){String s=state.optString("status");return !s.isEmpty()&&!s.equals("READY")&&!s.equals("FAILED");}
    private synchronized void update(String status,String message) throws Exception{state.put("status",status);state.put("message",message);if(!prefs.edit().putString("active",state.toString()).commit())throw new IOException("No se pudo guardar el estado del trabajo.");notifyUi();}
    private void notifyUi(){main.post(()->{Listener l;JSONObject copy; synchronized(this){l=listener;copy=snapshot();}if(l!=null)l.changed(copy);});}
    public synchronized void attach(Listener l){listener=l;notifyUi();schedule(0);}
    public synchronized void detach(Listener l){if(listener==l)listener=null;if(timer!=null){timer.cancel(false);timer=null;}}
    private synchronized void schedule(int seconds){if(listener!=null&&busy()&&(timer==null||timer.isDone()))timer=worker.schedule(()->{synchronized(this){timer=null;}poll();},seconds,TimeUnit.SECONDS);}
    public synchronized void refresh(){if(timer!=null){timer.cancel(false);timer=null;}if(busy())schedule(0);else notifyUi();}
    public synchronized void start(String topic) throws Exception{
        if(busy())throw new IOException("Ya hay una producción en curso. Consulta su resultado antes de iniciar otra.");
        if(topic==null||topic.trim().length()<3||topic.trim().length()>160||topic.matches("(?s).*[\\p{Cntrl}].*"))throw new IOException("Introduce un tema de 3 a 160 caracteres, sin saltos de línea.");
        if(!new CredentialStore(context).connected())throw new IOException("Conecta GitHub antes de generar un Short.");
        state=new JSONObject().put("request_id",UUID.randomUUID().toString().replace("-","")).put("topic",topic.trim()).put("created_ms",System.currentTimeMillis());errors=0;
        update("SENDING","Enviando una solicitud nueva a GitHub Actions…");
        JSONObject submitted=snapshot();worker.execute(()->{
            try{new GitHubClient(new CredentialStore(context).load()).dispatch(submitted.getString("request_id"),submitted.getString("topic"));update("WAITING","Solicitud enviada. Esperando a que GitHub inicie el trabajo…");}
            catch(GitHubClient.ApiError e){safeUpdate("FAILED",e.getMessage());}
            catch(Exception e){safeUpdate("UNCERTAIN","No se pudo confirmar el envío. Buscando la solicitud por su identificador; no se reenviará automáticamente.");}
            schedule(2);
        });
    }
    private void safeUpdate(String status,String message){try{update(status,message);}catch(Exception e){main.post(()->{Listener l; synchronized(this){l=listener;}if(l!=null){JSONObject copy=snapshot();try{copy.put("message","Error al guardar el estado local. No se enviarán solicitudes nuevas.");}catch(Exception ignored){}l.changed(copy);}});}}
    public File video(String id){if(!GitHubClient.validId(id))throw new IllegalArgumentException("Identificador inválido.");return new File(context.getFilesDir(),"videos/"+id+".mp4");}
    private void poll(){
        if(!busy())return;
        try{
            JSONObject job=snapshot();String id=job.getString("request_id"),token=new CredentialStore(context).load();GitHubClient client=new GitHubClient(token);
            JSONObject run=job.has("run_id")?client.getRun(job.getString("run_id")):client.findRun(id);
            if(run==null){update("WAITING","GitHub todavía no muestra esta solicitud. Puedes salir y volver; no se enviará de nuevo.");schedule(12);return;}
            synchronized(this){state.put("run_id",String.valueOf(run.getLong("id")));state.put("run_url","https://github.com/"+GitHubClient.REPO+"/actions/runs/"+run.getLong("id"));}
            if(!run.optString("status").equals("completed")){update("RUNNING",run.optString("status").equals("queued")?"Trabajo en la cola de GitHub. Esperando un runner gratuito…":"Produciendo narración, escenas y MP4 en GitHub Actions…");}
            else if(!run.optString("conclusion").equals("success")){update("FAILED","GitHub terminó el trabajo sin éxito ("+run.optString("conclusion")+"). Abre sus registros para revisar el motivo.");return;}
            else{
                JSONObject result=client.result(id,snapshot().getString("run_id"));
                if(result==null){update("RUNNING","Producción terminada. Esperando a que el resultado publicado esté disponible…");}
                else if(!result.optString("status").equals("completed")){update("FAILED",result.optString("message","La producción no se completó."));return;}
                else{
                    update("DOWNLOADING","Descargando tu MP4 y verificando su SHA-256…");trimCache(id);GitHubClient.download(id,result.getJSONObject("video"),video(id));
                    synchronized(this){state.put("result",result);state.put("local_file",video(id).getAbsolutePath());}
                    update("READY","Vídeo descargado y verificado. Listo para reproducir.");remember();return;
                }
            }
            errors=0;schedule(8);
        }catch(Exception e){errors++;JSONObject job=snapshot();String status=job.optString("status","WAITING");if(status.equals("SENDING"))status="UNCERTAIN";safeUpdate(status,e instanceof GitHubClient.ApiError?e.getMessage():"Sin conexión confirmada con GitHub. El trabajo conserva su identificador; vuelve a consultar cuando tengas red.");schedule(Math.min(60,10*errors));}
    }
    private synchronized void remember() throws Exception{
        JSONArray old=history(),next=new JSONArray();next.put(snapshot());for(int i=0;i<old.length()&&next.length()<30;i++){JSONObject item=old.getJSONObject(i);if(!item.optString("request_id").equals(state.optString("request_id")))next.put(item);}if(!prefs.edit().putString("history",next.toString()).commit())throw new IOException("No se pudo guardar el historial.");
    }
    private void trimCache(String current){File dir=new File(context.getFilesDir(),"videos");File[] files=dir.listFiles((d,n)->n.endsWith(".mp4"));if(files==null)return;Arrays.sort(files,Comparator.comparingLong(File::lastModified));long size=0;for(File f:files)size+=f.length();for(File f:files)if(size>100*1024*1024&&!f.getName().equals(current+".mp4")){long n=f.length();if(f.delete())size-=n;}}
}
