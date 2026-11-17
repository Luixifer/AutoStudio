package com.luixifer.autostudio;

import android.app.*;
import android.content.*;
import android.os.*;
import android.view.*;
import android.widget.*;
import org.json.*;
import java.io.*;
import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;

/** Videos and in-progress research runs visible without opening the GitHub browser. */
public final class ResearchVideosActivity extends Activity {
    private LinearLayout results;
    private TextView status;
    private Button refresh;
    private final AtomicBoolean loading=new AtomicBoolean(false);
    private final Handler ui=new Handler(Looper.getMainLooper());
    private boolean active;
    private final Runnable ticker=new Runnable(){
        @Override public void run(){
            if(!active)return;
            refreshVideos();
            ui.postDelayed(this,30000);
        }
    };

    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        LinearLayout body=Ui.scroll(this,Ui.root(this,"Mis vídeos"));
        Ui.para(body,"Tus vídeos de investigación, incluidos los borradores y las pruebas. "
            +"Cuando GitHub termine de producirlos, aparecerán aquí. "
            +"Las pruebas no están aprobadas para YouTube.");
        refresh=Ui.button(body,"Actualizar vídeos",1201,true);
        refresh.setOnClickListener(v->refreshVideos());
        status=Ui.para(body,"Consultando GitHub…");
        results=new LinearLayout(this);
        results.setOrientation(LinearLayout.VERTICAL);
        body.addView(results,new LinearLayout.LayoutParams(-1,-2));
        Ui.button(body,"Volver",1202,false).setOnClickListener(v->finish());
    }
    @Override protected void onStart(){
        super.onStart();active=true;ui.post(ticker);
    }
    @Override protected void onStop(){
        active=false;ui.removeCallbacks(ticker);super.onStop();
    }
    private void refreshVideos(){
        if(!loading.compareAndSet(false,true))return;
        if(!new CredentialStore(this).connected()){
            status.setText("Conecta GitHub desde Ajustes para ver las investigaciones.");
            loading.set(false);return;
        }
        refresh.setEnabled(false);
        status.setText("Buscando vídeos y borradores en GitHub…");
        AutoStudioApp.IO.execute(()->{
            try{
                ResearchArtifactClient client=new ResearchArtifactClient(new CredentialStore(getApplicationContext()).load());
                JSONArray runs=client.researchRuns();
                Map<String,JSONObject> artifacts=client.availableVideos();
                runOnUiThread(()->{
                    if(!active){loading.set(false);return;}
                    results.removeAllViews();
                    int shown=0;
                    for(int i=0;i<runs.length()&&shown<20;i++){
                        JSONObject run=runs.optJSONObject(i);
                        if(run==null)continue;
                        String id=run.optString("id");
                        if(!ResearchArtifactClient.validRunId(id))continue;
                        String title=run.optString("display_title","Investigación");
                        if(title.length()>180)title=title.substring(0,180);
                        String progress=run.optString("status","");
                        String conclusion=run.optString("conclusion","");
                        JSONObject artifact=artifacts.get(id);
                        boolean completed="completed".equals(progress);
                        boolean playable=artifact!=null;
                        File local;
                        try{local=ResearchArtifactClient.localFile(getFilesDir(),id);}
                        catch(Exception e){continue;}
                        LinearLayout card=Ui.card(results);
                        card.addView(Ui.text(this,title,17,true));
                        if(local.isFile()){
                            Ui.para(card,"Vídeo guardado · copia local disponible");
                            Ui.button(card,"▶ Reproducir dentro de AutoStudio",View.generateViewId(),true)
                                .setOnClickListener(v->openVideo(id));
                        }else if(playable){
                            Ui.para(card,"Vídeo de prueba terminado · pendiente de descargar");
                            Ui.button(card,"Descargar y reproducir",View.generateViewId(),true)
                                .setOnClickListener(v->downloadAndPlay(id,artifact));
                        }else if(!completed){
                            Ui.para(card,"Investigación en curso · "+progress);
                        }else if("success".equals(conclusion)){
                            Ui.para(card,"Investigación terminada · sin MP4 disponible. "
                                +"Algunos temas solo producen un informe; los artefactos caducan.");
                        }else{
                            Ui.para(card,"La investigación terminó con error o fue cancelada.");
                        }
                        Ui.button(card,"Ver informe en GitHub",View.generateViewId(),false)
                            .setOnClickListener(v->Ui.browser(this,
                                "https://github.com/"+GitHubClient.REPO+"/actions/runs/"+id));
                        shown++;
                    }
                    status.setText(shown>0?"Últimas "+shown+" investigaciones · actualización automática cada 30 s":
                        "Aún no hay investigaciones recientes en GitHub.");
                    refresh.setEnabled(true);
                    loading.set(false);
                });
            }catch(Exception error){
                runOnUiThread(()->{
                    if(active)status.setText("No se pudo consultar GitHub: "+error.getMessage()+
                        ". Los vídeos descargados siguen guardados.");
                    refresh.setEnabled(true);
                    loading.set(false);
                });
            }
        });
    }
    private void openVideo(String runId){
        startActivity(new Intent(this,PlayerActivity.class).putExtra("research_run_id",runId));
    }
    private void downloadAndPlay(String runId,JSONObject artifact){
        if(!loading.compareAndSet(false,true))return;
        refresh.setEnabled(false);
        status.setText("Descargando vídeo y verificando SHA-256…");
        AutoStudioApp.IO.execute(()->{
            try{
                ResearchArtifactClient client=new ResearchArtifactClient(new CredentialStore(getApplicationContext()).load());
                File file=client.download(runId,artifact,getFilesDir());
                runOnUiThread(()->{
                    loading.set(false);
                    refresh.setEnabled(true);
                    status.setText("MP4 descargado y verificado: "+file.length()+" bytes.");
                    openVideo(runId);
                    refreshVideos();
                });
            }catch(Exception e){
                runOnUiThread(()->{
                    loading.set(false);
                    refresh.setEnabled(true);
                    Ui.error(this,"No se pudo descargar el vídeo: "+e.getMessage());
                });
            }
        });
    }
}
